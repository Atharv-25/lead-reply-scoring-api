"""
ROUND 2 — 10-THREAD VENDOR EVAL STRESS TEST
Specifically targets the vendor_eval_bonus for false positives.
"""

import json, time, urllib.request

BASE = "http://localhost:8081"

def post_reply(email, body, sender="lead", mins_ago=0):
    payload = {
        "email": email,
        "body": body,
        "sender": sender,
        "timestamp": time.time() - (mins_ago * 60),
    }
    req = urllib.request.Request(
        f"{BASE}/webhook/reply",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read())
        return data.get("analysis", data)

def divider(num, title, expected):
    print(f"\n{'='*70}")
    print(f"  THREAD {num}: {title}")
    print(f"  Expected: {expected}")
    print(f"{'='*70}")

def log(r):
    score = r["score"]
    state = r["state"]
    momentum = r.get("momentum", "—")
    explanation = r.get("explanation", [])
    breakdown = r.get("score_breakdown", {})
    nonzero = {k: v for k, v in breakdown.items() if v != 0}
    print(f"  Score:      {score}/100")
    print(f"  Band:       {state}")
    print(f"  Momentum:   {momentum}")
    print(f"  Explain:    {explanation}")
    print(f"  Breakdown:  {nonzero}")
    return {"score": score, "state": state, "momentum": momentum}


print("=" * 70)
print("  🧪 ROUND 2 — VENDOR EVAL BONUS STRESS TEST")
print("  Testing for false inflation from pilot/trial/timeline patterns.")
print("=" * 70)

results = {}

# ─── THREAD 1: Casual Pilot Language ───
divider(1, "Casual Pilot Language", "Curious at best — 'try' alone should NOT inflate")
r = post_reply("r2-t1@synth.com",
    "Maybe we could try this with a small group sometime next month if it makes sense.")
results[1] = log(r)

# ─── THREAD 2: Vendor Mention Without Action ───
divider(2, "Vendor Mention Without Action", "Curious — no bonus, no Ready Now")
r = post_reply("r2-t2@synth.com",
    "We're also looking at two other tools in this space.")
results[2] = log(r)

# ─── THREAD 3: Timeline Without Depth ───
divider(3, "Timeline Without Depth", "Low-mid — not Ready Now")
r = post_reply("r2-t3@synth.com",
    "Can we speak tomorrow?")
results[3] = log(r)

# ─── THREAD 4: Real Active Evaluation ───
divider(4, "Real Active Evaluation", "Ready Now — vendor bonus fires, momentum rising")
r = post_reply("r2-t4@synth.com",
    "We're evaluating two platforms this week. If this checks out, we want to run a "
    "2-week pilot with 6 reps starting Monday. Can you walk us through it tomorrow?")
results[4] = log(r)

# ─── THREAD 5: Budget Gate + Urgency ───
divider(5, "Budget Gate + Urgency", "Mid-high Curious or low Evaluating — not Ready Now")
r = post_reply("r2-t5@synth.com",
    "Budget resets next quarter but if pricing works we'd want to test immediately.")
results[5] = log(r)

# ─── THREAD 6: Pain Without Timeline ───
divider(6, "Pain Without Timeline", "High Evaluating, maybe borderline Ready Now, no vendor bonus")
r = post_reply("r2-t6@synth.com",
    "Our reps respond randomly and it's hurting conversion. We need a better prioritization system.")
results[6] = log(r)

# ─── THREAD 7: Curious Technical + Pilot Mention ───
divider(7, "Curious Technical + Pilot Mention", "Curious — no inflation")
r = post_reply("r2-t7@synth.com",
    "Is this rule-based or ML? Could we trial this at some point?")
results[7] = log(r)

# ─── THREAD 8: Contradictory Signals ───
divider(8, "Contradictory Signals", "Low-mid Curious — negation should suppress")
r = post_reply("r2-t8@synth.com",
    "We're pretty happy with our current setup but open to testing if it's easy.")
results[8] = log(r)

# ─── THREAD 9: Long Operational Detail ───
divider(9, "Long Operational Detail", "High Evaluating, maybe Ready Now, strong depth")
r = post_reply("r2-t9@synth.com",
    "We manage 14 SDRs across regions. Replies come in unevenly and reps cherry-pick "
    "easier threads. We've tried inbox tagging but it doesn't solve prioritization. "
    "If we deployed this, what would rollout look like?")
