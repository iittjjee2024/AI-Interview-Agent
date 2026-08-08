import json
d = json.load(open("curriculum.json"))
print(f"Days: {len(d['days'])}")
print(f"Keys in day 1: {list(d['days'][0].keys())}")
print(f"\nDay 7:")
print(json.dumps(d["days"][6], indent=2))
print(f"\nDay 12:")
print(json.dumps(d["days"][11], indent=2))
