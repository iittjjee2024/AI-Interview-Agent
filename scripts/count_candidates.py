import json
data = json.load(open("candidates.json"))
print(f"Total candidates: {len(data['candidates'])}")
for c in data["candidates"]:
    m = c["member"]
    print(f"  {m['id']} - {m['name']} ({m['jobRole']})")
