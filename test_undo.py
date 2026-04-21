import requests
import json
import time

API = "http://127.0.0.1:8000/api"

print("Fetching matches...")
matches = requests.get(f"{API}/matches").json()
match = matches[-1]
mid = match["id"]
print(f"Match ID: {mid}")

live = requests.get(f"{API}/matches/{mid}/live").json()
iid = live["innings"]["id"]
print(f"Innings ID: {iid}")

print("Recording 1 run...")
striker_id = [b for b in live["batting_scores"] if b["is_on_strike"]][0]["player_id"]
non_striker_id = [b for b in live["batting_scores"] if not b["is_on_strike"] and b["is_at_crease"]][0]["player_id"]
bowler_id = [b for b in live["bowling_scores"] if b["is_current_bowler"]][0]["player_id"]

res = requests.post(f"{API}/innings/{iid}/ball", json={
    "striker_id": striker_id,
    "non_striker_id": non_striker_id,
    "bowler_id": bowler_id,
    "runs_scored": 1
})
print(f"Ball response: {res.status_code}")

print("Undoing ball...")
res = requests.post(f"{API}/innings/{iid}/undo")
print(f"Undo response: {res.status_code}")
if res.status_code != 200:
    print(res.text)

