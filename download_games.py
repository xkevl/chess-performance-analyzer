import json
import time
from pathlib import Path

import requests

# -----------------------------
# Configuration
# -----------------------------
USERNAME = "xkevl"
OUTPUT_DIR = Path("data")

BASE_URL = f"https://api.chess.com/pub/player/{USERNAME}"

HEADERS = {
    "User-Agent": "ChessPerformanceAnalyzer/1.0 (personal analytics project)"
}

# -----------------------------
# Prepare output folder
# -----------------------------
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update(HEADERS)


def save_json(filename, data):
    """Save data as a readable JSON file."""
    filepath = OUTPUT_DIR / filename

    with filepath.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    print(f"Saved: {filepath.resolve()}")


# -----------------------------
# Retrieve archive list
# -----------------------------
try:
    response = session.get(
        f"{BASE_URL}/games/archives",
        timeout=30
    )
    response.raise_for_status()

    archives = response.json()["archives"]

    print(f"Found {len(archives)} monthly archives.")
    print("Starting game download...\n")

except (requests.exceptions.RequestException, KeyError) as error:
    raise SystemExit(f"Could not retrieve archives: {error}")


# -----------------------------
# Download every archive
# -----------------------------
all_games = []
failed_archives = []

for number, archive_url in enumerate(archives, start=1):
    try:
        response = session.get(archive_url, timeout=60)
        response.raise_for_status()

        monthly_games = response.json().get("games", [])

        # Keep the original records intact.
        all_games.extend(monthly_games)

        print(
            f"[{number}/{len(archives)}] "
            f"{archive_url.rsplit('/', 2)[-2]}/"
            f"{archive_url.rsplit('/', 1)[-1]}: "
            f"{len(monthly_games)} games"
        )

        # Be considerate of the public API.
        time.sleep(0.2)

    except (requests.exceptions.RequestException, ValueError) as error:
        print(f"Failed: {archive_url} — {error}")
        failed_archives.append(archive_url)


# -----------------------------
# Save original game records
# -----------------------------
save_json("all_games.json", all_games)

# Separate games by their rated flag.
rated_games = [
    game for game in all_games
    if game.get("rated") is True
]

unrated_games = [
    game for game in all_games
    if game.get("rated") is False
]

unknown_rating_status = [
    game for game in all_games
    if "rated" not in game
    or game.get("rated") not in (True, False)
]

save_json("rated_games.json", rated_games)
save_json("unrated_games.json", unrated_games)
save_json("unknown_rating_status.json", unknown_rating_status)

# Record any archive failures so we can retry them.
save_json("failed_archives.json", failed_archives)

# -----------------------------
# Download summary
# -----------------------------
print("\n" + "=" * 40)
print("DOWNLOAD SUMMARY")
print("=" * 40)

print(f"Archives available: {len(archives)}")
print(f"Archives failed: {len(failed_archives)}")
print(f"Total games downloaded: {len(all_games)}")
print(f"Rated games: {len(rated_games)}")
print(f"Unrated games: {len(unrated_games)}")
print(f"Unknown rated status: {len(unknown_rating_status)}")

print("\nGames by time control:")

time_classes = {}

for game in all_games:
    category = game.get("time_class", "unknown")
    time_classes[category] = time_classes.get(category, 0) + 1

for category, count in sorted(time_classes.items()):
    print(f"{category}: {count}")

if failed_archives:
    print(
        "\nSome archives failed. "
        "Check failed_archives.json before proceeding."
    )
else:
    print("\nAll monthly archives downloaded successfully!")

print("\nNext step: inspect the downloaded data.")
