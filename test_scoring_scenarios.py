"""
Verification: 6 scenarios + comparative + momentum
Tests the 8 corrections:
  1. Evaluative depth compounding
  2. Constraint-depth pairing (constraints alone ≠ Ready Now)
  3. Velocity capped
  4. Smooth gradients
  5. Momentum tracking
  6. Comparative explanation
  7. Engagement compounding
  8. Shallow penalty
"""
import time
from reply_intelligence import ReplyIntelligence

engine = ReplyIntelligence()
now = time.time()

def test(name, thread, expect_min, expect_max, expect_state, expect_momentum=None):
    result = engine.analyze_thread(thread)
    s = result['score']
    state = result['state']
    expl = result['explanation']
    bd = result['score_breakdown']
    mom = result['momentum']

    print(f"\n{'='*65}")
    print(f"  {name}")
    print(f"{'='*65}")
    print(f"  Score:      {s}/100  (expect {expect_min}-{expect_max})")
    print(f"  State:      {state}  (expect {expect_state})")
    print(f"  Momentum:   {mom}")
    print(f"  Explanation: {expl}")
    print(f"  Breakdown:  {bd}")

    assert expect_min <= s <= expect_max, f"FAIL: score {s} not in [{expect_min},{expect_max}]"
    assert state == expect_state, f"FAIL: state '{state}' != '{expect_state}'"
    if expect_momentum:
        assert mom == expect_momentum, f"FAIL: momentum '{mom}' != '{expect_momentum}'"
    print(f"  ✅ PASS")
    return result

# ─────────────────────────────────────────────────
# SCENARIO 1: Polite reply
# ─────────────────────────────────────────────────
test("1. Polite Reply ('thanks, will check')",
    [{"body": "Thanks, will check and get back.", "timestamp": now, "sender": "lead"}],
    0, 15, "Noise")

# ─────────────────────────────────────────────────
# SCENARIO 2: Shallow fast reply (Flaw 8: penalty)
# ─────────────────────────────────────────────────
test("2. Shallow Fast Reply ('sounds good' in 1 min)",
    [
        {"body": "Hi there", "timestamp": now - 120, "sender": "agent"},
        {"body": "Sounds good", "timestamp": now - 60, "sender": "lead"}
    ],
    0, 20, "Noise")

# ─────────────────────────────────────────────────
# SCENARIO 3: Pricing only (should NOT exceed 60)
# ─────────────────────────────────────────────────
test("3. Pricing Only (2 replies)",
    [
        {"body": "How much does it cost?", "timestamp": now - 3600, "sender": "lead"},
        {"body": "Here is pricing.", "timestamp": now - 1800, "sender": "agent"},
        {"body": "Thanks, what are the different pricing tiers?", "timestamp": now, "sender": "lead"}
    ],
    26, 55, "Curious")

# ─────────────────────────────────────────────────
# SCENARIO 4: Budget + Timeline WITHOUT depth
#    Flaw 2: constraints alone = weak
#    1 reply = Deprioritize (constraints get depth_mult=0.3)
# ─────────────────────────────────────────────────
test("4. Budget + Timeline (no depth, 1 reply) → STAYS LOW",
    [{"body": "We have budget approved and need this soon.", "timestamp": now, "sender": "lead"}],
    0, 25, "Curious")

# ─────────────────────────────────────────────────
# SCENARIO 5: Budget + Timeline WITH depth (3 replies)
# ─────────────────────────────────────────────────
test("5. Budget + Timeline + Depth (3 replies)",
    [
        {"body": "We have budget approved for this quarter.", "timestamp": now - 7200, "sender": "lead"},
        {"body": "Great, let me send details.", "timestamp": now - 3600, "sender": "agent"},
        {"body": "When can we launch? What are the next steps?", "timestamp": now - 1800, "sender": "lead"},
        {"body": "Here is the plan.", "timestamp": now - 900, "sender": "agent"},
        {"body": "Perfect. Our team needs this by end of month. Can you walk us through it?", "timestamp": now, "sender": "lead"}
    ],
    61, 85, "Ready Now")

