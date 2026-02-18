"""
=================================================================
  🔥 10-STAGE STRESS TEST PROTOCOL
  Goal: Find where the scoring engine BREAKS.
  Rule: NO weight modifications. Observe only.
=================================================================
"""

import json
import time
import urllib.request

BASE = "http://localhost:8081"

# ── Helpers ──

def post_reply(email, body, sender="lead", mins_ago=0):
    """Send a single reply to the webhook (the API format).
    Returns the analysis sub-object directly (score, state, breakdown, etc.)."""
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
        # API returns {success: true, analysis: {score, state, ...}}
        return data.get("analysis", data)

def get_dashboard():
    req = urllib.request.Request(f"{BASE}/api/dashboard")
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())

def divider(stage, title, goal):
    print(f"\n{'='*70}")
    print(f"  {stage}: {title}")
    print(f"  Goal: {goal}")
    print(f"{'='*70}")

def show(score, state, breakdown, explanation, verdict, notes=""):
    print(f"  Score:      {score}/100")
    print(f"  State:      {state}")
    print(f"  Breakdown:  {breakdown}")
    print(f"  Explain:    {explanation}")
    print(f"  Verdict:    {verdict}")
    if notes:
        print(f"  Notes:      {notes}")
    return {"score": score, "state": state, "verdict": verdict, "notes": notes}


# ════════════════════════════════════════════════════════════════
#   STAGE 1 — SIGNAL SATURATION TEST
# ════════════════════════════════════════════════════════════════

def stage_1():
    divider("🔥 STAGE 1", "Signal Saturation Test",
            "Does stuffing every signal explode the score past realistic bounds?")

    body = (
        "We're scaling our outbound team from 4 to 12 SDRs next quarter. "
        "Honestly, we're drowning in replies — our team spends 3 hours a day "
        "just triaging who to call back. We looked at Apollo but their scoring "
        "was too basic and kept flagging the wrong leads. We need something that "
        "integrates with HubSpot directly since that's our CRM. We'd also need "
        "to retrain the team on whatever we bring in, so implementation support "
        "matters. A few questions: 1) How does your scoring handle multi-touch "
        "sequences where the same lead replies across different campaigns? "
        "2) Can we customize the intent bands based on our ICP criteria? "
        "3) What does onboarding look like for a team our size? "
        "We're looking at a 2-week timeline to decide and pricing is a factor — "
        "what's the cost for 12 seats?"
    )

    r = post_reply("saturated@stress.com", body)
    score = r["score"]

    if score >= 95:
        verdict = "⚠️ CONCERN — Superhuman hot. Stacking too additive."
    elif score >= 80:
        verdict = "✅ HEALTHY — High but realistic for a signal-saturated reply."
    elif score >= 60:
        verdict = "✅ GOOD — Caps are working. Doesn't blindly stack."
    else:
        verdict = "🤔 UNEXPECTED — Saturated reply scoring too low?"

    return show(score, r["state"], r.get("breakdown", {}),
                r.get("explanation", []), verdict)


# ════════════════════════════════════════════════════════════════
#   STAGE 2 — POLITE LONG EMAIL TRAP
# ════════════════════════════════════════════════════════════════

def stage_2():
    divider("🧊 STAGE 2", "Polite Long Email Trap",
            "Does word count inflate score? 150-word fluff should stay LOW.")

    body = (
        "Hi there! Thanks so much for reaching out to us. I really appreciate "
        "you taking the time to send over that information. It was very kind of "
        "you and our team enjoyed reading through the materials. Everything "
        "looks very professional and well put together. We think your company "
        "seems like a great organization and we admire the work you've been "
        "doing in the space. The presentation deck was visually appealing and "
        "the content was easy to follow. We shared it around the office and "
        "several people commented on how nice it looked. Thank you again for "
        "thinking of us and for your patience. We'll keep your information on "
        "file and if anything comes up in the future, we'll certainly keep you "
        "in mind. Wishing you and your team all the best. Have a wonderful rest "
        "of your week and a great weekend ahead. Looking forward to staying in "
        "touch. Best regards and warmest wishes from everyone here."
    )

    r = post_reply("polite-fluff@stress.com", body)
    score = r["score"]

    if score >= 30:
        verdict = "❌ FAIL — Richness logic is leaking. Fluff inflates score."
    elif score >= 15:
        verdict = "⚠️ BORDERLINE — Some leakage but not critical."
    else:
        verdict = "✅ PASS — Engine correctly ignores polite fluff."

    return show(score, r["state"], r.get("breakdown", {}),
                r.get("explanation", []), verdict)


