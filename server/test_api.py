import urllib.request
import json as j


def get(path):
    r = urllib.request.urlopen(f"http://localhost:8000{path}")
    return j.loads(r.read())


def post(path, data=None):
    req = urllib.request.Request(
        f"http://localhost:8000{path}",
        data=j.dumps(data).encode() if data else None,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return j.loads(urllib.request.urlopen(req).read())


def put(path, data=None):
    req = urllib.request.Request(
        f"http://localhost:8000{path}",
        data=j.dumps(data).encode() if data else None,
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    return j.loads(urllib.request.urlopen(req).read())


def delete(path):
    req = urllib.request.Request(
        f"http://localhost:8000{path}",
        method="DELETE",
    )
    return j.loads(urllib.request.urlopen(req).read())


def ok(name, cond):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name}")
    return cond


all_ok = True

print("=== Agents ===")
d = get("/api/agents")
all_ok &= ok("count>=3", len(d["data"]) >= 3)
names = [a["name"] for a in d["data"]]
all_ok &= ok("has 笃笃", "笃笃" in names)

print("\n=== Devices ===")
d = get("/api/devices")
all_ok &= ok("count=2", len(d["data"]) == 2)

print("\n=== Voices ===")
d = get("/api/voices")
all_ok &= ok("count=5", len(d["data"]) == 5)
c = d["data"][0]
all_ok &= ok("camelCase keys", "isCloned" in c and "isSelected" in c)
print(f"  first voice keys: {list(c.keys())}")

print("\n=== Knowledge ===")
d = get("/api/knowledge")
all_ok &= ok("count=4", len(d["data"]) == 4)
c = d["data"][0]
all_ok &= ok("camelCase keys", "itemCount" in c and "isSystem" in c)

print("\n=== History ===")
d = get("/api/history")
all_ok &= ok("count>=3", len(d["data"]) >= 3)
c = d["data"][0]
all_ok &= ok("camelCase keys", "agentName" in c and "messageCount" in c)

# detail + messages
conv_id = d["data"][0]["id"]
detail = get(f"/api/history/{conv_id}")
all_ok &= ok("detail has messages", len(detail["data"]["messages"]) > 0)

msgs = get(f"/api/history/{conv_id}/messages")
all_ok &= ok("messages endpoint", len(msgs["data"]) > 0)

print("\n=== Voiceprint ===")
d = get("/api/voiceprint")
all_ok &= ok("count=2", len(d["data"]) == 2)
c = d["data"][0]
all_ok &= ok("camelCase keys", "sampleCount" in c)

print("\n=== User ===")
d = get("/api/user/profile")
c = d["data"]
all_ok &= ok("has userId", "userId" in c)
all_ok &= ok("has avatarEmoji", "avatarEmoji" in c)

print("\n=== CRUD ===")
# Create
d = post("/api/agents", {"name": "p2-test", "emoji": "T", "description": "test"})
new_id = d["data"]["id"]
all_ok &= ok("create agent", new_id is not None)

# Update
d = put(f"/api/agents/{new_id}", {"name": "p2-updated"})
all_ok &= ok("update agent", d["data"]["name"] == "p2-updated")

# Delete
d = delete(f"/api/agents/{new_id}")
all_ok &= ok("delete agent", d["code"] == 0)

# Knowledge toggle
d = get("/api/knowledge")
kb_id = d["data"][0]["id"]
d = put(f"/api/knowledge/{kb_id}/toggle", {"enabled": False})
all_ok &= ok("toggle knowledge", d["code"] == 0)

# Register speaker
d = post("/api/voiceprint/register", {"name": "test-speaker"})
spk_id = d["data"]["id"]
all_ok &= ok("register speaker", spk_id is not None)

# Delete speaker
d = delete(f"/api/voiceprint/{spk_id}")
all_ok &= ok("delete speaker", d["code"] == 0)

print("\n=== Pipeline ===")
agent_id = get("/api/agents")["data"][0]["id"]
d = post("/api/pipeline/chat", {"text": "你好，1+1=?", "agentId": agent_id})
all_ok &= ok("chat 200", d["code"] == 0)
inner = d["data"]
all_ok &= ok("chat has conversationId", "conversationId" in inner)
all_ok &= ok("chat has text", inner.get("text") is not None)
print(f"  text: {inner.get('text','')[:60]}")

print(f"\n{'='*20}")
print(f"{'ALL PASSED' if all_ok else 'SOME FAILED'}")
print(f"{'='*20}")
