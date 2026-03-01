"""
Stress Test: Classification Accuracy
Validates that the scoring engine correctly handles:
- Ultra-short dismissive replies (k, lol, ok, nah)
- Cold outreach rejections (wrong fit, don't do cold outreach)
- Genuine buyer signals still hit Ready Now
- Existing terminal patterns still work
- No regressions in Right ICP / Wrong Timing

Run: python stress_test_classification.py
"""

import sys
sys.path.insert(0, '.')
from reply_intelligence import decide_lead

PASS = 0
FAIL = 0
RESULTS = []

def check(name, text, expected_tier, expected_action=None):
    global PASS, FAIL
    result = decide_lead(text)
    tier = result["tier"]
    action = result["action"]
    score = result["priority_score"]

    ok_tier = tier == expected_tier
    ok_action = True
    if expected_action:
        ok_action = action == expected_action

    status = "✅" if (ok_tier and ok_action) else "❌"
    if ok_tier and ok_action:
        PASS += 1
    else:
        FAIL += 1

    RESULTS.append({
        "name": name, "status": status,
        "expected_tier": expected_tier, "got_tier": tier,
        "expected_action": expected_action, "got_action": action,
        "score": score
    })


print("=" * 70)
print("  STRESS TEST: CLASSIFICATION ACCURACY")
print("=" * 70)

# ==========================================
# SECTION 1: Ultra-short dismissive replies → Noise
# ==========================================
print("\n--- SECTION 1: Ultra-short dismissive replies → Noise ---")
check("Single 'k'",        "k",        "Noise", "do_not_respond")
check("Single 'lol'",      "lol",      "Noise", "do_not_respond")
check("Single 'ok'",       "ok",       "Noise", "do_not_respond")
check("Single 'no'",       "no",       "Noise", "do_not_respond")
check("Single 'nah'",      "nah",      "Noise", "do_not_respond")
check("Single 'nope'",     "nope",     "Noise", "do_not_respond")
check("Single 'haha'",     "haha",     "Noise", "do_not_respond")
check("Single 'hi'",       "hi",       "Noise", "do_not_respond")
check("Single '.'",        ".",        "Noise", "do_not_respond")
check("Two word nothing",  "sure thanks", "Noise", "do_not_respond")

# ==========================================
# SECTION 2: Cold outreach / wrong fit rejections → Noise
# ==========================================
print("\n--- SECTION 2: Cold outreach rejections → Noise ---")
check("Wrong fit explicit",
      "Wrong fit.",
      "Noise", "do_not_respond")
check("Don't do cold outreach",
      "We don't do cold outreach at all.",
      "Noise", "do_not_respond")
check("Not a fit",
      "Not a fit for us right now.",
      "Noise", "do_not_respond")
check("Pass on this",
      "We'll pass on this.",
      "Noise", "do_not_respond")
check("No need",
      "No need, we're covered.",
      "Noise", "do_not_respond")
check("Inbound only",
      "We do inbound only. Not relevant for us.",
      "Noise", "do_not_respond")

# ==========================================
# SECTION 3: Explicit noise patterns → Noise
# ==========================================
print("\n--- SECTION 3: Explicit noise patterns → Noise ---")
check("Not interested",     "Not interested.",       "Noise", "do_not_respond")
check("No thanks",          "No thanks.",            "Noise", "do_not_respond")
check("Remove me",          "Please remove me.",     "Noise", "do_not_respond")
check("Stop emailing",      "Stop emailing me.",     "Noise", "do_not_respond")
check("Out of office",      "Out of office until next week.", "Noise", "do_not_respond")
check("Unsubscribe",        "Unsubscribe.",          "Noise", "do_not_respond")
check("Not relevant",       "Not relevant to us.",   "Noise", "do_not_respond")
check("Lol no thanks",      "Lol no thanks.",        "Noise", "do_not_respond")
check("Not doing outbound", "We're not doing outbound.", "Noise", "do_not_respond")

# ==========================================
# SECTION 4: Disengagement → Deprioritize
# ==========================================
print("\n--- SECTION 4: Disengagement → Deprioritize ---")
check("Revisit next quarter",
      "Let's revisit next quarter, we have other priorities right now.",
      "Deprioritize", "do_not_respond")
check("Bad timing explicit",
      "Bad timing for us. We're focused on other things and have other priorities.",
      "Deprioritize", "do_not_respond")
check("Planning to start in Q3",
      "We're planning to start in Q3. Maybe when we scale.",
      "Deprioritize", "do_not_respond")
check("Small team deferral",
      "We're a small team of 5, maybe when we scale up.",
      "Deprioritize", "do_not_respond")

# ==========================================
# SECTION 5: Terminal ready patterns → Ready Now
# ==========================================
print("\n--- SECTION 5: Terminal ready signals → Ready Now ---")
check("Budget approved",
      "Budget approved, let's move forward.",
      "Ready Now", "respond_now")
check("Send the contract",
      "Please send the contract, we're ready.",
      "Ready Now", "respond_now")
check("Decision this week",
      "We need to make a decision this week.",
      "Ready Now", "respond_now")