# ════════════════════════════════════════════════════════════════
#   STAGE 3 — SARCASM & NEGATION TEST
# ════════════════════════════════════════════════════════════════

def stage_3():
    divider("🎭 STAGE 3", "Sarcasm & Negation Test",
            "Do negations and sarcasm accidentally fire positive signals?")

    results = []

    # 3a: Sarcasm
    r = post_reply("sarcasm@stress.com",
        "Yeah sure, we're totally drowning in leads 😂 "
        "Our massive team of two people is just overwhelmed with all "
        "the zero inbound we get. Very funny."
    )
    s = r["score"]
    v = f"⚠️ SARCASM LEAKED — Score {s}" if s >= 30 else f"✅ SARCASM OK — Score {s}"
    print(f"\n  3a) Sarcasm: score={s}, state={r['state']}")
    print(f"      Breakdown: {r.get('breakdown', {})}")
    print(f"      Verdict: {v}")
    results.append({"sub": "sarcasm", "score": s, "verdict": v})

    # 3b: Negation
    r = post_reply("negation@stress.com",
        "Not looking to switch from Apollo. We're happy with what we have. "
        "We're not hiring SDRs anymore, actually we just downsized."
    )
    s = r["score"]
    v = f"⚠️ NEGATION LEAKED — Score {s}" if s >= 30 else f"✅ NEGATION OK — Score {s}"
    print(f"\n  3b) Negation: score={s}, state={r['state']}")
    print(f"      Breakdown: {r.get('breakdown', {})}")
    print(f"      Verdict: {v}")
    results.append({"sub": "negation", "score": s, "verdict": v})

    # 3c: Mixed negation + real question
    r = post_reply("mixed-neg@stress.com",
        "We're not switching from Apollo, but I do have a question — "
        "how does your system handle multi-language reply detection?"
    )
    s = r["score"]
    v = f"⚠️ MIXED OVER-WEIGHT — Score {s}" if s >= 40 else f"✅ MIXED OK — Score {s}"
    print(f"\n  3c) Mixed negation+question: score={s}, state={r['state']}")
    print(f"      Breakdown: {r.get('breakdown', {})}")
    print(f"      Verdict: {v}")
    results.append({"sub": "mixed", "score": s, "verdict": v})

    overall = "✅ PASS" if all(r["score"] < 30 for r in results[:2]) else "⚠️ NEEDS REVIEW"
    print(f"\n  Stage 3 Overall: {overall}")
    return {"sub_results": results, "overall": overall, "verdict": overall}


# ════════════════════════════════════════════════════════════════
#   STAGE 4 — MULTI-TURN ESCALATION
# ════════════════════════════════════════════════════════════════

def stage_4():
    divider("🧨 STAGE 4", "Multi-Turn Escalation",
            "Does score increase gradually across 4 replies? Believable curve?")

    email = "escalation@stress.com"
    scores = []

    # Reply 1: Curious
    res = post_reply(email, "Interesting, can you tell me more about what you do?", mins_ago=180)
    scores.append(res["score"])
    print(f"  Reply 1 (Curious):        score={res['score']}, state={res['state']}")

    # Reply 2: Light question
    res = post_reply(email, "How much does this cost? Is there a free trial?", mins_ago=120)
    scores.append(res["score"])
    print(f"  Reply 2 (Light question):  score={res['score']}, state={res['state']}")

    # Reply 3: Pain
    res = post_reply(email,
        "Our reps are spending too much time on unqualified leads. "
        "We lose about 2 hours per rep per day on bad outreach replies.",
        mins_ago=60)
    scores.append(res["score"])
    print(f"  Reply 3 (Pain):           score={res['score']}, state={res['state']}, momentum={res.get('momentum')}")

    # Reply 4: Competitor switch
    res = post_reply(email,
        "We've been using Apollo for this but honestly it's not cutting it. "
        "Their scoring is too simplistic. Can your tool integrate with Salesforce?",
        mins_ago=10)
    scores.append(res["score"])
    print(f"  Reply 4 (Competitor):     score={res['score']}, state={res['state']}, momentum={res.get('momentum')}")

    print(f"\n  Trajectory: {' → '.join(str(s) for s in scores)}")

    big_jumps = [scores[i + 1] - scores[i] for i in range(len(scores) - 1)]
    max_jump = max(big_jumps) if big_jumps else 0
    monotonic = all(scores[i] <= scores[i + 1] for i in range(len(scores) - 1))

    if not monotonic:
        verdict = f"⚠️ NON-MONOTONIC — Score decreased at some point. Jumps: {big_jumps}"
    elif max_jump > 40:
        verdict = f"⚠️ VIOLENT JUMP — Max single-step jump = {max_jump}."
    elif scores[-1] < 50:
        verdict = f"🤔 UNDER-SCORING — Full escalation only reaches {scores[-1]}?"
    else:
        verdict = f"✅ HEALTHY CURVE — Gradual escalation, max jump = {max_jump}."

    print(f"  Verdict: {verdict}")
    return {"scores": scores, "jumps": big_jumps, "verdict": verdict}


