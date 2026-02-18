"""
V3 Chaos Regression Test
========================
Tests all 5 failure scenarios + 4 noise scenarios.

Pass criteria (from user directive V3):
  painonly   >= 45
  budgetpain >= 60
  churnrisk  >= 60
  analytical >= 35
  escalation >= 65

Noise control (must stay low):
  fakeurgent <= 20
  cheap      <= 10
  longpolite <= 10
  mixed      <= 20
"""
import time
from reply_intelligence import ReplyIntelligence

engine = ReplyIntelligence()
now = time.time()

PASS = 0
FAIL = 0

def test(name, thread, expect_min, expect_max, label=""):
    global PASS, FAIL
    result = engine.analyze_thread(thread)
    s = result['score']
    state = result['state']
    bd = result['score_breakdown']
    expl = result['explanation']

    ok = expect_min <= s <= expect_max
    icon = "✅" if ok else "❌"

    print(f"\n{'='*65}")
    print(f"  {icon} {name}")
    print(f"{'='*65}")
    print(f"  Score:     {s}/100  (expect {expect_min}–{expect_max})")
    print(f"  State:     {state}")
    print(f"  Explain:   {expl}")
    print(f"  Breakdown: {bd}")
    if label:
        print(f"  Label:     {label}")

    if ok:
        PASS += 1
        print(f"  ✅ PASS")
    else:
        FAIL += 1
        print(f"  ❌ FAIL: score {s} not in [{expect_min},{expect_max}]")

    return result


# ═══════════════════════════════════════════════════
# HIGH-INTENT SCENARIOS (must score HIGH)
# ═══════════════════════════════════════════════════

# ── 1. PAINONLY ──────────────────────────────────
# 20k emails + bottleneck + reps wasting hours
# No questions. Pure operational pain.
# Target: 45–55
test("painonly — 20k emails, bottleneck, reps wasting hours",
    [{
        "body": (
            "We're sending 20k emails a month and the bottleneck is killing us. "
            "Our reps are wasting hours manually sorting through replies. "
            "We're drowning in volume and losing deals because of inefficiency. "
            "This is a critical scaling problem for our team."
        ),
        "timestamp": now,
        "sender": "lead"
    }],
    45, 70, "Business pain without question must hit 45–55")

# ── 2. BUDGETPAIN ───────────────────────────────
# Budget approved + operational pain + "How does it actually work?"
# Target: 60+
test("budgetpain — budget approved, operational pain, 'how does it work?'",
    [{
        "body": (
            "We have budget approved for a tool like this. Our team is overwhelmed "
            "with manual work and wasting time on low-quality leads. "
            "How does it actually work? Can you walk me through the setup?"
        ),
        "timestamp": now,
        "sender": "lead"
    }],
    60, 100, "Budget + pain + question = real buyer")

# ── 3. CHURNRISK ────────────────────────────────
# Switching from Apollo + competitor dissatisfaction + "What makes yours better?"
# Target: 60+
test("churnrisk — switching from Apollo, competitor dissatisfaction",
    [{
        "body": (
            "We're currently using Apollo but we're not happy with the results. "
            "Considering switching to a better vendor. What makes your tool different? "
            "We need something that actually delivers on accuracy."
        ),
        "timestamp": now,
        "sender": "lead"
    }],
    60, 100, "Active vendor evaluation = 60+ minimum")

# ── 4. ANALYTICAL ───────────────────────────────
# Win-rate delta + signal stabilization
# Data-driven buyer. No explicit pain language.
# Target: 35+
test("analytical — win-rate delta, signal stabilization",
    [{
        "body": (
            "What's the improvement in win-rate delta after your signals stabilize? "
            "How do you measure accuracy and what benchmarks do you use? "
            "I want to see the data on false positive rates before we commit."
        ),
        "timestamp": now,
        "sender": "lead"
    }],
    35, 80, "Data-driven buyer must score on complexity")

# ── 5. ESCALATION ───────────────────────────────
# 3 replies + competitor + implementation + integration
# Target: 65+
test("escalation — 3 replies, competitor, implementation, integration",
    [
        {
            "body": "We're evaluating your tool against two other vendors.",
            "timestamp": now - 7200,
            "sender": "lead"
        },
        {
            "body": "Here's our comparison doc.",
            "timestamp": now - 5400,
            "sender": "agent"
        },
        {
            "body": "Can your API integrate with our Salesforce instance? How does the webhook work?",
            "timestamp": now - 3600,
            "sender": "lead"
        },
        {
            "body": "Yes, here is our integration guide.",
            "timestamp": now - 1800,
            "sender": "agent"
        },
        {
            "body": (
                "Great. We need to deploy this by end of month. "
                "What does the migration look like? Can we connect to our existing pipeline? "
                "We're switching from our current vendor because of accuracy issues."
            ),
            "timestamp": now,
            "sender": "lead"
        }
    ],
    65, 100, "3 replies + competitor + implementation = buying motion")


# ═══════════════════════════════════════════════════
# NOISE SCENARIOS (must stay LOW)
# ═══════════════════════════════════════════════════

# ── 6. FAKEURGENT ────────────────────────────────
# Fake urgency, no substance
test("fakeurgent — vague urgency, no substance",
    [{
        "body": "This is urgent please respond asap!!!!",
        "timestamp": now,
        "sender": "lead"
    }],
    0, 20, "Fake urgency = noise")

# ── 7. CHEAP ─────────────────────────────────────
# One-word tire kicker
test("cheap — one-word, no content",
    [{
        "body": "ok",
        "timestamp": now,
        "sender": "lead"
    }],
    0, 10, "One-word = noise")

# ── 8. LONGPOLITE ────────────────────────────────
# Polite but zero signals
test("longpolite — polite, no buying signals",
    [{
        "body": "Thanks so much for reaching out! We'll take a look and circle back if needed.",
        "timestamp": now,
        "sender": "lead"
    }],
    0, 10, "Polite = noise")

# ── 9. MIXED ─────────────────────────────────────
# Multiple shallow replies, no substance
test("mixed — multiple shallow replies",
    [
        {"body": "Hey", "timestamp": now - 7200, "sender": "lead"},
        {"body": "Info sent.", "timestamp": now - 5400, "sender": "agent"},
        {"body": "cool", "timestamp": now - 3600, "sender": "lead"},
        {"body": "Follow up.", "timestamp": now - 1800, "sender": "agent"},
        {"body": "yeah sure", "timestamp": now, "sender": "lead"}
    ],
    0, 20, "Shallow multi-turn = noise")


# ═══════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════
print(f"\n{'='*65}")
print(f"  V3 CHAOS REGRESSION RESULTS")
print(f"{'='*65}")
print(f"  Passed: {PASS}/{PASS+FAIL}")
print(f"  Failed: {FAIL}/{PASS+FAIL}")
if FAIL == 0:
    print(f"  🎯 ALL TESTS PASSED — Engine is buyer-calibrated")
else:
    print(f"  ⚠️  {FAIL} FAILURES — Engine needs further tuning")
print(f"{'='*65}")
