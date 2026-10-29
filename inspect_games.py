import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

# Load the rated games dataset
DATA_FILE = Path("data") / "rated_games.json"

with DATA_FILE.open("r", encoding="utf-8") as file:
    games = json.load(file)

print("=" * 50)
print("CHESS DATASET INSPECTION")
print("=" * 50)

print(f"\nTotal rated games: {len(games):,}")

if not games:
    raise SystemExit("No rated games found.")

# 1. Inspect available fields
print("\n1. AVAILABLE FIELDS")
print("-" * 30)

all_keys = sorted(set().union(*(game.keys() for game in games)))

for key in all_keys:
    present = sum(key in game and game[key] is not None for game in games)
    print(f"{key}: present in {present:,}/{len(games):,} games")

# 2. Game formats
print("\n2. GAMES BY TIME CONTROL")
print("-" * 30)

for category, count in Counter(
    game.get("time_class", "unknown") for game in games
).most_common():
    print(f"{category}: {count:,}")

# 3. Results from your perspective
print("\n3. RESULTS")
print("-" * 30)

results = Counter()

for game in games:
    white = game.get("white", {})
    black = game.get("black", {})

    white_user = white.get("username", "").lower()
    black_user = black.get("username", "").lower()

    if white_user == "xkevl":
        result = white.get("result", "unknown")
    elif black_user == "xkevl":
        result = black.get("result", "unknown")
    else:
        result = "username_not_matched"

    results[result] += 1

for result, count in results.most_common():
    print(f"{result}: {count:,}")

# 4. Color breakdown
print("\n4. GAMES BY COLOR")
print("-" * 30)

colors = Counter()

for game in games:
    white_user = game.get("white", {}).get("username", "").lower()
    black_user = game.get("black", {}).get("username", "").lower()

    if white_user == "xkevl":
        colors["White"] += 1
    elif black_user == "xkevl":
        colors["Black"] += 1
    else:
        colors["Unknown"] += 1

for color, count in colors.items():
    print(f"{color}: {count:,}")

# 5. Date range
print("\n5. GAME DATE RANGE")
print("-" * 30)

timestamps = [
    game["end_time"]
    for game in games
    if isinstance(game.get("end_time"), (int, float))
]

if timestamps:
    earliest = datetime.fromtimestamp(
        min(timestamps), tz=timezone.utc
    )
    latest = datetime.fromtimestamp(
        max(timestamps), tz=timezone.utc
    )

    print("Earliest game (UTC):", earliest.strftime("%Y-%m-%d"))
    print("Latest game (UTC):", latest.strftime("%Y-%m-%d"))
else:
    print("No valid end_time timestamps found.")

# 6. Duplicate game URLs
print("\n6. DUPLICATE CHECK")
print("-" * 30)

urls = [
    game.get("url")
    for game in games
    if game.get("url")
]

print(f"Games with URLs: {len(urls):,}")
print(f"Unique URLs: {len(set(urls)):,}")
print(f"Duplicate URLs: {len(urls) - len(set(urls)):,}")

# 7. Preview one game
print("\n7. SAMPLE GAME RECORD")
print("-" * 30)

print(json.dumps(games[0], indent=2, ensure_ascii=False))

print("\nInspection complete.")