# ─────────────────────────────────────────────────
# SCENARIO 6: Full constraint + implementation + competitor
# ─────────────────────────────────────────────────
r6 = test("6. Full Constraint + Implementation + Competitor",
    [
        {"body": "We have the budget approved and need to launch ASAP.", "timestamp": now - 7200, "sender": "lead"},
        {"body": "Here are our options.", "timestamp": now - 5400, "sender": "agent"},
        {"body": "What is the pricing? We are comparing you vs another vendor. Can your API integrate?", "timestamp": now - 3600, "sender": "lead"},
        {"body": "Yes, here is our API docs.", "timestamp": now - 1800, "sender": "agent"},
        {"body": "Our team lead approved. How do we set up the config and deploy? What does the migration look like?", "timestamp": now, "sender": "lead"}
    ],
    85, 100, "Ready Now")

# Verify competitor + implementation appear in explanation
expl_text = " ".join(r6['explanation']).lower()
assert "competitor" in expl_text, f"FAIL: 'competitor' not in explanation: {r6['explanation']}"
assert "implementation" in expl_text, f"FAIL: 'implementation' not in explanation: {r6['explanation']}"
print(f"  ✅ Competitor + Implementation surfaced in explanation")

# ─────────────────────────────────────────────────
# FLAW 5: MOMENTUM TEST
# ─────────────────────────────────────────────────
print(f"\n{'='*65}")
print(f"  MOMENTUM TEST")
print(f"{'='*65}")

# Rising: first half weak, second half strong
rising = engine.analyze_thread([
    {"body": "ok", "timestamp": now - 7200, "sender": "lead"},
    {"body": "sure", "timestamp": now - 5400, "sender": "lead"},
    {"body": "Actually, what is the pricing? Can your API integrate with our system?", "timestamp": now - 1800, "sender": "lead"},
    {"body": "We have budget approved. Comparing you vs competitors.", "timestamp": now, "sender": "lead"}
])
assert rising['momentum'] == "Rising", f"FAIL: Expected Rising, got {rising['momentum']}"
print(f"  Rising momentum: ✅ ({rising['momentum']})")

# Cooling: first half strong, second half weak
cooling = engine.analyze_thread([
    {"body": "We need to integrate ASAP. Budget is approved. What is the pricing?", "timestamp": now - 7200, "sender": "lead"},
    {"body": "Can your API work with our system? We are comparing vendors.", "timestamp": now - 5400, "sender": "lead"},
    {"body": "ok", "timestamp": now - 1800, "sender": "lead"},
    {"body": "will get back", "timestamp": now, "sender": "lead"}
])
assert cooling['momentum'] == "Cooling", f"FAIL: Expected Cooling, got {cooling['momentum']}"
print(f"  Cooling momentum: ✅ ({cooling['momentum']})")

# ─────────────────────────────────────────────────
# FLAW 6: COMPARATIVE EXPLANATION
# ─────────────────────────────────────────────────
print(f"\n{'='*65}")
print(f"  COMPARATIVE EXPLANATION TEST")
print(f"{'='*65}")

lead_a = engine.analyze_thread([
    {"body": "Budget approved. Need to launch ASAP.", "timestamp": now - 7200, "sender": "lead"},
    {"body": "What is the pricing? Can your API integrate?", "timestamp": now - 3600, "sender": "lead"},
    {"body": "We are comparing competitors.", "timestamp": now, "sender": "lead"}
])
lead_b = engine.analyze_thread([
    {"body": "We have budget.", "timestamp": now - 7200, "sender": "lead"},
    {"body": "When can we start?", "timestamp": now, "sender": "lead"}
])

comparisons = engine.compare_leads([
    {"email": "leadA@test.com", "score": lead_a['score'], "signals": lead_a['signals'], "metrics": lead_a['metrics']},
    {"email": "leadB@test.com", "score": lead_b['score'], "signals": lead_b['signals'], "metrics": lead_b['metrics']}
])

for c in comparisons:
    print(f"  {c['reason']}")

assert len(comparisons) >= 1, "FAIL: No comparisons generated"
assert "leadA@test.com" in comparisons[0]['reason'], "FAIL: Lead A should outrank Lead B"
print(f"  ✅ Comparative layer working")

# ─────────────────────────────────────────────────
print(f"\n{'='*65}")
print(f"  ALL 6 SCENARIOS + MOMENTUM + COMPARATIVE PASSED ✅")
print(f"{'='*65}")