results[9] = log(r)

# ─── THREAD 10: Aggressive Buyer ───
divider(10, "Aggressive Buyer", "Strong Ready Now, >60, momentum rising")
r = post_reply("r2-t10@synth.com",
    "We're in final vendor selection. Decision this week. Need pilot details, "
    "onboarding timeline, pricing breakdown, and integration specifics. "
    "Can you meet tomorrow 10am?")
results[10] = log(r)


# ═══════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════
print(f"\n{'='*70}")
print("  📋 ROUND 2 SUMMARY")
print(f"{'='*70}")

band_counts = {"Ready Now": 0, "Evaluating": 0, "Curious": 0, "Noise": 0}
for t in range(1, 11):
    state = results[t]["state"]
    band_counts.setdefault(state, 0)
    band_counts[state] += 1

total = sum(band_counts.values())
ready_pct = (band_counts.get("Ready Now", 0) / total * 100) if total else 0

print(f"\n  Band Distribution:")
for band in ["Ready Now", "Evaluating", "Curious", "Noise"]:
    count = band_counts.get(band, 0)
    pct = count / total * 100 if total else 0
    print(f"    {band:15s}: {count:2d} ({pct:.0f}%)")

print(f"\n  Ready Now %: {ready_pct:.0f}%  {'⚠️ AGGRESSIVE >20%' if ready_pct > 20 else '✅ Healthy'}")

# Specific checks
issues = []

# Thread 1: casual "try" should not inflate
if results[1]["state"] == "Ready Now":
    issues.append("T1 casual 'try' hit Ready Now — vendor_eval inflating")
    print(f"  ❌ T1 Casual pilot = {results[1]['score']}/{results[1]['state']}")
else:
    print(f"  ✅ T1 Casual pilot = {results[1]['score']}/{results[1]['state']}")

# Thread 2: vendor mention alone
if results[2]["state"] in ["Ready Now", "Evaluating"]:
    issues.append(f"T2 vendor mention alone = {results[2]['state']}")
    print(f"  ❌ T2 Vendor mention = {results[2]['score']}/{results[2]['state']}")
else:
    print(f"  ✅ T2 Vendor mention = {results[2]['score']}/{results[2]['state']}")

# Thread 3: timeline alone
if results[3]["state"] == "Ready Now":
    issues.append("T3 timeline alone hit Ready Now")
    print(f"  ❌ T3 Timeline alone = {results[3]['score']}/{results[3]['state']}")
else:
    print(f"  ✅ T3 Timeline alone = {results[3]['score']}/{results[3]['state']}")

# Thread 4: should be Ready Now
if results[4]["state"] != "Ready Now":
    issues.append(f"T4 real evaluation = {results[4]['state']} (expected Ready Now)")
    print(f"  ⚠️ T4 Real evaluation = {results[4]['score']}/{results[4]['state']}")
else:
    print(f"  ✅ T4 Real evaluation = {results[4]['score']}/{results[4]['state']}")

# Thread 7: trial mention should not inflate
if results[7]["state"] == "Ready Now":
    issues.append("T7 casual trial hit Ready Now")
    print(f"  ❌ T7 Casual trial = {results[7]['score']}/{results[7]['state']}")
else:
    print(f"  ✅ T7 Casual trial = {results[7]['score']}/{results[7]['state']}")

# Thread 8: negation should suppress
if results[8]["state"] in ["Ready Now", "Evaluating"]:
    issues.append(f"T8 contradictory = {results[8]['state']} (negation should suppress)")
    print(f"  ⚠️ T8 Contradictory = {results[8]['score']}/{results[8]['state']}")
else:
    print(f"  ✅ T8 Contradictory = {results[8]['score']}/{results[8]['state']}")

# Thread 10: should be Ready Now
if results[10]["state"] != "Ready Now":
    issues.append(f"T10 aggressive buyer = {results[10]['state']} (expected Ready Now)")
    print(f"  ⚠️ T10 Aggressive buyer = {results[10]['score']}/{results[10]['state']}")
else:
    print(f"  ✅ T10 Aggressive buyer = {results[10]['score']}/{results[10]['state']}")

if issues:
    print(f"\n  ⚠️ ISSUES: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        print(f"    {i}. {issue}")
else:
    print(f"\n  🎯 ALL THREADS BEHAVED AS EXPECTED")

print(f"{'='*70}")
