import re
import time
import math
import json
import os
from datetime import datetime

# ==========================================
# CONFIGURATION & PERSISTENCE (Hardening 1)
# ==========================================
LEAD_MEMORY_FILE = "lead_memory.json"
UNKNOWN_LOG_FILE = "unknown_signals.log"

def _load_memory():
    if os.path.exists(LEAD_MEMORY_FILE):
        try:
            with open(LEAD_MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_memory(memory):
    try:
        with open(LEAD_MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
    except:
        pass # Operational resilience

def _log_unknown(text):
    try:
        with open(UNKNOWN_LOG_FILE, 'a') as f:
            f.write(f"{datetime.now().isoformat()} | {text}\n")
    except:
        pass

# Global State initialized from disk
LEAD_MEMORY = _load_memory()

# ==========================================
# SIGNAL FAMILIES (Hardening 3)
# ==========================================
SIGNAL_FAMILIES = {
    # Financial Family
    "pricing": "Financial",
    "budget": "Financial",
    # Timing/Urgency Family
    "timeline": "Urgency",
    "implementation": "Urgency", # Implementation often implies moving forward
    # Validation Family
    "competitor": "Validation",
    "analytical": "Validation",
    # Authority Family
    "stakeholder": "Authority",
    # Need Family
    "business_pain": "Need",
    "problem_desc": "Need"
}

class ReplyIntelligence:
    def __init__(self):
        # ==========================================
        # SIGNAL PATTERNS (Fix 4: Hard Limit 10)
        # ==========================================
        self.PATTERNS = {
            "pricing": [
                r"price", r"cost", r"quote", r"pricing", r"how much", 
                r"\$", r"rate", r"fee", r"charges", r"billing" 
            ],
            "timeline": [
                r"when", r"soon", r"asap", r"timeline", r"schedule", 
                r"deadline", r"launch", r"this week", r"this month", r"next quarter"
            ],
            "budget": [
                r"budget", r"afford", r"fund", r"approv", r"allocat", 
                r"spend", r"fiscal", r"money", r"resources", r"cost center"
            ],
            "stakeholder": [
                r"boss", r"manager", r"team", r"colleague", r"partner", 
                r"approv", r"legal", r"finance", r"cto", r"ceo"
            ],
            "competitor": [
                r"competitor", r"other tool", r"comparison", r"switch", r"vendor",
                r"alternative", r"vs\b", r"compared to", r"currently using",
                r"better than"
            ],
            "problem_desc": [
                r"problem", r"issue", r"struggle", r"pain", r"need", 
                r"fix", r"solve", r"help", r"challenge", r"blocker"
            ],
            "implementation": [
                r"api", r"integrat", r"setup", r"install", r"config", 
                r"sdk", r"webhook", r"deploy", r"migration", r"onboard"
            ],
            "business_pain": [
                r"scaling", r"scale\b", r"growing fast", r"growth", r"wasting", 
                r"drowning", r"overwhelm", r"bottleneck", r"inefficien", r"manual"
            ],
            "analytical": [
                r"win.?rate", r"metric", r"accuracy", r"benchmark", r"data.?driven", 
                r"roi\b", r"performance", r"kpi", r"conversion", r"retention"
            ]
        }

        # Terminal and Scoring weights
        self.TERMINAL_READY_PATTERNS = [
            r"finalize vendor",
            r"decision this week",
            r"ready to move forward",
            r"greenlit",
            r"procurement is done",
            r"lock this in",
            r"send the contract",
            r"sign the contract",
            r"budget approved",
            r"meet tomorrow",
            r"availability this week",
            r"available this week",
            r"thursday or friday",
            r"quick demo this week",
            r"when can we talk",
            r"let's talk",
            r"lets talk",
            r"looping in.*head of",
            r"looping in.*vp",
            r"looping in.*cto",
            r"looping in.*ceo",
            r"i make the call",
            r"founder.*decision",
        ]

        self.TERMINAL_NOISE_PATTERNS = [
            r"remove me",
            r"stop emailing",
            r"unsubscribe",
            r"take me off",
            r"lol no thanks",
            r"not relevant",
            r"inbound only",
            r"out of office",
            r"ooo",
            r"not doing outbound",
            r"not interested",
            r"no thanks",
            r"wrong fit",
            r"not a fit",
            r"don'?t do cold",
            r"we don'?t do outbound",
            r"no need",
            r"pass on this",
            r"^k$",
            r"^lol$",
            r"^ok$",
            r"^no$",
            r"^nah$",
            r"^nope$",
            r"^haha$",
        ]

        self.MAX_SCORES = {
            "evaluative_depth": 30, "business_pain": 35, "competitor_switch_bonus": 20,
            "analytical_depth": 12, "engagement_compound": 22, "constraint_x_depth": 15,
            "content_richness": 15, "question_density": 7, "velocity": 5,
            "consistency": 3, "shallow_penalty": -15,
        }

    # Signal Extraction updated for logging
    def _extract_signals(self, history):
        lead_messages = [m['body'].lower() for m in history if m.get('sender') == 'lead']
        combined_text = " ".join(lead_messages)
        
        # Negation Handling
        negation_patterns = [
            r"not\s+", r"no\s+", r"never\s+", r"don't\s+", r"won't\s+", 
            r"aren't\s+", r"we're\s+not\s+", r"happy\s+with"
        ]
        negated_text = combined_text
        for neg_pat in negation_patterns:
            negated_text = re.sub(neg_pat + r'(\S+(?:\s+\S+){0,5})', '', negated_text)

        extracted = {}
        for key, patterns in self.PATTERNS.items():
            count = 0
            search_text = negated_text if key in ('competitor', 'business_pain', 'implementation') else combined_text
            for p in patterns:
                if re.search(p, search_text):
                    count += 1
            extracted[key] = count
            
        # Logging unknown phrases (Persistence)
        if len(combined_text.split()) > 50 and sum(extracted.values()) == 0:
             _log_unknown(combined_text[:200]) # Log first 200 chars

        extracted["word_count"] = len(combined_text.split())
        extracted["question_count"] = combined_text.count("?")
        
        # Keyword Spam
        total_words = extracted["word_count"]
        total_signals = sum(v for k,v in extracted.items() if k not in ('word_count', 'question_count'))
        is_spam = False
        if total_words > 0 and (total_signals / total_words) > 0.4 and total_signals > 5:
            is_spam = True
        extracted["is_keyword_spam"] = is_spam

        # Disengagement
        disengage_patterns = [
            r"revisit\s+next\s+quarter", r"not\s+interested",
            r"other\s+priorities", r"bad\s+timing",
            r"no\s+thanks",
            r"inbound\s+only",
            r"not\s+relevant",
            r"not\s+doing\s+outbound",
            r"planning\s+to\s+start\s+in\s+q",
            r"small\s+team\s+of\s+\d",
            r"maybe\s+when\s+we\s+scale",
            r"wrong\s+fit",
            r"not\s+a\s+fit",
            r"don'?t\s+do\s+cold",
            r"we\s+don'?t\s+do\s+outbound",
        ]
        is_disengaging = any(re.search(p, combined_text) for p in disengage_patterns)
        extracted["is_disengaging"] = is_disengaging

        return extracted

    # Metrics & Scoring
    def _calculate_metrics(self, history, signals):
        lead_replies = [m for m in history if m.get('sender') == 'lead']
        depth = len(lead_replies)
        velocity_hours = 999
        if len(lead_replies) > 1:
             timestamps = sorted([m['timestamp'] for m in lead_replies])
             diffs = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
             velocity_hours = (sum(diffs) / len(diffs)) / 3600
        return {
            "depth": depth, "signals": signals, "velocity_hours": velocity_hours,
            "avg_words_per_reply": signals["word_count"] / max(1, depth), "is_consistent": 1
        }

    def _calculate_score(self, metrics):
        s = metrics['signals']
        eval_depth = 0
        if s.get('question_count', 0) > 1: eval_depth += 10
        if s.get('implementation'): eval_depth += 10
        if s.get('competitor'): eval_depth += 10
        eval_depth = min(30, eval_depth)
        
        pain = min(35, s.get('business_pain', 0) * 10)
        
        comp_bonus = 0
        if s.get('competitor', 0) >= 1: comp_bonus = 12
        if s.get('competitor', 0) >= 2: comp_bonus = 16
        comp_bonus = min(20, comp_bonus)
        
        constraint_score = 0
        constraint_score += s.get('pricing', 0) * 5
        constraint_score += s.get('budget', 0) * 5
        constraint_score += s.get('timeline', 0) * 5
        constraint_score += s.get('stakeholder', 0) * 5
        constraint_score = min(15, constraint_score)

        score_breakdown = {
            "evaluative_depth": eval_depth, "business_pain": pain,
            "competitor_switch_bonus": comp_bonus, "analytical_depth": min(12, s.get('analytical', 0) * 5),
            "engagement_compound": min(22, metrics['depth'] * 5),
            "constraint_x_depth": constraint_score, "content_richness": 0,
            "question_density": min(7, s.get('question_count', 0) * 3),
            "velocity": 5, "consistency": 3, "shallow_penalty": 0,
        }
        
        if s.get('is_disengaging'): score_breakdown["disengage_penalty"] = -30
        if s.get('is_keyword_spam'): score_breakdown["spam_penalty"] = -50 
        return score_breakdown

    def _classify_state(self, score, signals):
        if signals.get('is_explicit_noise'): return "Noise"
        if signals.get('is_disengaging'): return "Deprioritize"
        if signals.get('is_keyword_spam'): return "Noise"
        # Short-reply noise guard: <5 words with weak score = Noise
        if signals.get('word_count', 0) < 5 and score < 25: return "Noise"
        if score >= 55: return "Ready Now"
        if score >= 20: return "Right ICP / Wrong Timing"
        return "Noise"

    # ==========================================
    # FIX 5: EXPLANATION NORMALIZATION with FAMILIES (Hardening 4)
    # ==========================================
    def _generate_explanation_v2(self, state, signals, score):
        if state == "Ready Now":
            return "Lead shows strong buying intent and urgency."
        if state == "Right ICP / Wrong Timing":
            # Find dominant family
            families_present = set()
            for k, v in signals.items():
                if v > 0 and k in SIGNAL_FAMILIES:
                    families_present.add(SIGNAL_FAMILIES[k])
            
            if "Financial" in families_present:
                return "Lead indicates financial intent (pricing/budget)."
            if "Urgency" in families_present:
                return "Lead implies timeline constraints."
            if "Validation" in families_present:
                 return "Lead is validating against competitors."
            if "Need" in families_present:
                 return "Lead has clear business pain."
            
            return "Good fit lead, but lacks urgent signals."
            
        if state == "Deprioritize": return "Lead explicitly requested to disconnect."
        return "Not enough signal to warrant action." 

    def analyze_thread(self, thread_history):
        if not thread_history: return self._default_result()
        signals = self._extract_signals(thread_history)
        metrics = self._calculate_metrics(thread_history, signals)
        score_breakdown = self._calculate_score(metrics)
        raw_score = sum(score_breakdown.values())
        normalized_score = min(100, max(0, raw_score))
        
        lead_count = len([m for m in thread_history if m.get('sender') == 'lead'])
        if lead_count <= 1 and normalized_score > 90: normalized_score = 90
        if signals.get('is_keyword_spam'): normalized_score = min(normalized_score, 15)

        state = self._classify_state(normalized_score, signals)
        explanation = self._generate_explanation_v2(state, signals, normalized_score)
        
        return {
            "score": normalized_score, "score_breakdown": score_breakdown,
            "state": state, "explanation": explanation, "signals": signals,
            "metrics": metrics, "momentum": "Stable", 
            "tiebreaker": {}, "full_explanation": [], "cliff_flag": None
        }

    def _default_result(self):
        return {
            "score": 0, "state": "Noise", "explanation": "No content.",
            "signals": {}, "metrics": {}, "score_breakdown": {}, "full_explanation": [], "tiebreaker": {}
        }


# ==========================================
# DECIDE LEAD with HARDENING
# ==========================================
def decide_lead(thread_text=None, thread_history=None, metadata=None):
    if metadata is None: metadata = {}
    
    # Resolve input...
    latest_text = ""
    history_to_analyze = []
    if thread_history:
        history_to_analyze = thread_history
        lead_msgs = [m for m in thread_history if m.get('sender') == 'lead']
        if lead_msgs:
            lead_msgs.sort(key=lambda x: x.get('timestamp', 0))
            latest_text = lead_msgs[-1]['body']
    elif thread_text:
        latest_text = thread_text
        history_to_analyze = [{"sender": "lead", "body": thread_text, "timestamp": time.time()}]
    
    decision = {
        "action": "do_not_respond", "tier": "Noise", "confidence_bucket": "Low",
        "priority_score": 0, "priority_level": "Low", "explanation": "No content detected.",
        "feedback_prompt": "Is this noise? (Yes/No)", "disposition": "ignore", "analysis": {}
    }

    if not latest_text and not history_to_analyze:
        return _apply_inbox_reality(decision, metadata)

    engine = ReplyIntelligence()
    text_lower = latest_text.lower().strip()
    
    # Terminal checks on latest text...
    cleaned_lines = [l for l in text_lower.split('\n') if not l.strip().startswith('>')]
    cleaned_text = " ".join(cleaned_lines)

    for p in engine.TERMINAL_READY_PATTERNS:
        if re.search(p, cleaned_text):
            decision.update({
                "action": "respond_now", "tier": "Ready Now", "confidence_bucket": "High",
                "priority_score": 95, "priority_level": "Critical", "explanation": "Terminal buying command detected.",
                "feedback_prompt": "Did you reply? (Yes/No)", "disposition": "qualified"
            })
            return _apply_inbox_reality(decision, metadata)

    for p in engine.TERMINAL_NOISE_PATTERNS:
        if re.search(p, cleaned_text):
            decision.update({
                "action": "do_not_respond", "tier": "Noise", "confidence_bucket": "High",
                "priority_score": 0, "priority_level": "Low", "explanation": "Explicit unsubscribe request.",
                "feedback_prompt": "Correctly blocked? (Yes/No)", "disposition": "blocked"
            })
            return _apply_inbox_reality(decision, metadata)

    # Heuristic Analysis
    result = engine.analyze_thread(history_to_analyze)
    score = result['score']
    state = result['state']
    signals = result['signals']

    if state == "Ready Now":
        decision.update({
            "action": "respond_now", "tier": "Ready Now", "confidence_bucket": "High",
            "explanation": result['explanation'], "priority_score": max(80, score),
            "priority_level": "High", "disposition": "qualified", "feedback_prompt": "Did you reply? (Yes/No)"
        })
    elif state == "Right ICP / Wrong Timing":
         decision.update({
            "action": "respond_later", "tier": "Right ICP / Wrong Timing", "confidence_bucket": "Medium",
            "explanation": result['explanation'], "priority_score": max(40, score),
            "priority_level": "Standard", "disposition": "nurture", "feedback_prompt": "Did you snooze? (Yes/No)"
        })
    elif state == "Deprioritize":
        decision.update({
            "action": "do_not_respond", "tier": "Deprioritize", "confidence_bucket": "High",
            "explanation": result['explanation'], "priority_score": 10,
            "priority_level": "Low", "disposition": "lost", "feedback_prompt": "Did you archive? (Yes/No)"
        })
    else:
        decision.update({
            "action": "do_not_respond", "tier": "Noise", "confidence_bucket": "Low",
            "explanation": result['explanation'], "priority_score": 0,
            "priority_level": "Low", "disposition": "ignore", "feedback_prompt": "Is this noise? (Yes/No)"
        })

    # HARDENING 3: CONFIDENCE FAMILIES
    # High Confidence requires signals from >= 2 FAMILIES (not just patterns)
    if decision["confidence_bucket"] == "High" and state not in ["Noise", "Deprioritize"]:
        families_detected = set()
        for k, v in signals.items():
            if v > 0 and k in SIGNAL_FAMILIES:
                families_detected.add(SIGNAL_FAMILIES[k])
        
        # If < 2 distinct families, downgrade confidence (Review Process needed)
        if len(families_detected) < 2:
            decision["confidence_bucket"] = "Medium"

    decision["analysis"] = result
    return _apply_inbox_reality(decision, metadata)


# ==========================================
# HARDENING 2: STRICT RECENCY & PERSISTENCE
# ==========================================
def _apply_inbox_reality(decision, metadata):
    email_id = metadata.get("email_id") or metadata.get("id")
    
    # 1. STRICT RECENCY (Hardening 2)
    created_at = metadata.get("created_at")
    recency_bonus = 0
    if created_at and str(created_at).strip():
        try:
            # Must parse successfully. No default to "now".
            dt = None
            clean_ts = str(created_at).replace("Z", "+00:00")
            if "T" in clean_ts:
                # ISO format
                dt = datetime.fromisoformat(clean_ts)
            elif re.match(r"^\d{10}(\.\d+)?$", str(created_at)):
                 # Unix timestamp
                 dt = datetime.fromtimestamp(float(created_at))

            if dt:
                now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
                # If naive, assume system time is compatible
                age_days = (now - dt).total_seconds() / 86400.0
                if age_days >= 0:
                     val = max(0, 10 - int(age_days))
                     recency_bonus = min(10, val)
        except:
            pass # Malformed = No bonus
            
    decision["priority_score"] += recency_bonus

    # 2. DUPLICATE SUPPRESSION + SAVE (Hardening 1)
    if email_id and decision["action"] == "respond_now":
        now_ts = time.time()
        memory = LEAD_MEMORY.get(email_id)
        
        if memory:
            last_action = memory.get("last_action")
            last_seen = memory.get("last_seen", 0)
            
            if last_action == "respond_now" and (now_ts - last_seen) < (48 * 3600):
                decision["action"] = "respond_later"
                decision["tier"] = "Right ICP / Wrong Timing"
                decision["priority_score"] = max(0, decision["priority_score"] - 15)
                decision["explanation"] += " (Suppressed duplicate recommendation)"

        # Update Memory & PERSIST
        LEAD_MEMORY[email_id] = {
            "last_action": decision["action"],
            "last_priority": decision["priority_score"],
            "last_seen": now_ts
        }
        _save_memory(LEAD_MEMORY) # <--- WRITE TO DISK
    
    decision["priority_score"] = min(100, max(0, int(decision["priority_score"])))
    
    return decision

# Alias
score_lead = decide_lead