# ════════════════════════════════════════════════════════════════
#   STAGE 5 — FAKE URGENCY TRAP
# ════════════════════════════════════════════════════════════════

def stage_5():
    divider("🪤 STAGE 5", "Fake Urgency Trap",
            "Urgent language + no depth should NOT hit Ready Now.")

    r = post_reply("fake-urgent@stress.com",
        "Need pricing ASAP. Can you send a proposal today? "
        "We have a board meeting Thursday and need numbers. "
        "Please respond urgently."
    )
    score = r["score"]

    if score >= 60:
        verdict = f"❌ FAIL — Score {score}. Timeline amplifier too strong."
    elif score >= 40:
        verdict = f"⚠️ BORDERLINE — Score {score}. Urgency inflating moderately."
    else:
        verdict = f"✅ PASS — Score {score}. Engine sees through fake urgency."

    return show(score, r["state"], r.get("breakdown", {}),
                r.get("explanation", []), verdict)


# ════════════════════════════════════════════════════════════════
#   STAGE 6 — ANALYTICAL NON-BUYER
# ════════════════════════════════════════════════════════════════

def stage_6():
    divider("🧮 STAGE 6", "Analytical Non-Buyer",
            "Technical questions alone ≠ buying. Should not reach Ready Now.")

    r = post_reply("analyst@stress.com",
        "I have a few technical questions: "
        "1) What's your false positive rate on intent classification? "
        "2) How do you handle signal decay over multi-week threads? "
        "3) What ML model architecture are you using for scoring? "
        "Just curious about the technical side."
    )
    score = r["score"]

    if r["state"] == "Ready Now":
        verdict = f"❌ FAIL — Analytical non-buyer hitting Ready Now ({score})."
    elif score >= 50:
        verdict = f"⚠️ BORDERLINE — Score {score}. Analytical over-promoted."
    else:
        verdict = f"✅ PASS — Score {score}, state={r['state']}. Analytical ≠ buying."

    return show(score, r["state"], r.get("breakdown", {}),
                r.get("explanation", []), verdict)


# ════════════════════════════════════════════════════════════════
#   STAGE 7 — COLD AFTER HEAT
# ════════════════════════════════════════════════════════════════

def stage_7():
    divider("🧊 STAGE 7", "Cold After Heat",
            "Score should cool when lead disengages after hot start.")

    email = "cold-hot@stress.com"

    # Reply 1: High pain
    post_reply(email,
        "We're losing deals because our reps can't prioritize. "
        "We waste 40% of our outbound hours on bad leads.",
        mins_ago=300)

    # Reply 2: Implementation depth
    res_hot = post_reply(email,
        "Can you walk me through how the integration works with Salesforce? "
        "We'd need SSO and role-based access for 30 reps. What's the pricing?",
        mins_ago=200)
    hot_score = res_hot["score"]
    print(f"  After 2 hot replies:  score={hot_score}, state={res_hot['state']}, momentum={res_hot.get('momentum')}")

    # Reply 3: Cool down
    res_cold = post_reply(email,
        "Thanks for the info. Actually, we've decided to revisit this next quarter. "
        "We have other priorities right now. Appreciate your time.",
        mins_ago=10)
    cold_score = res_cold["score"]
    momentum = res_cold.get("momentum", "Unknown")
    print(f"  After cooling reply:  score={cold_score}, state={res_cold['state']}, momentum={momentum}")
    print(f"  Delta: {cold_score - hot_score}")

    if cold_score >= hot_score:
        verdict = f"❌ FAIL — Score didn't drop. {hot_score} → {cold_score}. No cooling."
    elif momentum != "Cooling":
        verdict = f"⚠️ CONCERN — Score dropped ({hot_score}→{cold_score}) but momentum={momentum}."
    else:
        verdict = f"✅ PASS — Score cooled {hot_score}→{cold_score}, momentum=Cooling."

    print(f"  Verdict: {verdict}")
    return {"hot": hot_score, "cold": cold_score, "momentum": momentum, "verdict": verdict}


