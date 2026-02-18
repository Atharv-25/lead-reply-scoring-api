"""
TEST FIXES: Verification Script for Thread 4 & Thread 5
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

def log(num, title, r):
    print(f"\n{'='*70}")
    print(f"  THREAD {num}: {title}")
    print(f"{'='*70}")
    
    score = r["score"]
    state = r["state"]
    explanation = r.get("explanation", [])
    breakdown = r.get("score_breakdown", {})
    nonzero = {k: v for k, v in breakdown.items() if v != 0}
    
    print(f"  Score:      {score}/100")
    print(f"  Band:       {state}")
    print(f"  Explain:    {explanation}")
    print(f"  Breakdown:  {nonzero}\n")
    return {"score": score, "state": state, "breakdown": breakdown}

print("=" * 70)
print("  🛠️ VERIFYING FIXES FOR ROUND 2 OBSERVATIONS")
print("=" * 70)

# THREAD 4
# Issue: "evaluating two platforms" didn't trigger competitor signal -> no bonus -> score 15
print("\n>>> Testing Thread 4 Fix (Competitor Pattern)")
r4 = post_reply("fix-t4@test.com", 
    "We're evaluating two platforms this week. If this checks out, we want to run a "
    "2-week pilot with 6 reps starting Monday. Can you walk us through it tomorrow?")
log(4, "Real Active Evaluation", r4)

# THREAD 5
# Issue: "Budget resets next quarter" triggered disengage penalty (-30) -> score 0
print("\n>>> Testing Thread 5 Fix (Budget Disengagement Exception)")
r5 = post_reply("fix-t5@test.com", 
    "Budget resets next quarter but if pricing works we'd want to test immediately.")
log(5, "Budget Gate + Urgency", r5)

print("\n" + "="*70)
print("  EXPECTED RESULTS:")
print("  Thread 4: Ready Now (>60) | Competitor + Vendor Bonus (+10)")
print("  Thread 5: No -30 penalty  | Disengage Penalty = 0")
print("="*70)
