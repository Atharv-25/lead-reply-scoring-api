"""
🔥 FOUNDER-LEVEL EDGE MATRIX — 20 Corner Cases
Rule: NO tweaks during run. Observe only.
"""

import json, time, urllib.request

BASE = "http://localhost:8081"
RUN_ID = str(int(time.time()))  # unique per run to avoid reply accumulation

def post(email, body, sender="lead", mins_ago=0):
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
        return json.loads(res.read()).get("analysis", {})

def log(num, title, expected, r):
    score = r.get("score", 0)
    state = r.get("state", "?")
    mom   = r.get("momentum", "Stable")
    expl  = r.get("explanation", [])
    bd    = r.get("score_breakdown", {})
    nz    = {k: v for k, v in bd.items() if v != 0}

    print(f"\n{'='*70}")
    print(f"  #{num}: {title}")
    print(f"{'='*70}")
    print(f"  Score:      {score}/100")
    print(f"  Band:       {state}")
    print(f"  Momentum:   {mom}")
    print(f"  Explain:    {expl}")
    print(f"  Breakdown:  {nz}")
    print(f"  Expected:   {expected}")
    return {"num": num, "title": title, "score": score, "state": state,
            "momentum": mom, "expected": expected}

results = []

print("=" * 70)
print("  🔥 FOUNDER-LEVEL EDGE MATRIX — 20 CORNER CASES")
print("  Rule: NO tweaks during run. Observe only.")
print("=" * 70)

# ─── 1A: Single Word — "Interested." ───
r = post(f"edge1a{RUN_ID}@test.com", "Interested.")
results.append(log("1A", "Single Word: 'Interested.'", "Low Curious (5-12)", r))

# ─── 1B: Single Word — "Price?" ───
r = post(f"edge1b{RUN_ID}@test.com", "Price?")
results.append(log("1B", "Single Word: 'Price?'", "Low-mid Curious", r))

# ─── 1C: Single Word — "Call me." ───
r = post(f"edge1c{RUN_ID}@test.com", "Call me.")
results.append(log("1C", "Single Word: 'Call me.'", "Curious, NOT Ready Now", r))

# ─── 2: Very Short + Timeline ───
r = post(f"edge2{RUN_ID}@test.com", "Let's talk tomorrow.")
results.append(log("2", "Very Short + Timeline", "Curious, NOT Ready Now", r))

# ─── 3: Timeline + No Context ───
r = post(f"edge3{RUN_ID}@test.com", "ASAP.")
results.append(log("3", "Timeline No Context: 'ASAP.'", "Noise or very low Curious", r))

# ─── 4: Polite Multi-Turn Shallow ───
post(f"edge4{RUN_ID}@test.com", "Looks good.", mins_ago=120)
post(f"edge4{RUN_ID}@test.com", "Will review internally.", mins_ago=60)
r = post(f"edge4{RUN_ID}@test.com", "Following up later.")
results.append(log("4", "Polite Multi-Turn Shallow (3 replies)", "Shallow penalty. NOT above Curious", r))

# ─── 5: Fake Depth Jargon Spam ───
r = post(f"edge5{RUN_ID}@test.com",
    "We need scalable prioritization orchestration to optimize SDR throughput velocity.")
results.append(log("5", "Fake Depth Jargon Spam", "Moderate Curious at most, NOT Evaluating", r))

# ─── 6: Real Operational Depth ───
r = post(f"edge6{RUN_ID}@test.com",
    "We have 11 SDRs. Replies come in uneven waves. Some reps respond within 5 mins, others 2 hours. Managers can't see response lag clearly.")
results.append(log("6", "Real Operational Depth", "High Evaluating, possibly borderline Ready Now", r))

# ─── 7: Real Pain + Budget Delay ───
r = post(f"edge7{RUN_ID}@test.com",
    "This is exactly our issue, but budgets open next quarter.")
results.append(log("7", "Real Pain + Budget Delay", "High Evaluating, NOT Ready Now", r))

# ─── 8: Vendor Comparison Without Pilot ───
r = post(f"edge8{RUN_ID}@test.com",
    "We're comparing you with Apollo and two other tools.")
results.append(log("8", "Vendor Compare, No Pilot", "Curious or low Evaluating. Bonus NOT firing", r))

# ─── 9: Pilot Without Vendor Mention ───
r = post(f"edge9{RUN_ID}@test.com",
    "Can we run a 2-week pilot with 5 reps?")
results.append(log("9", "Pilot, No Vendor", "Evaluating, NOT auto Ready Now", r))

# ─── 10: Vendor + Pilot + No Timeline ───
r = post(f"edge10{RUN_ID}@test.com",
    "We're evaluating two vendors and would like to pilot.")
results.append(log("10", "Vendor + Pilot, No Timeline", "Evaluating. Bonus NOT fully firing", r))

# ─── 11: Vendor + Timeline + No Pilot ───
r = post(f"edge11{RUN_ID}@test.com",
    "We're deciding this week between platforms.")
results.append(log("11", "Vendor + Timeline, No Pilot", "High Curious / Evaluating. Bonus NOT firing", r))

# ─── 12: All Three (True Late Stage) ───
r = post(f"edge12{RUN_ID}@test.com",
    "We're evaluating two platforms this week. Want to run a pilot starting Monday. Can we meet tomorrow?")
results.append(log("12", "All Three — True Late Stage", "Ready Now", r))

