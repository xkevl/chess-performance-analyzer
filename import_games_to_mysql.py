import csv
import os
import mysql.connector
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Locate the cleaned CSV in your project folder
PROJECT_DIR = Path(__file__).resolve().parent
CSV_FILE = PROJECT_DIR / "data" / "cleaned_games.csv"

connection = None
cursor = None

try:
    print(f"Reading CSV: {CSV_FILE}")

    with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        games = list(reader)

    print(f"CSV rows found: {len(games):,}")

    if len(games) != 3267:
        raise ValueError(
            f"Expected 3,267 games, but found {len(games):,}. "
            "Import cancelled."
        )

    connection = mysql.connector.connect(
    	host=os.getenv("MYSQL_HOST", "localhost"),
    	user=os.getenv("MYSQL_USER", "root"),
    	password=os.getenv("MYSQL_PASSWORD"),
    	database=os.getenv("MYSQL_DATABASE", "chess_analytics"),
    	port=int(os.getenv("MYSQL_PORT", "3306"))
    )

    cursor = connection.cursor()

    # Map empty CSV fields to SQL NULL and convert numeric values.
    columns = [
        "game_id", "game_date", "color", "result", "raw_result",
        "player_rating", "opponent", "opponent_rating", "time_class",
        "time_control", "eco", "opening", "duration_seconds", "rated",
        "rules", "url", "pgn"
    ]

    insert_sql = """
        INSERT INTO games (
            game_id, game_date, color, result, raw_result,
            player_rating, opponent, opponent_rating, time_class,
            time_control, eco, opening, duration_seconds, rated,
            rules, url, pgn
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    def optional_int(value):
        value = (value or "").strip()
        return int(value) if value else None

    def optional_text(value):
        value = (value or "").strip()
        return value if value else None

    rows = []

    for game in games:
        rated_value = (game.get("rated") or "").strip().lower()
        if rated_value in ("true", "1", "yes"):
            rated = 1
        elif rated_value in ("false", "0", "no"):
            rated = 0
        else:
            raise ValueError(
                f"Unexpected rated value: {game.get('rated')!r}"
            )

        rows.append((
            game["game_id"],
            game["game_date"],
            game["color"],
            game["result"],
            optional_text(game.get("raw_result")),
            optional_int(game.get("player_rating")),
            game["opponent"],
            optional_int(game.get("opponent_rating")),
            game["time_class"],
            game["time_control"],
            optional_text(game.get("eco")),
            game["opening"],
            optional_int(game.get("duration_seconds")),
            rated,
            game["rules"],
            game["url"],
            game["pgn"]
        ))

    # Avoid silently adding duplicate records.
    cursor.execute("SELECT COUNT(*) FROM games")
    existing_count = cursor.fetchone()[0]

    if existing_count != 0:
        raise ValueError(
            f"The games table already contains {existing_count} rows. "
            "Import cancelled to avoid duplicates."
        )

    cursor.executemany(insert_sql, rows)
    connection.commit()

    cursor.execute("SELECT COUNT(*) FROM games")
    imported_count = cursor.fetchone()[0]

    print("\nIMPORT SUMMARY")
    print("=" * 35)
    print(f"CSV rows:      {len(games):,}")
    print(f"Imported rows: {imported_count:,}")

    if imported_count == 3267:
        print("SUCCESS: All 3,267 games were imported.")
    else:
        print("WARNING: The imported row count differs from expectations.")

except Exception as error:
    if connection and connection.is_connected():
        connection.rollback()
    print("\nIMPORT FAILED")
    print(error)

finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()
