import re
import time
import math

class ReplyIntelligence:
    def __init__(self):
        # ==========================================
        # SIGNAL PATTERNS
        # ==========================================
        self.PATTERNS = {
            "pricing": [r"price", r"cost", r"quote", r"pricing", r"how much", r"\$", r"rate"],
            "timeline": [r"when", r"soon", r"asap", r"timeline", r"schedule", r"deadline",
                        r"launch", r"this week", r"this month", r"next quarter", r"next month"],
            "budget": [r"budget", r"afford", r"fund", r"approv", r"allocat", r"spend"],
            "stakeholder": [r"boss", r"manager", r"team", r"colleague", r"partner", r"approv",
                          r"legal", r"finance", r"cto", r"ceo", r"vp"],
            "competitor": [r"competitor", r"other tool", r"comparison", r"switch", r"vendor",
                         r"alternative", r"vs\b", r"compared to", r"currently using",
                         r"switched from", r"moving from", r"replacing", r"instead of",
                         r"using .+ for", r"considering leaving", r"currently use .+ but",
                         r"leaving .+ for", r"better than", r"what makes .+ different",
                         r"evaluat(?:ing|e|ion)\s+(?:.{0,20}\s+)?(?:vendors?|platforms?|solutions?|options?)",
                         r"looking\s+at\s+(?:.{0,20}\s+)?(?:vendors?|platforms?|solutions?|options?)",
                         r"compar(?:e|ing)\s+(?:.{0,20}\s+)?(?:vendors?|platforms?|solutions?|options?)"],
            "problem_desc": [r"problem", r"issue", r"struggle", r"pain", r"need", r"fix",
                           r"solve", r"help", r"challenge", r"blocker"],
            "implementation": [r"api", r"integrat", r"setup", r"install", r"config", r"sdk",
                             r"webhook", r"deploy", r"migration", r"onboard", r"plug",
                             r"retrain", r"sequence", r"automat", r"workflow", r"pipeline",
                             r"connect", r"move\s+forward", r"proceed", r"next\s+steps"],
            "business_pain": [r"scaling", r"scale\b", r"growing fast", r"growth",
                            r"wasting", r"waste", r"drowning", r"overwhelm", r"overload",
                            r"bottleneck", r"inefficien", r"manual",
                            r"hiring", r"recruit", r"new reps", r"new team", r"sdrs?\b",
                            r"churn", r"losing", r"retention",
                            r"valuable", r"game.?changer", r"critical",
                            r"replac", r"behind", r"burning"],
            "analytical": [r"win.?rate", r"delta", r"metric", r"accuracy", r"benchmark",
                         r"data.?driven", r"signal", r"stabiliz", r"roi\b", r"performance",
                         r"measur", r"kpi", r"conversion", r"retention.?rate",
                         r"false.?positive", r"false.?negative", r"precision", r"recall",
                         r"improvement", r"uplift", r"variance", r"sample.?size"]
        }

        # ==========================================
        # SCORING WEIGHTS (V2 — Behavioral Intent)
        # ==========================================
        # Primary principle:
        #   effort + specificity + operational framing = buying motion.
        #   Activity alone is noise.
        #
        # Total positive max ≈ 100
        self.MAX_SCORES = {
            "evaluative_depth":         30,  # Questions + impl(10) + competitor(10) + problem(5)
            "business_pain":            35,  # UP from 25: operational pain, scaling, hiring
            "competitor_switch_bonus":  20,  # NEW: late-stage vendor switching signals
            "analytical_depth":         12,  # NEW: data-driven buyer complexity
            "engagement_compound":      22,  # UP from 15: exponential with signal escalation
            "constraint_x_depth":       15,  # Constraints × depth multiplier
            "content_richness":         15,  # UP from 8: single-reply evaluator bonus
            "question_density":          7,  # Questions per reply
            "velocity":                  5,  # REDUCED cap
            "consistency":               3,  # Reliable cadence
            # Penalty
            "shallow_penalty":         -15,
        }

        # Band thresholds (User Defined 5-Tier)
        self.BANDS = {
            "ready_now_min":    85,   # 85+  → Ready Now (Closing Floor)
            "high_intent_min":  71,   # 71-84 → High Intent
            "evaluating_min":   51,   # 51-70 → Evaluating
            "light_interest_min": 31, # 31-50 → Light Interest
            "noise_max":         30   # 0-30 → Noise
        }



    # ==========================================
    # MAIN ANALYSIS
    # ==========================================
    def analyze_thread(self, thread_history):
        if not thread_history:
            return self._default_result()

        signals = self._extract_signals(thread_history)
        metrics = self._calculate_metrics(thread_history, signals)
        score_breakdown = self._calculate_score(metrics)
        raw_score = sum(score_breakdown.values())
        normalized_score = min(100, max(0, raw_score))

        # ── Fix 4 (P1): SINGLE-REPLY SOFT CAP ──
        # Single-reply threads cap at 90 to preserve headroom
        # for multi-turn proven buyers to differentiate.
        lead_count = len([m for m in thread_history if m.get('sender') == 'lead'])
        if lead_count <= 1 and normalized_score > 90:
            normalized_score = 90

        # ── KEYWORD SPAM HARD CAP ──
        # Spam can fire 100+ raw signal points from pattern matches alone.
        # The -80 penalty isn't always enough. Hard cap at 15 (Noise band)
        # ensures keyword-stuffed messages never escape Noise.
        if signals.get('is_keyword_spam'):
            normalized_score = min(normalized_score, 15)

        state = self._classify_state(normalized_score)
        explanation = self._generate_explanation(metrics, signals, score_breakdown)
        cliff_flag = self._check_engagement_cliff(thread_history)
        momentum = self._calculate_momentum(thread_history, metrics, score_breakdown)
        
        # Force Cooling if the thread is stale (>48h), overriding sentiment-based Stable/Rising.
        if metrics.get('hours_since_last_lead', 0) > 48:
            momentum = "Cooling"

        tiebreaker = self._calculate_tiebreaker(metrics, signals)

        # ── COOLING SCORE DECAY ──
        # When momentum is Cooling, apply a time-based soft decay
        # so stale threads actually drop in sort priority.
        # Without this, a 73/Ready Now lead with 5 days silence
        # still sits at the top — defeating the purpose of cooling.
        cooling_decay = 0
        cooling_decay = 0
        if momentum == "Cooling":
            # Use the GREATER of current silence or the longest gap in the thread.
            # If they just replied after 5 days (gap=120h) with a weak message,
            # they are still "Cooling" and should be penalized for the drag.
            hours_stale = metrics.get('hours_since_last_lead', 0)
            max_gap = metrics.get('max_gap_hours', 0)
            effective_staleness = max(hours_stale, max_gap)

            if effective_staleness > 120:       # 5+ days
                decay_pct = 0.35
            elif effective_staleness > 96:      # 4-5 days
                decay_pct = 0.25
            elif effective_staleness > 48:      # 2-4 days
                decay_pct = 0.15
            elif effective_staleness > 24:      # 1-2 days
                decay_pct = 0.05
            else:
                decay_pct = 0.0
            cooling_decay = round(normalized_score * decay_pct)
            normalized_score = max(0, normalized_score - cooling_decay)
            # Re-classify state after decay
            state = self._classify_state(normalized_score)

        full_explanation = self._generate_full_explanation(metrics, signals, score_breakdown)

        return {
            "score": normalized_score,
            "score_breakdown": score_breakdown,
            "state": state,
            "explanation": explanation,
            "full_explanation": full_explanation,
            "signals": signals,
            "metrics": metrics,
            "cliff_flag": cliff_flag,
            "momentum": momentum,
            "tiebreaker": tiebreaker,
            "cooling_decay": cooling_decay
        }

    # ==========================================
    # SIGNAL EXTRACTION
    # ==========================================
    def _extract_signals(self, history):
        lead_messages = [m['body'].lower() for m in history if m.get('sender') == 'lead']
        combined_text = " ".join(lead_messages)

        # ── Fix 3 (P1): NEGATION HANDLING ──
        # Suppress signals when preceded by negation phrases.
        # We create a "cleaned" version where negated clauses are removed
        # before signal matching.
        negation_patterns = [
            r"not\s+(?:looking\s+to\s+|planning\s+to\s+|going\s+to\s+)?",
            r"n't\s+(?:looking\s+to\s+|planning\s+to\s+|going\s+to\s+)?",
            r"no\s+(?:plans?\s+(?:to|for)\s+)?",
            r"never\s+",
            r"don't\s+(?:want\s+to\s+|need\s+to\s+)?",
            r"won't\s+",
            r"aren't\s+",
            r"we're\s+not\s+",
            r"we\s+are\s+not\s+",
            r"we\s+don't\s+",
            r"happy\s+with\s+(?:what\s+we\s+have|our\s+current)",
        ]
        # Build negated text: remove negation + next 8 words for signal suppression
        negated_text = combined_text
        for neg_pat in negation_patterns:
            negated_text = re.sub(
                neg_pat + r'(\S+(?:\s+\S+){0,7})',
                '', negated_text
            )

        extracted = {}
        for key, patterns in self.PATTERNS.items():
            count = 0
            # Use negated_text for competitor, business_pain, implementation
            # (signals most likely to be negated in real email)
            search_text = negated_text if key in ('competitor', 'business_pain', 'implementation') else combined_text
            for p in patterns:
                if re.search(p, search_text):
                    count += 1
            extracted[key] = count

        extracted["word_count"] = len(combined_text.split())
        extracted["question_count"] = combined_text.count("?")
        extracted["lead_message_count"] = len(lead_messages)

        # Per-message avg word count
        if lead_messages:
            word_counts = [len(m.split()) for m in lead_messages]
            extracted["avg_words_per_reply"] = sum(word_counts) / len(word_counts)
        else:
            extracted["avg_words_per_reply"] = 0

        # ── Fix 1 (P0): KEYWORD DENSITY / COHERENCE CHECK ──
        # Detect unnatural keyword stuffing: high signal-keyword ratio
        # relative to total word count, AND lack of sentence structure.
        words = combined_text.split()
        total_words = len(words)
        total_signal_hits = sum(v for k, v in extracted.items()
                                if k not in ('word_count', 'question_count',
                                             'lead_message_count', 'avg_words_per_reply'))

        # Coherence check: does the text have verbs / sentence structure?
        has_verbs = bool(re.search(
            r'\b(is|are|was|were|have|has|had|do|does|did|will|would|could|'
            r'can|should|need|want|like|use|using|looking|trying|think|'
            r'know|see|get|make|take|give|help|work|run|go|come|tell|'
            r'ask|seem|feel|keep|let|begin|show|hear|play|move|live|believe)\b',
            combined_text
        ))
        has_sentences = bool(re.search(r'[.!?]', combined_text)) or bool(re.search(r'\b(we|our|i|my|you|your)\b', combined_text))

        # Density ratio: signal hits per word. Natural text ≈ 0.05-0.15.
        # Spam has 0.3+ (every other word is a keyword)
        density_ratio = total_signal_hits / max(total_words, 1)
        # Spam detection only applies to SINGLE-REPLY threads.
        # Multi-turn conversations naturally accumulate signal keywords
        # across replies and should never be flagged as spam.
        num_lead_msgs = len(lead_messages)
        is_keyword_spam = False
        if num_lead_msgs <= 1:
            if density_ratio > 0.4 and total_signal_hits >= 8:
                # Extreme density — always spam regardless of verbs
                is_keyword_spam = True
            elif density_ratio > 0.3 and total_signal_hits >= 8 and (not has_verbs or not has_sentences):
                # High density without structure
                is_keyword_spam = True
            elif density_ratio > 0.3 and total_signal_hits >= 12 and total_words < 30:
                # Short message, tons of keywords = list-style spam
                is_keyword_spam = True

        extracted["is_keyword_spam"] = is_keyword_spam
        extracted["keyword_density"] = round(density_ratio, 3)

        # ── JARGON WITHOUT SPECIFICS DETECTION ──
        # Buzzword-heavy sentences that pass spam detection but lack
        # concrete details (numbers, proper nouns, measurements).
        # e.g. "scalable prioritization orchestration to optimize SDR throughput velocity"
        jargon_words = [
            r'\b(?:scalable|orchestrat\w+|prioritiz\w+|optimiz\w+|streamlin\w+)\b',
            r'\b(?:throughput|velocity|synerg\w+|leverage\w*|alignment)\b',
            r'\b(?:holistic|paradigm|ecosystem|framework|methodology)\b',
            r'\b(?:actionable|transformative|disruptive|innovative|cutting.edge)\b',
            r'\b(?:empower\w*|enablement|operationalize|verticalize)\b',
        ]
        jargon_hits = sum(1 for jp in jargon_words if re.search(jp, combined_text))
        has_concrete = bool(re.search(r'\d+\s*(?:reps?|sdrs?|seats?|users?|people|%|hours?|mins?|days?|weeks?|months?|\$|k\b)', combined_text))
        is_jargon = (jargon_hits >= 2 and not has_concrete and num_lead_msgs <= 1)
        extracted["is_jargon"] = is_jargon

        # ── Fix 2 (P0): DISENGAGEMENT DETECTION ──
        # Check the LAST lead message for disengagement phrases.
        last_lead_msg = lead_messages[-1] if lead_messages else ""
        disengage_patterns = [
            r"revisit\s+(?:this\s+)?(?:next|later|in\s+q[1-4])",
            r"next\s+quarter",
            r"next\s+year",
            r"not\s+(?:right\s+now|at\s+this\s+time|a\s+priority)",
            r"other\s+priorities",
            r"put\s+(?:this\s+)?on\s+hold",
            r"circle\s+back\s+later",
            r"table\s+this",
            r"shelv(?:e|ing)\s+(?:this|the)",
            r"we(?:'ve|\s+have)\s+decided\s+(?:to\s+)?(?:wait|hold|pause|revisit)",
            r"not\s+(?:the\s+right|a\s+good)\s+time",
            r"maybe\s+(?:later|next|down\s+the\s+road)",
            r"appreciate\s+your\s+time\b(?!.*\b(?:demo|call|meeting|schedule))",
        ]
        is_disengaging = False
        for dp in disengage_patterns:
            if re.search(dp, last_lead_msg):
                # EXCEPTION: Financial planning context
                # "Budget resets next quarter" should not trigger disengagement.
                # If "budget", "fiscal", or "funding" appears, treat temporal markers as timeline info, not blow-off.
                if ("quarter" in last_lead_msg or "year" in last_lead_msg) and \
                   re.search(r'\b(?:budgets?|fiscal|funding)\b', last_lead_msg):
                    continue
                
                is_disengaging = True
                break
        
        extracted["is_disengaging"] = is_disengaging

        # ── Fix P2: SARCASM DETECTION ──
        # Emoji + dismissive language = sentiment inversion.
        # Detect sarcasm markers and penalize signal firing.
        sarcasm_markers = [
            r'[😂🤣😏😅🙄💀😜😹]',                    # sarcasm emoji
            r'(?:totally|sure|oh\s+yeah|right|very funny)',  # dismissive superlatives
            r'(?:lol|lmao|rofl|haha)',                        # laugh markers
        ]
        sarcasm_count = sum(1 for sp in sarcasm_markers if re.search(sp, combined_text))
        # Sarcasm = 2+ markers (emoji + superlative together)
        # OR emoji + very short text (dismissive one-liner)
        is_sarcastic = (
            sarcasm_count >= 2 or
            (sarcasm_count >= 1 and total_words < 25)
        )
        extracted["is_sarcastic"] = is_sarcastic

        # ── ACTIVE VENDOR EVALUATION DETECTION ──
        # Some buyers skip pain articulation entirely. They're in
        # vendor-selection mode: comparing tools, requesting pilots,
        # and moving on a tight timeline. Detect these signals.
        pilot_patterns = [
            r'\b(?:pilot|trial|poc|proof\s+of\s+concept)\b',
            r'\b(?:test|try)\s+(?:it|this|with)\b',
        ]
        has_pilot_intent = any(re.search(pp, combined_text) for pp in pilot_patterns)
        extracted["has_pilot_intent"] = has_pilot_intent

        fast_action_patterns = [
            r'\b(?:this\s+week|tomorrow|today|immediately|right\s+away)\b',
            r'\b(?:asap|as\s+soon\s+as)\b',
        ]
        has_fast_action = any(re.search(fp, combined_text) for fp in fast_action_patterns)
        extracted["has_fast_action"] = has_fast_action

        # ── CONTRADICTION DETECTION ──
        # Positive sentiment + "but" + exploration = hedging.
        # e.g. "We're happy with our setup but exploring alternatives."
        positive_sentiment = bool(re.search(
            r'\b(?:happy|satisfied|content|pleased|good|fine|great|love|like)\b.*\b(?:with|about)\b',
            combined_text
        ))
        has_but_pivot = bool(re.search(
            r'\b(?:but|however|though|although)\b.*\b(?:explor|look|evaluat|consider|open\s+to|curious|alternatives?)\b',
            combined_text
        ))
        is_contradictory = (positive_sentiment and has_but_pivot)
        extracted["is_contradictory"] = is_contradictory


        closing_patterns = [
            r'\b(?:send|review|sign|forward)\s+(?:the\s+)?(?:contract|msa|dpa|agreement|paperwork)\b',
            r'\b(?:ready|want|like|will)\s+to\s+(?:sign|countersign|execute)\b',
            r'\b(?:where|how)\s+do\s+i\s+sign\b',
            r'\b(?:legal|contract|agreement)\s+(?:has\s+)?approved\b',
            r'\b(?:sent|signed)\s+(?:the\s+)?(?:contract|msa|dpa)\b',
            r'\bsign\s+by\b',
            r'\bcan\s+(?:we|i)\s+sign\b',
            r'\b(?:execute|final)\s+contract\b',
            r'\bagreement\s+attached\b',
        ]
        has_closing_intent = any(re.search(cp, combined_text) for cp in closing_patterns)
        extracted["has_closing_intent"] = has_closing_intent

        return extracted

    # ==========================================
    # METRICS
    # ==========================================
    def _calculate_metrics(self, history, signals):
        lead_replies = [m for m in history if m.get('sender') == 'lead']
        depth = len(lead_replies)

        timestamps = sorted([m['timestamp'] for m in history])
        if len(timestamps) > 1:
            diffs = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            avg_response_time_hours = (sum(diffs) / len(diffs)) / 3600
        else:
            avg_response_time_hours = 24

        is_consistent = 1 if avg_response_time_hours < 24 else 0

        # Evaluative signal count
        eval_signals = sum(1 for k in ["implementation", "competitor", "problem_desc", "business_pain"]
                          if signals.get(k, 0) > 0)

        # Constraint signal count
        constraint_count = sum(1 for k in ["pricing", "timeline", "budget", "stakeholder"]
                               if signals.get(k, 0) > 0)

        # Question density
        questions_per_reply = 0
        if depth > 0:
            questions_per_reply = signals.get("question_count", 0) / depth

        # Business pain category count (number of distinct pain pattern matches)
        pain_count = signals.get("business_pain", 0)

        # Analytical depth (data-driven buyer)
        analytical_count = signals.get("analytical", 0)

        # Hours since the most recent lead reply (for cooling decay)
        import time as _time
        lead_timestamps = sorted([m['timestamp'] for m in lead_replies])
        if lead_timestamps:
            hours_since_last_lead = (_time.time() - lead_timestamps[-1]) / 3600
        else:
            hours_since_last_lead = 0

        # Max gap between messages (to detect drag even if they just replied)
        max_gap_hours = 0
        if len(lead_timestamps) > 1:
            gaps = [lead_timestamps[i] - lead_timestamps[i-1] for i in range(1, len(lead_timestamps))]
            if gaps:
                max_gap_hours = max(gaps) / 3600

        return {
            "depth": depth,
            "velocity_hours": avg_response_time_hours,
            "is_consistent": is_consistent,
            "signals": signals,
            "eval_signals": eval_signals,
            "constraint_count": constraint_count,
            "questions_per_reply": questions_per_reply,
            "timeline_urgency": signals.get("timeline", 0),
            "avg_words_per_reply": signals.get("avg_words_per_reply", 0),
            "pain_count": pain_count,
            "analytical_count": analytical_count,
            "hours_since_last_lead": hours_since_last_lead,
            "max_gap_hours": max_gap_hours
        }

    # ==========================================
    # SCORING (V2 — 8 Corrections)
    # ==========================================
    def _calculate_score(self, metrics):
        s = metrics['signals']
        depth = metrics['depth']
        pain_count = s.get('business_pain', 0)

        # -------------------------------------------------
        # 1. EVALUATIVE DEPTH (max 30)
        #    Questions + implementation + competitor + problem
        # -------------------------------------------------
        eval_base = 0

        qc = s.get('question_count', 0)
        if qc >= 4:
            eval_base += 18
        elif qc == 3:
            eval_base += 12
        elif qc == 2:
            eval_base += 7
        elif qc == 1:
            eval_base += 3

        # Implementation discussion (+10)
        if s.get('implementation'):
            eval_base += 10

        # Competitor mention (+10)
        if s.get('competitor'):
            eval_base += 10

        # Problem clarity (+5)
        if s.get('problem_desc'):
            eval_base += 5

        evaluative_depth = min(30, eval_base)

        # -------------------------------------------------
        # 2. BUSINESS PAIN (V3, max 35)
        #    Raised ceiling. Pain-only threads with clear
        #    operational scale must reach 50 baseline.
        # -------------------------------------------------
        pain_score = 0

        if pain_count >= 4:
            pain_score = 35
        elif pain_count >= 3:
            pain_score = 30  # Systemic evaluator — 3 distinct pain signals
        elif pain_count >= 2:
            pain_score = 22
        elif pain_count >= 1:
            pain_score = 14

        business_pain = min(35, pain_score)

        # -------------------------------------------------
        # 2b. COMPETITOR SWITCH BONUS (V3 NEW, max 20)
        #     Independent axis. Late-stage vendor switching
        #     signals auto-bonus heavily.
        #     "switching", "considering leaving", "currently using X but"
        # -------------------------------------------------
        competitor_count = s.get('competitor', 0)
        competitor_switch_bonus = 0

        if competitor_count >= 3:
            competitor_switch_bonus = 20  # Deep vendor evaluation
        elif competitor_count >= 2:
            competitor_switch_bonus = 16  # Multi-signal vendor eval
        elif competitor_count >= 1:
            competitor_switch_bonus = 12  # Single competitor mention = still late-stage

        competitor_switch_bonus = min(20, competitor_switch_bonus)

        # -------------------------------------------------
        # 2c. ANALYTICAL DEPTH (V3 NEW, max 12)
        #     Data-driven buyers score on complexity of inquiry.
        #     Questions about metrics, accuracy, delta = high cognition
        #     High cognition = serious evaluation
        # -------------------------------------------------
        analytical_count = s.get('analytical', 0)
        analytical_depth = 0

        if analytical_count >= 3:
            analytical_depth = 12
        elif analytical_count >= 2:
            analytical_depth = 8
        elif analytical_count >= 1:
            analytical_depth = 5

        # -------------------------------------------------
        # 3. ENGAGEMENT COMPOUND (V3, max 22, CONTENT-GATED)
        #    Exponential: 5 * 1.7^(depth-1)
        #    V3: Signal escalation — if evaluative signals
        #    appear in later turns, compound sharply.
        #    Not flat. Scales exponentially when signals
        #    appear in later turns.
        # -------------------------------------------------
        if depth >= 1:
            compound_raw = 5 * (1.7 ** (depth - 1))

            # Content quality gate
            has_evaluative_content = (
                eval_base > 0 or
                pain_score > 0 or
                competitor_switch_bonus > 0 or
                analytical_depth > 0 or
                metrics.get('constraint_count', 0) > 0
            )
            avg_wpr = metrics['avg_words_per_reply']

            if avg_wpr < 8 and not has_evaluative_content:
                # Vague multi-turn: crush compounding
                content_mult = 0.3
            elif avg_wpr < 12 and not has_evaluative_content:
                # Low-effort multi-turn without signals
                content_mult = 0.5
            else:
                content_mult = 1.0

            # V3: Signal escalation multiplier
            # When depth + signals combine, this is buying motion
            if depth >= 3 and (eval_base >= 15 or pain_score >= 14):
                compound_raw *= 1.5  # Signals + depth = buying motion
            if depth >= 4 and (eval_base >= 20 or competitor_switch_bonus >= 12):
                compound_raw *= 1.3  # Deep + competitor = late-stage

            engagement_compound = max(5, min(22, round(compound_raw * content_mult)))
        else:
            engagement_compound = 0

        # -------------------------------------------------
        # 4. CONSTRAINT × DEPTH MULTIPLIER (max 15)
        #    V3: Budget + pain amplifier. Budget approved
        #    WITH pain should amplify, not dampen.
        # -------------------------------------------------
        raw_constraint = 0
        if s.get('budget'):
            raw_constraint += 7
            # V3: Budget + pain amplifier
            if pain_count >= 1:
                raw_constraint += 8  # Budget confirmed WITH operational pain
        if s.get('timeline'):
            raw_constraint += 5
        if s.get('pricing'):
            raw_constraint += 4
        if s.get('stakeholder'):
            raw_constraint += 4

        if depth >= 4:
            depth_mult = 1.0
        elif depth == 3:
            depth_mult = 0.9
        elif depth == 2:
            depth_mult = 0.6
        elif depth == 1:
            # V3: Don't crush depth=1 when signals have substance
            if raw_constraint >= 10 or pain_count >= 2:
                depth_mult = 0.7
            else:
                depth_mult = 0.3
        else:
            depth_mult = 0.0

        constraint_x_depth = min(15, round(raw_constraint * depth_mult))

        # -------------------------------------------------
        # 5. VELOCITY (max 5, REDUCED)
        # -------------------------------------------------
        vh = metrics['velocity_hours']
        if vh < 1:
            velocity = 3  # Instant: suspicious
        elif vh < 3:
            velocity = 5  # Sweet spot
        elif vh < 12:
            velocity = 3
        elif vh < 24:
            velocity = 1
        else:
            velocity = 0

        # -------------------------------------------------
        # 6. QUESTION DENSITY (max 7)
        # -------------------------------------------------
        qpr = metrics['questions_per_reply']
        if qpr >= 2.0:
            question_density = 7
        elif qpr >= 1.0:
            question_density = 5
        elif qpr >= 0.5:
            question_density = 3
        else:
            question_density = 0

        # -------------------------------------------------
        # 7. CONSISTENCY (max 3, REDUCED)
        # -------------------------------------------------
        consistency = 3 if metrics['is_consistent'] else 0

        # -------------------------------------------------
        # 8. CONTENT RICHNESS BONUS (V3, max 15)
        #    Single-reply high-depth evaluators get a bonus.
        #    V3: Includes competitor_switch_bonus + analytical
        #    in richness input. Raised ceiling.
        # -------------------------------------------------
        richness_input = evaluative_depth + business_pain + competitor_switch_bonus + analytical_depth
        content_richness = 0

        if depth <= 2 and richness_input >= 35:
            content_richness = 15  # Multi-axis evaluator at depth 1-2
        elif depth <= 2 and richness_input >= 25:
            content_richness = 12  # Strong evaluator
        elif depth <= 2 and richness_input >= 18:
            content_richness = 10
        elif depth <= 2 and richness_input >= 12:
            content_richness = 8
        elif depth <= 2 and richness_input >= 8:
            content_richness = 5

        # -------------------------------------------------
        # 9. SHALLOW PENALTY (up to -15)
        #    Only when NO evaluative substance.
        # -------------------------------------------------
        avg_wpr = metrics['avg_words_per_reply']
        penalty = 0

        has_substance = (qc > 0 or eval_base > 0 or pain_score > 0 or
                         raw_constraint > 0 or competitor_switch_bonus > 0 or
                         analytical_depth > 0)

        if depth >= 2 and avg_wpr < 5 and not has_substance:
            penalty = -12
            if vh < 1:
                penalty = -15
        elif depth >= 2 and avg_wpr < 8 and not has_substance:
            penalty = -2
            if vh < 1:
                penalty = -4

        # -------------------------------------------------
        # 10. KEYWORD SPAM PENALTY (Fix 1 P0)
        #     Unnatural keyword density without sentence
        #     structure = gaming. HARD CAP: zero out all
        #     positive signals so spam always scores 0.
        # -------------------------------------------------
        spam_penalty = 0
        if s.get('is_keyword_spam'):
            # Zero out every positive signal — spam gets nothing
            evaluative_depth = 0
            business_pain = 0
            competitor_switch_bonus = 0
            analytical_depth = 0
            engagement_compound = 0
            constraint_x_depth = 0
            content_richness = 0
            velocity = 0
            question_density = 0
            consistency = 0
            spam_penalty = -5  # Small residual to surface the warning


        #     Buzzword-heavy, no concrete specifics.
        #     Halve evaluative_depth and content_richness
        #     so jargon alone can't reach Evaluating.
        # -------------------------------------------------
        if s.get('is_jargon') and not s.get('is_keyword_spam'):
            evaluative_depth = evaluative_depth // 2
            content_richness = content_richness // 2
            business_pain = business_pain // 2
            analytical_depth = analytical_depth // 2

        # -------------------------------------------------
        # 11. DISENGAGEMENT PENALTY (Fix 2 P0, up to -30)
        #     Last message contains explicit disengagement.
        #     "Revisit next quarter", "other priorities", etc.
        #     Pulls score down significantly.
        # -------------------------------------------------
        disengage_penalty = 0
        if s.get('is_disengaging'):
            disengage_penalty = -30

        # -------------------------------------------------
        # 12. SARCASM PENALTY (P2 hardening — MULTIPLICATIVE)
        #     Emoji + dismissive language → sentiment inversion.
        #     Halve all key signal scores, THEN apply flat -20.
        #     This prevents sarcastic messages from scoring
        #     high when they accidentally trigger many patterns.
        # -------------------------------------------------
        sarcasm_penalty = 0
        if s.get('is_sarcastic'):
            # Multiplicative discount: halve key signals
            evaluative_depth = evaluative_depth // 2
            business_pain = business_pain // 2
            competitor_switch_bonus = competitor_switch_bonus // 2
            content_richness = content_richness // 2
            analytical_depth = analytical_depth // 2
            # Flat penalty on top of the halved signals
            sarcasm_penalty = -20

        # -------------------------------------------------
        # 12b. CONTRADICTION DISCOUNT
        #     "Happy with X but exploring Y" = hedging.
        #     Halve competitor_switch_bonus and content_richness
        #     so contradictory leads stay in Curious.
        # -------------------------------------------------
        if s.get('is_contradictory'):
            competitor_switch_bonus = competitor_switch_bonus // 2
            content_richness = content_richness // 2
            evaluative_depth = evaluative_depth // 2

        # -------------------------------------------------
        # 13. ACTIVE VENDOR EVALUATION BONUS (+10)
        #     Pain-less buyers in vendor selection mode:
        #     comparing tools + pilot intent + short timeline.
        #     Lightweight lift — not enough to inflate, but
        #     enough to cross into Ready Now for real buyers.
        # -------------------------------------------------
        vendor_eval_bonus = 0
        if (competitor_switch_bonus > 0
                and s.get('has_pilot_intent')
                and s.get('has_fast_action')):
            vendor_eval_bonus = 10

        # -------------------------------------------------
        # 14. CLOSING INTENT BOOST (The "Take My Money" Rule)
        #     If they ask for a contract, invoice, or say "approved",
        #     they are Ready Now. Period.
        #     Floor the score at 85 unless spam/disengage.
        # -------------------------------------------------
        closing_boost = 0
        if s.get('has_closing_intent') and not s.get('is_keyword_spam') and not s.get('is_disengaging'):
            # Calculate what's needed to reach 85
            # Note: We must sum up all impacts so far to know the gap
            current_sum = (evaluative_depth + business_pain + competitor_switch_bonus +
                           analytical_depth + engagement_compound + constraint_x_depth +
                           content_richness + velocity + question_density + consistency + 
                           penalty + spam_penalty + disengage_penalty + sarcasm_penalty + vendor_eval_bonus)
            
            # Apply floor of 85
            if current_sum < 85:
                closing_boost = 85 - current_sum

        return {
            "evaluative_depth": evaluative_depth,
            "business_pain": business_pain,
            "competitor_switch_bonus": competitor_switch_bonus,
            "analytical_depth": analytical_depth,
            "engagement_compound": engagement_compound,
            "constraint_x_depth": constraint_x_depth,
            "content_richness": content_richness,
            "velocity": velocity,
            "question_density": question_density,
            "consistency": consistency,
            "shallow_penalty": penalty,
            "spam_penalty": spam_penalty,
            "disengage_penalty": disengage_penalty,
            "sarcasm_penalty": sarcasm_penalty,
            "vendor_eval_bonus": vendor_eval_bonus,
            "closing_boost": closing_boost
        }

    # ==========================================
    # STATE CLASSIFICATION
    # ==========================================
    def _classify_state(self, score):
        if score >= self.BANDS["ready_now_min"]:
            return "Ready Now"
        elif score >= self.BANDS["high_intent_min"]:
            return "High Intent"
        elif score >= self.BANDS["evaluating_min"]:
            return "Evaluating"
        elif score >= self.BANDS["light_interest_min"]:
            return "Light Interest"
        else:
            return "Noise"

    # ==========================================
    # MOMENTUM — V2 ESCALATION DETECTION
    # ==========================================
    def _calculate_momentum(self, history, metrics, score_breakdown):
        """
        V2: Detect escalation even on single high-quality replies.
        - Single reply with high evaluative depth → Rising (start of eval)
        - Multi-turn: compare first-half vs second-half quality
        - Low-effort throughout → Stable or Cooling
        - Disengagement detected → always Cooling
        """
        # Fix 2: Disengagement override — always Cooling
        if metrics.get('signals', {}).get('is_disengaging'):
            return "Cooling"

        lead_msgs = [m for m in history if m.get('sender') == 'lead']

        # Single reply: check if it's evaluative
        if len(lead_msgs) == 1:
            richness = score_breakdown.get('evaluative_depth', 0) + score_breakdown.get('business_pain', 0)
            if richness >= 10:
                return "Rising"  # Strong first reply = upward trajectory
            return "Stable"

        # Multi-turn: compare halves
        mid = len(lead_msgs) // 2
        first_half = lead_msgs[:mid]
        second_half = lead_msgs[mid:]

        def half_quality(msgs):
            text = " ".join([m['body'].lower() for m in msgs])
            score = 0
            score += text.count("?") * 4
            score += len(text.split())
            for key in ["implementation", "competitor", "problem_desc", "business_pain"]:
                for p in self.PATTERNS.get(key, []):
                    if re.search(p, text):
                        score += 6
            return score

        q1 = half_quality(first_half)
        q2 = half_quality(second_half)

        if q2 > q1 * 1.3:
            return "Rising"
        elif q1 > q2 * 1.3:
            return "Cooling"
        else:
            return "Stable"

    # ==========================================
    # TIE-BREAKER
    # ==========================================
    def _calculate_tiebreaker(self, metrics, signals):
        return {
            "eval_signals": metrics.get('eval_signals', 0),
            "constraint_count": metrics.get('constraint_count', 0),
            "timeline_urgency": metrics.get('timeline_urgency', 0),
            "velocity_hours": metrics.get('velocity_hours', 999)
        }

    # ==========================================
    # EXPLANATION (V2 — surfaces pain + competitor)
    # ==========================================
    def _generate_explanation(self, metrics, signals, score_breakdown):
        s = signals
        candidates = []

        # Business pain (highest priority in V2)
        if s.get('business_pain', 0) >= 2:
            candidates.append((score_breakdown.get('business_pain', 0),
                             f"Articulated business pain ({s['business_pain']} signals)"))
        elif s.get('business_pain', 0) == 1:
            candidates.append((8, "Expressed operational pain"))

        # Evaluative signals
        qc = s.get('question_count', 0)
        if qc >= 2:
            candidates.append((score_breakdown.get('evaluative_depth', 0) * 0.5,
                             f"Asked {qc} specific questions"))
        elif qc == 1:
            candidates.append((3, "Asked a direct question"))

        if s.get('implementation'):
            candidates.append((10, "Discussed implementation details"))
        if s.get('competitor'):
            candidates.append((10, "Comparing with competitors"))
        if s.get('problem_desc'):
            candidates.append((5, "Described specific problem"))

        # Constraint signals
        if s.get('budget'):
            candidates.append((score_breakdown.get('constraint_x_depth', 0) * 0.4, "Mentioned budget"))
        if s.get('timeline'):
            candidates.append((score_breakdown.get('constraint_x_depth', 0) * 0.3, "Mentioned timeline"))
        if s.get('pricing'):
            candidates.append((score_breakdown.get('constraint_x_depth', 0) * 0.2, "Asked about pricing"))
        if s.get('stakeholder'):
            candidates.append((4, "Referenced stakeholder"))

        # Depth
        depth = metrics['depth']
        if depth >= 3:
            candidates.append((score_breakdown.get('engagement_compound', 0) * 0.3,
                             f"{depth} back-and-forth exchanges"))

        # Velocity (minor)
        if 1 <= metrics['velocity_hours'] < 3:
            candidates.append((1, f"Responsive ({metrics['velocity_hours']:.0f}h avg)"))

        # Penalty
        if score_breakdown.get('shallow_penalty', 0) < 0:
            candidates.append((0, "Shallow replies detected"))

        # Spam penalty (production hardening)
        if score_breakdown.get('spam_penalty', 0) < 0:
            candidates.append((100, "⚠️ Keyword spam detected — score penalized"))

        # Disengagement penalty
        if score_breakdown.get('disengage_penalty', 0) < 0:
            candidates.append((100, "Lead disengaging — revisit later / other priorities"))

        # Sarcasm penalty
        if score_breakdown.get('sarcasm_penalty', 0) < 0:
            candidates.append((50, "Sarcastic tone detected — signals discounted"))

        # Vendor evaluation bonus
        if score_breakdown.get('vendor_eval_bonus', 0) > 0:
            candidates.append((45, "Active vendor evaluation — pilot intent with timeline"))
            
        # Closing Intent (Max Priority)
        if score_breakdown.get('closing_boost', 0) > 0:
            candidates.append((200, "🔥 Contract or Closing Requested"))

        # Sort by weight desc
        candidates.sort(key=lambda x: x[0], reverse=True)

        # Force business_pain, competitor, implementation to surface
        forced = set()
        for _, label in candidates:
            if "pain" in label.lower():
                forced.add(label)
            if "competitor" in label.lower():
                forced.add(label)
            if "implementation" in label.lower():
                forced.add(label)
            if "spam" in label.lower() or "disengag" in label.lower() or "sarcas" in label.lower():
                forced.add(label)

        result = list(forced)
        for _, label in candidates:
            if label not in result:
                result.append(label)
            if len(result) >= 3:
                break

        return result[:3]

    # ==========================================
    # COMPARATIVE EXPLANATION
    # ==========================================
    def compare_leads(self, leads_with_scores):
        if len(leads_with_scores) < 2:
            return []

        sorted_leads = sorted(leads_with_scores, key=lambda x: x['score'], reverse=True)
        comparisons = []

        for i in range(len(sorted_leads) - 1):
            higher = sorted_leads[i]
            lower = sorted_leads[i + 1]

            reasons = []
            h_sig = higher.get('signals', {})
            l_sig = lower.get('signals', {})
            h_met = higher.get('metrics', {})
            l_met = lower.get('metrics', {})

            # Business pain
            h_pain = h_sig.get('business_pain', 0)
            l_pain = l_sig.get('business_pain', 0)
            if h_pain > l_pain:
                reasons.append(f"stronger business pain ({h_pain} vs {l_pain} signals)")

            # Evaluative depth
            h_eval = sum(1 for k in ["implementation", "competitor", "problem_desc"]
                        if h_sig.get(k, 0) > 0)
            l_eval = sum(1 for k in ["implementation", "competitor", "problem_desc"]
                        if l_sig.get(k, 0) > 0)
            if h_eval > l_eval:
                reasons.append(f"deeper evaluation ({h_eval} vs {l_eval} eval signals)")

            # Depth
            h_depth = h_met.get('depth', 0)
            l_depth = l_met.get('depth', 0)
            if h_depth > l_depth:
                reasons.append(f"more engagement ({h_depth} vs {l_depth} replies)")

            # Questions
            h_q = h_sig.get('question_count', 0)
            l_q = l_sig.get('question_count', 0)
            if h_q > l_q:
                reasons.append(f"asked more questions ({h_q} vs {l_q})")

            if not reasons:
                reasons.append(f"higher overall intent ({higher['score']} vs {lower['score']})")

            comparisons.append({
                "higher": higher['email'],
                "lower": lower['email'],
                "reason": f"{higher['email']} outranks {lower['email']} because: {'; '.join(reasons)}"
            })

        return comparisons

    # ==========================================
    # ENGAGEMENT CLIFF
    # ==========================================
    def _check_engagement_cliff(self, history):
        if len(history) < 2:
            return None
        last_msg = sorted(history, key=lambda x: x['timestamp'])[-1]
        time_since_last = time.time() - last_msg['timestamp']
        days_since = time_since_last / (24 * 3600)
        if days_since > 3:
            return "Paused or Internal Blocker"
        return None

    def _default_result(self):
        return {
            "score": 0,
            "score_breakdown": {},
            "state": "Noise",
            "explanation": [],
            "full_explanation": [],
            "signals": {},
            "metrics": {},
            "cliff_flag": None,
            "momentum": "Stable",
            "tiebreaker": {"eval_signals": 0, "constraint_count": 0, "timeline_urgency": 0, "velocity_hours": 999}
        }

    # ==========================================
    # FULL EXPLANATION (Feature 1: Transparency)
    # ==========================================
    def _generate_full_explanation(self, metrics, signals, score_breakdown):
        """
        Returns every signal that fired with its contribution.
        No black box. Trust = transparency.
        """
        s = signals
        items = []

        # Business pain
        pain_count = s.get('business_pain', 0)
        if pain_count > 0:
            items.append({
                "signal": "business_pain",
                "detail": f"Operational pain detected ({pain_count} signal{'s' if pain_count > 1 else ''})",
                "contribution": score_breakdown.get('business_pain', 0)
            })

        # Competitor switching
        comp_count = s.get('competitor', 0)
        if comp_count > 0:
            items.append({
                "signal": "competitor_switch",
                "detail": f"Vendor comparison/switching language ({comp_count} signal{'s' if comp_count > 1 else ''})",
                "contribution": score_breakdown.get('competitor_switch_bonus', 0)
            })

        # Implementation depth
        if s.get('implementation', 0) > 0:
            items.append({
                "signal": "implementation",
                "detail": "Asked about implementation, integration, or setup",
                "contribution": 10  # fixed contribution within evaluative_depth
            })

        # Questions
        qc = s.get('question_count', 0)
        if qc > 0:
            items.append({
                "signal": "questions",
                "detail": f"Asked {qc} specific question{'s' if qc > 1 else ''}",
                "contribution": score_breakdown.get('question_density', 0)
            })

        # Problem description
        if s.get('problem_desc', 0) > 0:
            items.append({
                "signal": "problem_description",
                "detail": "Described a specific problem or challenge",
                "contribution": 5
            })

        # Analytical depth

        # Closing Intent
        if score_breakdown.get('closing_boost', 0) > 0:
            items.append({
                "signal": "closing_intent",
                "detail": "Explicit closing signal (Contract/MSA/Sign)",
                "contribution": score_breakdown.get('closing_boost', 0)
            })
        ana_count = s.get('analytical', 0)
        if ana_count > 0:
            items.append({
                "signal": "analytical_depth",
                "detail": f"Data-driven inquiry ({ana_count} metric{'s' if ana_count > 1 else ''} referenced)",
                "contribution": score_breakdown.get('analytical_depth', 0)
            })

        # Budget
        if s.get('budget', 0) > 0:
            items.append({
                "signal": "budget",
                "detail": "Budget mentioned or approved",
                "contribution": 7
            })

        # Timeline
        if s.get('timeline', 0) > 0:
            items.append({
                "signal": "timeline",
                "detail": "Timeline or urgency referenced",
                "contribution": 5
            })

        # Pricing
        if s.get('pricing', 0) > 0:
            items.append({
                "signal": "pricing",
                "detail": "Asked about pricing or cost",
                "contribution": 4
            })

        # Stakeholder
        if s.get('stakeholder', 0) > 0:
            items.append({
                "signal": "stakeholder",
                "detail": "Referenced decision-maker or internal stakeholder",
                "contribution": 4
            })

        # Engagement depth
        depth = metrics.get('depth', 0)
        if depth >= 2:
            items.append({
                "signal": "engagement_depth",
                "detail": f"Conversation depth: {depth} replies",
                "contribution": score_breakdown.get('engagement_compound', 0)
            })

        # Content richness
        cr = score_breakdown.get('content_richness', 0)
        if cr > 0:
            items.append({
                "signal": "content_richness",
                "detail": "High-density evaluative content in early replies",
                "contribution": cr
            })

        # Shallow penalty
        pen = score_breakdown.get('shallow_penalty', 0)
        if pen < 0:
            items.append({
                "signal": "shallow_penalty",
                "detail": "Low-effort or vague replies detected",
                "contribution": pen
            })

        # Spam penalty (production hardening)
        spam_pen = score_breakdown.get('spam_penalty', 0)
        if spam_pen < 0:
            items.append({
                "signal": "spam_penalty",
                "detail": "Keyword stuffing detected — unnatural keyword density without coherent language",
                "contribution": spam_pen
            })

        # Disengagement penalty
        disengage_pen = score_breakdown.get('disengage_penalty', 0)
        if disengage_pen < 0:
            items.append({
                "signal": "disengage_penalty",
                "detail": "Lead explicitly disengaged (revisit later, other priorities, etc.)",
                "contribution": disengage_pen
            })

        # Sarcasm penalty
        sarcasm_pen = score_breakdown.get('sarcasm_penalty', 0)
        if sarcasm_pen < 0:
            items.append({
                "signal": "sarcasm_penalty",
                "detail": "Sarcastic tone detected — signals may be inverted",
                "contribution": sarcasm_pen
            })

        # Vendor evaluation bonus
        vendor_eval = score_breakdown.get('vendor_eval_bonus', 0)
        if vendor_eval > 0:
            items.append({
                "signal": "vendor_eval_bonus",
                "detail": "Active vendor selection mode — comparing tools with pilot intent and fast timeline",
                "contribution": vendor_eval
            })

        # Sort by contribution descending
        items.sort(key=lambda x: abs(x['contribution']), reverse=True)

        return items

# ==========================================
# PURE FUNCTION WRAPPER (User Request)
# ==========================================
def score_lead(thread_text):
    """
    Pure function interface for scoring a lead based on text.
    Returns: { "confidence": <int 0-100>, "reason": <list of strings> }
    """
    engine = ReplyIntelligence()
    # Treat input text as a single message thread from the lead
    mock_thread = [{
        "sender": "lead",
        "body": thread_text,
        "timestamp": time.time()
    }]
    
    result = engine.analyze_thread(mock_thread)
    
    return {
        "confidence": result.get('score', 0),
        "reason": result.get('explanation', [])
    }