# ─── 13: Negation Trick ───
r = post(f"edge13{RUN_ID}@test.com",
    "We're NOT actively evaluating vendors.")
results.append(log("13", "Negation Trick", "Noise or Curious. Vendor signal suppressed", r))

# ─── 14: Sarcasm Depth ───
r = post(f"edge14{RUN_ID}@test.com",
    "Yeah we're drowning in replies 😂 (wish that were true).")
results.append(log("14", "Sarcasm Depth", "Low. Pain suppressed", r))

# ─── 15: Contradictory ───
r = post(f"edge15{RUN_ID}@test.com",
    "We're happy with our setup but exploring alternatives.")
results.append(log("15", "Contradictory", "Curious. Switch bonus reduced", r))

# ─── 16: Sudden Cooling ───
post(f"edge16{RUN_ID}@test.com", "We need help prioritizing replies urgently.", mins_ago=4320)  # 3 days ago
r = post(f"edge16{RUN_ID}@test.com", "Let's revisit next quarter.")
results.append(log("16", "Sudden Cooling (hot → disengage)", "Score drop. Momentum cooling. Possibly downgraded", r))

# ─── 17: Massive Signal Stuffing ───
r = post(f"edge17{RUN_ID}@test.com",
    "We're scaling hiring drowning replies switching Apollo HubSpot integration retraining pilot timeline pricing ASAP.")
results.append(log("17", "Massive Signal Stuffing", "Spam cap holds. NOT Evaluating", r))

# ─── 18: Long Thread Escalation ───
post(f"edge18{RUN_ID}@test.com", "How does it work?", mins_ago=180)
post(f"edge18{RUN_ID}@test.com", "We use HubSpot.", mins_ago=120)
post(f"edge18{RUN_ID}@test.com", "Reps miss replies.", mins_ago=60)
r = post(f"edge18{RUN_ID}@test.com",
    "If we piloted this, how fast could we deploy across 9 SDRs?")
results.append(log("18", "Long Thread Escalation (4 replies)", "Gradual build. Ends Evaluating or Ready Now", r))

# ─── 19: Budget Objection Only ───
r = post(f"edge19{RUN_ID}@test.com",
    "What's the lowest pricing tier?")
results.append(log("19", "Budget Objection Only", "Curious. NOT Evaluating", r))

# ─── 20: Silence Test ───
post(f"edge20{RUN_ID}@test.com",
    "We need to switch from Apollo. How does API integration work? Budget approved.", mins_ago=7200)  # 5 days ago
r = post(f"edge20{RUN_ID}@test.com", "Thanks for following up.", mins_ago=0)
results.append(log("20", "Silence Test (5d gap)", "Cooling reduces priority. Momentum shifts", r))

# ─────────────────────────────────────────
# SUMMARY TABLE
# ─────────────────────────────────────────
print("\n\n" + "=" * 100)
print("  📋 EDGE MATRIX SUMMARY")
print("=" * 100)
print(f"  {'#':<5} {'Test':<45} {'Score':<7} {'Band':<15} {'Momentum':<10} {'Expected'}")
print("-" * 100)

flags = []
for r in results:
    line = f"  {r['num']:<5} {r['title']:<45} {r['score']:<7} {r['state']:<15} {r['momentum']:<10} {r['expected']}"
    print(line)

    # Flag potential problems
    s, st = r["score"], r["state"]
    n = r["num"]

    if n in ("1A","1B","1C","2","3") and st == "Ready Now":
        flags.append(f"⚠️ #{n}: Weak thread reached Ready Now ({s})")
    if n == "4" and st not in ("Noise", "Curious"):
        flags.append(f"⚠️ #4: Shallow multi-turn above Curious ({st}, {s})")
    if n == "5" and st in ("Evaluating", "Ready Now"):
        flags.append(f"⚠️ #5: Jargon spam reached {st} ({s})")
    if n == "6" and st == "Noise":
        flags.append(f"⚠️ #6: Real operational depth stuck in Noise ({s})")
    if n == "7" and st == "Ready Now":
        flags.append(f"⚠️ #7: Budget delay reached Ready Now ({s})")
    if n in ("8","9","10","11") and st == "Ready Now":
        flags.append(f"⚠️ #{n}: Incomplete signal set reached Ready Now ({s})")
    if n == "12" and st != "Ready Now":
        flags.append(f"⚠️ #12: True late stage NOT Ready Now ({st}, {s})")
    if n == "13" and st in ("Evaluating", "Ready Now"):
        flags.append(f"⚠️ #13: Negation trick reached {st} ({s})")
    if n == "14" and st in ("Evaluating", "Ready Now"):
        flags.append(f"⚠️ #14: Sarcasm depth reached {st} ({s})")
    if n == "15" and st == "Ready Now":
        flags.append(f"⚠️ #15: Contradictory reached Ready Now ({s})")
    if n == "17" and st in ("Evaluating", "Ready Now"):
        flags.append(f"⚠️ #17: Signal stuffing beat spam cap ({st}, {s})")
    if n == "19" and st in ("Evaluating", "Ready Now"):
        flags.append(f"⚠️ #19: Budget-only reached {st} ({s})")

print("\n" + "=" * 100)
if flags:
    print(f"  🚨 {len(flags)} FLAG(S) DETECTED:")
    for f in flags:
        print(f"    {f}")
else:
    print("  ✅ ZERO FLAGS — ALL THREADS BEHAVED AS EXPECTED")
print("=" * 100)
