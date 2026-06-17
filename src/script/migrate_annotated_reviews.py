import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
annotated_path = os.path.join(PROJECT_ROOT, "data", "processed", "annotated_reviews.json")

if not os.path.exists(annotated_path):
    print("annotated_reviews.json not found!")
    exit(1)

with open(annotated_path, "r", encoding="utf-8") as f:
    reviews = json.load(f)

# Define mappings
segment_map = {
    "Casual Listener": "Playlist Dependents",
    "Music Explorer": "New Music Seekers",
    "Passive Listener": "Passive Listener",
    "Trend Follower": "New Music Seekers",
    "Power User": "Genre Hoppers"
}

pain_map = {
    "Lack of Discovery Filters": "Lack of Mood/Context Filters"
}

goal_map = {
    "Mood-Based Listening": "Mood/Activity-Based Listening",
    "Curating Custom Playlists": "Relying on Familiar Playlists",
    "Background Focus Listening": "Background/Passive Listening"
}

repeat_map = {
    "Offline/Data Saving": "Mood Mismatch"
}

needs_map = {
    "Advanced Library Sorting": "Smart Playlist Refresh",
    "Intent-Based Recommendations": "Cross-Genre Discovery Mode"
}

migrated_count = 0

for r in reviews:
    # Migrate segment
    old_seg = r.get("segment_classification")
    if old_seg in segment_map:
        r["segment_classification"] = segment_map[old_seg]
        migrated_count += 1
    
    # Migrate pain points
    old_pain = r.get("discovery_pain_points")
    if old_pain in pain_map:
        r["discovery_pain_points"] = pain_map[old_pain]
        
    # Migrate goals
    old_goal = r.get("listening_goals_intentions")
    if old_goal in goal_map:
        r["listening_goals_intentions"] = goal_map[old_goal]
        
    # Migrate repeat drivers
    old_repeat = r.get("repeat_listening_signals")
    if old_repeat in repeat_map:
        r["repeat_listening_signals"] = repeat_map[old_repeat]
        
    # Migrate unmet needs
    old_need = r.get("unmet_needs")
    if old_need in needs_map:
        r["unmet_needs"] = needs_map[old_need]

with open(annotated_path, "w", encoding="utf-8") as f:
    json.dump(reviews, f, indent=2, ensure_ascii=False)

print(f"Successfully migrated {migrated_count} reviews in annotated_reviews.json.")