# ════════════════════════════════════════════════════════════════
#   STAGE 8 — DISTRIBUTION STRESS
# ════════════════════════════════════════════════════════════════

def stage_8():
    divider("🧠 STAGE 8", "Distribution Stress",
            "100 synthetic threads → check band distribution. Ready Now ≤10%.")

    noise_bodies = [
        "Thanks!", "Got it.", "Ok sounds good", "Will check later",
        "Interesting", "Noted", "Sure thing", "Appreciate it",
        "Cool", "Let me think about it", "I'll get back to you",
        "Thanks for the follow up", "Received", "Understood", "Good to know",
    ]

    curious_bodies = [
        "How much does it cost?",
        "Can you send more info?",
        "What's the pricing?",
        "Sounds interesting, tell me more.",
        "What makes you different from others?",
    ]

    eval_bodies = [
        "We're looking at a few tools right now. How does onboarding work and what's the timeline?",
        "I'd like to schedule a demo. We have 10 reps. What integrations do you support?",
        "We need something that works with Salesforce. What's your implementation process?",
    ]

    buyer_body = (
        "We're drowning in unqualified leads and our reps waste hours daily. "
        "Currently on Apollo and it's not working. Need to switch ASAP. "
        "How does your integration work with HubSpot? What's pricing for 15 seats? "
        "We have budget approved and need to decide by end of month."
    )

    count = 0

    # 60 noise
    for i in range(60):
        body = noise_bodies[i % len(noise_bodies)]
        post_reply(f"noise-{i}@stress.com", body)
        count += 1

    # 20 curious
    for i in range(20):
        body = curious_bodies[i % len(curious_bodies)]
        post_reply(f"curious-{i}@stress.com", body)
        count += 1

    # 15 evaluating
    for i in range(15):
        body = eval_bodies[i % len(eval_bodies)]
        post_reply(f"eval-{i}@stress.com", body)
        count += 1

    # 5 real buyers
    for i in range(5):
        post_reply(f"buyer-{i}@stress.com", buyer_body)
        count += 1

    print(f"  Ingested {count} threads.")

    # Pull dashboard
    dash = get_dashboard()
    bd = dash.get("band_distribution", {})
    sections = dash.get("sections", {})

    ready_count = len(sections.get("ready_now", []))
    eval_count = len(sections.get("evaluating", []))
    curious_count = len(sections.get("curious", []))
    noise_count = len(sections.get("noise", []))
    total = ready_count + eval_count + curious_count + noise_count

    print(f"  Band Counts: Ready={ready_count}, Eval={eval_count}, Curious={curious_count}, Noise={noise_count}")
    print(f"  Total leads in DB: {total}")
    print(f"  Band Distribution %: {bd}")

    ready_pct = bd.get("ready_now", 0)

    if ready_pct > 10:
        verdict = f"⚠️ CONCERN — Ready Now = {ready_pct}%. Possible inflation."
    else:
        verdict = f"✅ PASS — Ready Now = {ready_pct}%. Distribution looks healthy."

    if noise_count < 50:
        notes = f"Noise only {noise_count}/60+ expected. Some noise leaking upward."
    else:
        notes = f"Noise capture = {noise_count}. Solid."

    print(f"  Verdict: {verdict}")
    print(f"  Notes:   {notes}")
    return {"counts": {"ready": ready_count, "eval": eval_count, "curious": curious_count, "noise": noise_count},
            "distribution": bd, "verdict": verdict, "notes": notes}


# ════════════════════════════════════════════════════════════════
#   STAGE 9 — DENSITY ATTACK
# ════════════════════════════════════════════════════════════════

def stage_9():
    divider("⚠️ STAGE 9", "Density Attack",
            "Keyword spam with no natural language. Should NOT score high.")

    r = post_reply("spammer@stress.com",
        "Scaling hiring SDR drowning switching retrain Apollo integration "
        "churn pricing budget timeline implementation competitor HubSpot "
        "pain bottleneck urgency demo onboarding seats migrate"
    )
    score = r["score"]

    if score >= 50:
        verdict = f"❌ FAIL — Keyword spam scores {score}. Engine treats it as genuine."
    elif score >= 30:
        verdict = f"⚠️ MILD CONCERN — Spam scores {score}. Some signal leakage."
    else:
        verdict = f"✅ PASS — Spam scores {score}. Engine resists keyword stuffing."

    return show(score, r["state"], r.get("breakdown", {}),
                r.get("explanation", []), verdict)


