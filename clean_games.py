import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

# -----------------------------------
# Configuration
# -----------------------------------
INPUT_FILE = Path("data") / "rated_games.json"
OUTPUT_FILE = Path("data") / "cleaned_games.csv"

USERNAME = "xkevl"

# Normalize Chess.com results from your perspective.
DRAW_RESULTS = {
    "agreed",
    "repetition",
    "stalemate",
    "insufficient",
    "50move",
    "timevsinsufficient",
}

LOSS_RESULTS = {
    "resigned",
    "checkmated",
    "timeout",
    "abandoned",
    "lose",
}

# -----------------------------------
# Helper functions
# -----------------------------------
def parse_pgn_headers(pgn):
    """Extract PGN header tags into a dictionary."""
    if not pgn:
        return {}

    return dict(
        re.findall(r'^\[(\w+)\s+"(.*)"\]\s*$',
                   pgn, flags=re.MULTILINE)
    )


def parse_datetime(date_text, time_text):
    """Parse a UTC date and time from PGN headers."""
    if not date_text or not time_text:
        return None

    try:
        return datetime.strptime(
            f"{date_text} {time_text}",
            "%Y.%m.%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def opening_name(url):
    """Convert a Chess.com opening URL into a readable name."""
    if not url:
        return None

    slug = urlparse(url).path.rstrip("/").split("/")[-1]

    if not slug:
        return None

    return slug.replace("-", " ").title()


def classify_result(raw_result):
    """Standardize the result from the player's perspective."""
    if raw_result == "win":
        return "win"
    if raw_result in LOSS_RESULTS:
        return "loss"
    if raw_result in DRAW_RESULTS:
        return "draw"

    return "unknown"


def utc_datetime(timestamp):
    """Convert a Unix timestamp to a UTC datetime."""
    if timestamp is None:
        return None

    try:
        return datetime.fromtimestamp(
            timestamp, tz=timezone.utc
        )
    except (ValueError, OverflowError, OSError):
        return None


# -----------------------------------
# Load raw rated games
# -----------------------------------
with INPUT_FILE.open("r", encoding="utf-8") as file:
    games = json.load(file)

print(f"Loaded {len(games):,} rated games.")

cleaned_games = []
seen_urls = set()
result_counts = Counter()
unknown_results = Counter()
missing_counts = Counter()
invalid_records = 0

# -----------------------------------
# Clean each game
# -----------------------------------
for game in games:
    white = game.get("white") or {}
    black = game.get("black") or {}
    pgn = game.get("pgn") or ""
    headers = parse_pgn_headers(pgn)

    white_username = white.get("username", "").lower()
    black_username = black.get("username", "").lower()

    if white_username == USERNAME.lower():
        color = "White"
        player = white
        opponent = black
    elif black_username == USERNAME.lower():
        color = "Black"
        player = black
        opponent = white
    else:
        invalid_records += 1
        continue

    url = game.get("url")

    # Prevent duplicate game records.
    if not url or url in seen_urls:
        invalid_records += 1
        continue

    seen_urls.add(url)

    raw_result = player.get("result", "unknown")
    result = classify_result(raw_result)

    result_counts[result] += 1

    if result == "unknown":
        unknown_results[raw_result] += 1

    # Use the API end timestamp as the primary date source.
    end_dt = utc_datetime(game.get("end_time"))

    # Fall back to PGN end date/time if needed.
    if end_dt is None:
        end_dt = parse_datetime(
            headers.get("EndDate") or headers.get("UTCDate"),
            headers.get("EndTime") or headers.get("UTCTime")
        )

    start_dt = parse_datetime(
        headers.get("UTCDate"),
        headers.get("UTCTime")
    )

    # Use StartTime if UTC time headers are unavailable.
    if start_dt is None:
        start_dt = parse_datetime(
            headers.get("Date"),
            headers.get("StartTime")
        )

    duration_seconds = None

    if start_dt and end_dt:
        duration = (end_dt - start_dt).total_seconds()

        if 0 <= duration <= 86400:
            duration_seconds = int(duration)

    # Prefer the PGN ECO code; fall back to the API field.
    eco = headers.get("ECO")

    if not eco and game.get("eco"):
        match = re.search(r"/([A-E]\d{2})/", game["eco"])
        if match:
            eco = match.group(1)

    eco_url = headers.get("ECOUrl")

    if not eco_url and str(game.get("eco", "")).startswith("http"):
        eco_url = game["eco"]

    record = {
        "game_id": game.get("uuid") or url,
        "game_date": end_dt.date().isoformat() if end_dt else None,
        "color": color,
        "result": result,
        "raw_result": raw_result,
        "player_rating": player.get("rating"),
        "opponent": opponent.get("username"),
        "opponent_rating": opponent.get("rating"),
        "time_class": game.get("time_class"),
        "time_control": game.get("time_control"),
        "eco": eco,
        "opening": opening_name(eco_url),
        "duration_seconds": duration_seconds,
        "rated": int(bool(game.get("rated"))),
        "rules": game.get("rules"),
        "url": url,
        "pgn": pgn,
    }

    for field, value in record.items():
        if value is None or value == "":
            missing_counts[field] += 1

    cleaned_games.append(record)

# -----------------------------------
# Export cleaned dataset
# -----------------------------------
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

fieldnames = [
    "game_id",
    "game_date",
    "color",
    "result",
    "raw_result",
    "player_rating",
    "opponent",
    "opponent_rating",
    "time_class",
    "time_control",
    "eco",
    "opening",
    "duration_seconds",
    "rated",
    "rules",
    "url",
    "pgn",
]

with OUTPUT_FILE.open(
    "w", newline="", encoding="utf-8-sig"
) as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(cleaned_games)

# -----------------------------------
# Quality report
# -----------------------------------
print("\n" + "=" * 45)
print("CLEANING SUMMARY")
print("=" * 45)

print(f"Raw rated games: {len(games):,}")
print(f"Cleaned games: {len(cleaned_games):,}")
print(f"Skipped records: {invalid_records:,}")
print(f"Unique game URLs: {len(seen_urls):,}")

print("\nResults:")
for result in ["win", "loss", "draw", "unknown"]:
    print(f"{result.title()}: {result_counts[result]:,}")

if unknown_results:
    print("\nUnrecognized result labels:")
    for label, count in unknown_results.items():
        print(f"{label}: {count}")

print("\nGames by time control:")
time_counts = Counter(
    game["time_class"] or "unknown"
    for game in cleaned_games
)

for time_class, count in sorted(time_counts.items()):
    print(f"{time_class}: {count:,}")

print("\nMissing values in cleaned columns:")
for field in fieldnames:
    print(f"{field}: {missing_counts[field]:,}")

print(f"\nOutput saved to: {OUTPUT_FILE.resolve()}")
