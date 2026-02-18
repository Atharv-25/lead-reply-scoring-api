"""
12-THREAD SYNTHETIC BATCH TEST
Pure observation. No weight modifications.
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

def agent_reply(email, body, mins_ago=0):
    post_reply(email, body, sender="agent", mins_ago=mins_ago)

def divider(num, title, expected):
    print(f"\n{'='*70}")
    print(f"  THREAD {num}: {title}")
    print(f"  Expected: {expected}")
    print(f"{'='*70}")

def log_result(r, label=""):
    score = r["score"]
    state = r["state"]
    momentum = r.get("momentum", "—")
    explanation = r.get("explanation", [])
    breakdown = r.get("score_breakdown", {})
    print(f"  Score:      {score}/100")
    print(f"  Band:       {state}")
    print(f"  Momentum:   {momentum}")
    print(f"  Explain:    {explanation}")
    # Show breakdown keys with nonzero values
    nonzero = {k: v for k, v in breakdown.items() if v != 0}
    print(f"  Breakdown:  {nonzero}")
    if label:
        print(f"  {label}")
    return {"score": score, "state": state, "momentum": momentum,
            "explanation": explanation, "breakdown": nonzero}


# ═══════════════════════════════════════════
print("=" * 70)
print("  🧪 12-THREAD SYNTHETIC BATCH TEST")
print("  Rule: NO weight modifications. Observe only.")
print("=" * 70)

results = {}

# ─── THREAD 1: Real Buyer Escalation ───
divider(1, "Real Buyer Escalation", "Gradual rise → Ready Now")
email = "thread1-buyer@synth.com"
scores = []

r = post_reply(email, "Hey this is interesting. We've been trying to clean up our outbound replies. How does this work exactly?", mins_ago=240)
scores.append(r["score"])
print(f"  Reply 1: score={r['score']}, state={r['state']}")

agent_reply(email, "Great question! Here's how it works...", mins_ago=200)

r = post_reply(email, "We're currently using Apollo + HubSpot. Our reps are honestly drowning in replies and prioritizing randomly.", mins_ago=180)
scores.append(r["score"])
print(f"  Reply 2: score={r['score']}, state={r['state']}, momentum={r.get('momentum')}")

agent_reply(email, "I see — that's a common pain point.", mins_ago=150)

r = post_reply(email, "If we wanted to roll this out across 12 SDRs, what does implementation look like? And how fast can we test impact?", mins_ago=120)
scores.append(r["score"])
print(f"  Reply 3: score={r['score']}, state={r['state']}, momentum={r.get('momentum')}")

agent_reply(email, "Implementation takes about 2 weeks...", mins_ago=90)

r = post_reply(email, "Also how does pricing scale with volume?", mins_ago=60)
scores.append(r["score"])
print(f"  Reply 4: score={r['score']}, state={r['state']}, momentum={r.get('momentum')}")

print(f"  Trajectory: {' → '.join(str(s) for s in scores)}")
results[1] = {"scores": scores, "final_state": r["state"], "momentum": r.get("momentum")}


# ─── THREAD 2: Polite but Empty ───
divider(2, "Polite but Empty", "Low — Noise or low Curious")
r = post_reply("thread2-polite@synth.com",
    "Sounds interesting. Appreciate you sharing. We'll keep this in mind for future initiatives.")
log_result(r)
results[2] = {"score": r["score"], "state": r["state"]}


# ─── THREAD 3: Fake Urgency Trap ───
divider(3, "Fake Urgency Trap", "Mid at best — not Ready Now")
r = post_reply("thread3-urgent@synth.com",
    "Can you send pricing today? Need to review internally ASAP.")
log_result(r)
results[3] = {"score": r["score"], "state": r["state"]}


# ─── THREAD 4: Competitor but No Pain ───
divider(4, "Competitor but No Pain", "Curious — not Evaluating")
r = post_reply("thread4-comp@synth.com",
    "We're currently on Apollo and it works fine for us. Just exploring what else is out there.")
log_result(r)
results[4] = {"score": r["score"], "state": r["state"]}


# ─── THREAD 5: Deep Analytical, No Buying ───
divider(5, "Deep Analytical, No Buying", "Mid — not Ready Now")
r = post_reply("thread5-analyst@synth.com",
    "How do you calculate momentum delta across threads? Is it rule-based or vector-weighted? Also how are you handling negation logic?")
log_result(r)
results[5] = {"score": r["score"], "state": r["state"]}


# ─── THREAD 6: Sarcasm / Negation ───
divider(6, "Sarcasm / Negation", "Low — pain should not fire strongly")
r = post_reply("thread6-sarcasm@synth.com",
    "Yeah we're totally drowning in leads 😂 not really though, pipeline's been slow actually.")
log_result(r)
results[6] = {"score": r["score"], "state": r["state"]}


# ─── THREAD 7: Cooling After Heat ───
divider(7, "Cooling After Heat", "High early → Cooling after last reply")
email7 = "thread7-cooling@synth.com"

r = post_reply(email7, "We're actively evaluating tools to help our reps prioritize replies better.", mins_ago=300)
print(f"  Reply 1: score={r['score']}, state={r['state']}")

agent_reply(email7, "Great — here's what we offer.", mins_ago=250)

r = post_reply(email7, "Our response times are honestly inconsistent and it's hurting us.", mins_ago=200)
print(f"  Reply 2: score={r['score']}, state={r['state']}, momentum={r.get('momentum')}")
hot_score = r["score"]

agent_reply(email7, "That's a common challenge.", mins_ago=150)

r = post_reply(email7, "Actually let's revisit this next quarter once budgets open.", mins_ago=60)
print(f"  Reply 3: score={r['score']}, state={r['state']}, momentum={r.get('momentum')}")
results[7] = {"hot": hot_score, "cold": r["score"], "momentum": r.get("momentum")}


# ─── THREAD 8: Signal Stuffing Attack ───
divider(8, "Signal Stuffing Attack", "High but not absurdly inflated")
r = post_reply("thread8-stuffed@synth.com",
    "We're scaling outbound, hiring 5 SDRs, drowning in replies, considering switching from Apollo, "
    "need HubSpot integration, retraining workflow, what's pricing and timeline?")
log_result(r)
results[8] = {"score": r["score"], "state": r["state"]}


# ─── THREAD 9: Multi-Turn Slow Build ───
divider(9, "Multi-Turn Slow Build", "Gradual growth → ends Evaluating")
email9 = "thread9-slow@synth.com"
scores9 = []

r = post_reply(email9, "Interesting.", mins_ago=360)
scores9.append(r["score"])
print(f"  Reply 1: score={r['score']}, state={r['state']}")

agent_reply(email9, "Want to know more?", mins_ago=300)

r = post_reply(email9, "How are you different from inbox tags?", mins_ago=240)
scores9.append(r["score"])
print(f"  Reply 2: score={r['score']}, state={r['state']}")

agent_reply(email9, "We go much deeper than tags.", mins_ago=180)

r = post_reply(email9, "Does this track response time too?", mins_ago=120)
scores9.append(r["score"])
print(f"  Reply 3: score={r['score']}, state={r['state']}, momentum={r.get('momentum')}")

agent_reply(email9, "Yes, SLA tracking is built in.", mins_ago=90)

r = post_reply(email9, "We've actually struggled with reps replying FIFO.", mins_ago=30)
scores9.append(r["score"])
print(f"  Reply 4: score={r['score']}, state={r['state']}, momentum={r.get('momentum')}")

print(f"  Trajectory: {' → '.join(str(s) for s in scores9)}")
results[9] = {"scores": scores9, "final_state": r["state"], "momentum": r.get("momentum")}


# ─── THREAD 10: Density Spam ───
divider(10, "Density Spam", "Low or moderate — not Ready Now")
r = post_reply("thread10-spam@synth.com",
    "Scaling hiring drowning switching integration Apollo HubSpot retraining churn pricing timeline urgent.")
log_result(r)
results[10] = {"score": r["score"], "state": r["state"]}


# ─── THREAD 11: Budget Objection ───
divider(11, "Budget Objection", "Moderate — not high")
r = post_reply("thread11-budget@synth.com",
    "This looks good but budget's tight this quarter. What's your starting price?")
log_result(r)
results[11] = {"score": r["score"], "state": r["state"]}


# ─── THREAD 12: High Intent + Fast Action ───
divider(12, "High Intent + Fast Action", "High — Ready Now, strong momentum")
r = post_reply("thread12-intent@synth.com",
    "We're comparing two vendors this week. If we like this, we'd want to pilot with 8 reps immediately. "
    "Can we see a live walkthrough tomorrow?")
log_result(r)
results[12] = {"score": r["score"], "state": r["state"], "momentum": r.get("momentum")}


# ═══════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════
print(f"\n{'='*70}")
print("  📋 BATCH SUMMARY")
print(f"{'='*70}")

band_counts = {"Ready Now": 0, "Evaluating": 0, "Curious": 0, "Noise": 0}
issues = []

for t in [1, 8, 12]:
    state = results[t].get("final_state", results[t].get("state"))
    band_counts[state] += 1
for t in [2, 3, 4, 5, 6, 7, 9, 10, 11]:
    state = results[t].get("final_state", results[t].get("state"))
    band_counts[state] += 1

total = sum(band_counts.values())
ready_pct = (band_counts["Ready Now"] / total * 100) if total else 0

print(f"\n  Band Distribution:")
for band, count in band_counts.items():
    pct = count / total * 100 if total else 0
    print(f"    {band:15s}: {count:2d} ({pct:.0f}%)")

print(f"\n  Ready Now %: {ready_pct:.0f}%  {'⚠️ INFLATION' if ready_pct > 15 else '✅ Healthy'}")

# Check specific rules
t2_score = results[2]["score"]
if t2_score > 25:
    issues.append(f"Thread 2 (Polite) = {t2_score} → richness leaking")
    print(f"  ❌ Thread 2 polite fluff = {t2_score} (expected <25)")
else:
    print(f"  ✅ Thread 2 polite fluff = {t2_score}")

t3_state = results[3]["state"]
if t3_state == "Ready Now":
    issues.append(f"Thread 3 (Fake Urgency) hit Ready Now")
    print(f"  ❌ Thread 3 fake urgency = {results[3]['score']}/{t3_state}")
else:
    print(f"  ✅ Thread 3 fake urgency = {results[3]['score']}/{t3_state}")

t10_score = results[10]["score"]
if t10_score > 50:
    issues.append(f"Thread 10 (Spam) = {t10_score} → density logic weak")
    print(f"  ❌ Thread 10 spam = {t10_score}")
else:
    print(f"  ✅ Thread 10 spam = {t10_score}")

t7_momentum = results[7].get("momentum", "—")
if t7_momentum != "Cooling":
    issues.append(f"Thread 7 cooling momentum = {t7_momentum}")
    print(f"  ⚠️ Thread 7 cooling momentum = {t7_momentum} (expected Cooling)")
else:
    print(f"  ✅ Thread 7 cooling momentum = {t7_momentum}")

if issues:
    print(f"\n  ⚠️ ISSUES FOUND: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        print(f"    {i}. {issue}")
else:
    print(f"\n  🎯 ALL THREADS BEHAVED AS EXPECTED")

print(f"{'='*70}")