# ════════════════════════════════════════════════════════════════
#   STAGE 10 — EDGE INTENT FLIP
# ════════════════════════════════════════════════════════════════

def stage_10():
    divider("📉 STAGE 10", "Edge Intent Flip",
            "Hot thread → 5-day silence → polite follow-up. Does it degrade?")

    email = "intent-flip@stress.com"

    # Hot start (5 days ago)
    res1 = post_reply(email,
        "We're evaluating lead scoring tools. Currently on Apollo, not happy with it. "
        "How does your system integrate with Salesforce? What's pricing for 20 seats?",
        mins_ago=7200)
    print(f"  Hot start (5d ago):    score={res1['score']}, state={res1['state']}")

    # Small polite follow-up now (after 5 days of silence)
    res2 = post_reply(email,
        "Hi, just checking back in. Thanks for the info earlier.",
        mins_ago=0)
    print(f"  After 5d + polite:    score={res2['score']}, state={res2['state']}, momentum={res2.get('momentum')}")

    delta = res2["score"] - res1["score"]
    momentum = res2.get("momentum", "Unknown")

    if res2["score"] >= res1["score"] and momentum != "Cooling":
        verdict = f"📝 NO DECAY — Score held/grew ({res1['score']}→{res2['score']}). Expected: no time-decay exists yet."
        notes = "System has no time-decay logic. Silence doesn't degrade score."
    elif momentum == "Cooling":
        verdict = f"✅ GOOD — Momentum=Cooling. Score: {res1['score']}→{res2['score']}."
        notes = ""
    else:
        verdict = f"🤔 MIXED — Score delta={delta}, momentum={momentum}."
        notes = ""

    print(f"  Verdict: {verdict}")
    if notes:
        print(f"  Notes:   {notes}")
    return {"hot_score": res1["score"], "cold_score": res2["score"],
            "momentum": momentum, "verdict": verdict, "notes": notes}


# ════════════════════════════════════════════════════════════════
#   MAIN — RUN ALL STAGES
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  🔥 STRESS TEST PROTOCOL — 10 STAGES")
    print("  Rule: NO weight modifications. Observe only.")
    print("=" * 70)

    all_results = {}

    all_results["stage_1"] = stage_1()
    all_results["stage_2"] = stage_2()
    all_results["stage_3"] = stage_3()
    all_results["stage_4"] = stage_4()
    all_results["stage_5"] = stage_5()
    all_results["stage_6"] = stage_6()
    all_results["stage_7"] = stage_7()
    all_results["stage_8"] = stage_8()
    all_results["stage_9"] = stage_9()
    all_results["stage_10"] = stage_10()

    # ── Summary ──
    print("\n" + "=" * 70)
    print("  📋 STRESS TEST SUMMARY")
    print("=" * 70)

    stage_names = [
        ("stage_1",  "Signal Saturation"),
        ("stage_2",  "Polite Fluff Trap"),
        ("stage_3",  "Sarcasm & Negation"),
        ("stage_4",  "Multi-Turn Escalation"),
        ("stage_5",  "Fake Urgency Trap"),
        ("stage_6",  "Analytical Non-Buyer"),
        ("stage_7",  "Cold After Heat"),
        ("stage_8",  "Distribution Stress"),
        ("stage_9",  "Density Attack"),
        ("stage_10", "Edge Intent Flip"),
    ]

    pass_count = 0
    fail_count = 0
    concern_count = 0

    for key, name in stage_names:
        r = all_results[key]
        v = r.get("verdict", r.get("overall", ""))
        if v.startswith("✅"):
            pass_count += 1
            symbol = "✅"
        elif v.startswith("❌"):
            fail_count += 1
            symbol = "❌"
        else:
            concern_count += 1
            symbol = "⚠️"
        print(f"  {symbol} {name:25s} → {v[:80]}")

    print(f"\n  TOTAL: {pass_count} PASS | {concern_count} OBSERVATIONS | {fail_count} FAILURES")

    if fail_count == 0 and concern_count <= 2:
        print("  🎯 FOUNDATION IS STRONG")
    elif fail_count == 0:
        print("  ⚠️ FOUNDATION OK — Some edges to tighten")
    else:
        print(f"  🔴 {fail_count} CRITICAL FAILURES — Needs attention before production")

    print("=" * 70)