check("Let's talk",
      "Let's talk, when are you available?",
      "Ready Now", "respond_now")
check("Lets talk",
      "Lets talk about pricing.",
      "Ready Now", "respond_now")
check("Looping in CTO",
      "Looping in our CTO to discuss integration.",
      "Ready Now", "respond_now")
check("Looping in Head of",
      "Looping in our Head of Sales for next steps.",
      "Ready Now", "respond_now")
check("Available this week",
      "I'm available this week for a call.",
      "Ready Now", "respond_now")
check("Thursday or Friday",
      "Can we do Thursday or Friday?",
      "Ready Now", "respond_now")
check("Founder decision",
      "I'm the founder and I make the decision.",
      "Ready Now", "respond_now")
check("Quick demo this week",
      "Can you do a quick demo this week?",
      "Ready Now", "respond_now")
check("I make the call",
      "I make the call on vendor decisions.",
      "Ready Now", "respond_now")
check("Finalize vendor",
      "We need to finalize vendor selection by Friday.",
      "Ready Now", "respond_now")
check("Lock this in",
      "Let's lock this in.",
      "Ready Now", "respond_now")
check("Forwarded to Head of Sales",
      "I forwarded this to our Head of Sales. Not my area.",
      "Ready Now", "respond_now")
check("Sent this to VP",
      "I sent this to our VP of Revenue, he handles these decisions.",
      "Ready Now", "respond_now")
check("Passed to CTO",
      "I passed this to our CTO, he'll take it from here.",
      "Ready Now", "respond_now")

# ==========================================
# SECTION 6: Genuine mid-intent → Right ICP / Wrong Timing
# ==========================================
print("\n--- SECTION 6: Mid-intent → Right ICP / Wrong Timing ---")
check("Pricing inquiry only",
      "What's your pricing? We're evaluating a few options but no rush.",
      "Right ICP / Wrong Timing", "respond_later")
check("Competitor mention with detail",
      "We're currently using Competitor X but looking at alternatives. What does your API integration look like?",
      "Right ICP / Wrong Timing", "respond_later")
check("Business pain + questions",
      "We're struggling with manual processes and it's causing bottlenecks. How does your solution handle onboarding?",
      "Right ICP / Wrong Timing")

# ==========================================
# SECTION 7: Edge cases / boundary tests
# ==========================================
print("\n--- SECTION 7: Edge cases ---")
check("Empty-ish reply",
      "   ",
      "Noise", "do_not_respond")
check("Just punctuation",
      "...",
      "Noise", "do_not_respond")
check("Emoji only",
      "👍",
      "Noise", "do_not_respond")
check("Short gibberish",
      "ha ha ha",
      "Noise", "do_not_respond")

# ==========================================
# SECTION 8: User-flagged CSV rows (must NOT be Noise)
# ==========================================
print("\n--- SECTION 8: User-flagged rows from CSV ---")
check("Row 21: Forwarded to decision-maker",
      "I forwarded this to our Head of Sales. Not my area.",
      "Ready Now", "respond_now")
check("Row 14: Uncertain but open",
      "Maybe. Not sure if this applies to us yet. We are a small team.",
      "Right ICP / Wrong Timing", "respond_later")
check("Row 6: Interested but mid-cycle",
      "We are mid budget cycle right now but this is genuinely interesting. Can you send details and follow up with me in 6 weeks?",
      "Right ICP / Wrong Timing", "respond_later")
check("Row 9: Evaluating with history",
      "We tried three tools like this in the past and none of them worked. What makes yours different? Also our budget cycle ends in Q3.",
      "Right ICP / Wrong Timing", "respond_later")
check("Interesting detailed question",
      "Interesting approach. How does it handle replies that are ambiguous like someone who says sounds good but gives no other context?",
      "Right ICP / Wrong Timing", "respond_later")
check("High volume pain + details request",
      "Interesting. We handle about 300 replies a week across 5 SDRs and honestly it's chaos during campaign spikes. Send me more details on how it works.",
      "Right ICP / Wrong Timing", "respond_later")

# ==========================================
# PRINT RESULTS
# ==========================================
print("\n" + "=" * 70)
print("  RESULTS")
print("=" * 70)

for r in RESULTS:
    tier_match = "✅" if r["expected_tier"] == r["got_tier"] else f"❌ (wanted {r['expected_tier']})"
    action_info = ""
    if r["expected_action"]:
        action_match = "✅" if r["expected_action"] == r["got_action"] else f"❌ (wanted {r['expected_action']})"
        action_info = f" | action={r['got_action']} {action_match}"

    print(f"  {r['status']} {r['name']:<35} tier={r['got_tier']:<25} {tier_match} | score={r['score']}{action_info}")

print(f"\n  TOTAL: {PASS} passed, {FAIL} failed out of {PASS + FAIL}")

if FAIL > 0:
    print("\n  ⚠️  FAILURES DETECTED — review before deploying")
    sys.exit(1)
else:
    print("\n  ✅ ALL TESTS PASSED — safe to deploy")
    sys.exit(0)
