import os
import time
import json
from flask import Flask, request, jsonify
from reply_intelligence import ReplyIntelligence

# ==========================================
# CONFIGURATION
# ==========================================
PORT = 8081

# ==========================================
# STORAGE (In-Memory for MVP)
# ==========================================
# Structure (FLAT per user request):
# {
#   "email": {
#       "email": "user@example.com",
#       "thread": [ {"body": ..., "timestamp": ..., "sender": ...} ],
#       "score": 75,
#       "state": "Ready Now" | "Evaluating" | "Curious" | "Noise",
#       "signals": ["Mentioned pricing", ...],
#       "full_explanation": [{"signal": ..., "detail": ..., "contribution": ...}],
#       "last_updated": 1234567890,
#       "cliff_flag": None | "Paused or Internal Blocker",
#       "profile": { "name": "Unknown", "email": ... },
#       "score_history": [0, 32, 71],
#       "intent_jump_alert": None | {"from": 32, "to": 71, "delta": 39, "timestamp": ...},
#       "response_times": [120, 540],
#       "avg_response_time_min": 5.5,
#       "outcome": None | "meeting" | "no_meeting",
#       "last_lead_reply_at": None,
#       "disagreements": []
#   }
# }
LEAD_DB = {} 

reply_engine = ReplyIntelligence()

app = Flask(__name__, static_folder='public', static_url_path='/public')

# ==========================================
# FLASK ROUTES
# ==========================================

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/dashboard')
def serve_dashboard():
    return app.send_static_file('dashboard.html')

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """
    Returns leads sorted by readiness score and categorized.
    Reads directly from the flat LEAD_DB structure.
    """
    global LEAD_DB
    
    ready_now = []
    evaluating = []
    curious = []
    noise = []
    
    # Calculate stats for Performance Panel
    total_replies_analyzed = 0
    time_saved_minutes = 0
    
    # SLA tracking
    sla_under_30 = 0
    sla_over_30 = 0
    sla_no_response = 0
    
    now = time.time()
    
    for email, data in LEAD_DB.items():
        # ── HARDENING: LAZY DECAY (Operational Stability) ──
        # If lead hasn't been updated in >4 hours, re-score it.
        # This ensures "ghost" leads decay even if no new webhook arrives.
        last_updated = data.get('last_updated', 0)
        if (now - last_updated) > (4 * 3600):
            # Only re-score active leads to save CPU
            if data.get('state') in ["Ready Now", "High Intent", "Evaluating", "Light Interest"]:
                # Silent re-score
                analysis = reply_engine.analyze_thread(data['thread'])
                
                # Update DB in place
                data['score'] = analysis.get('score', 0)
                data['state'] = analysis.get('state', 'Noise')
                data['signals'] = analysis.get('explanation', [])
                data['full_explanation'] = analysis.get('full_explanation', [])
                data['cliff_flag'] = analysis.get('cliff_flag')
                data['momentum'] = analysis.get('momentum', 'Stable')
                data['tiebreaker'] = analysis.get('tiebreaker', {})
                data['last_updated'] = now  # Mark as fresh
        
        # Read from flat structure
        state = data.get('state', 'Noise')
        score = data.get('score', 0)
        
        # Count replies (user replies only)
        thread = data.get('thread', [])
        user_replies = [m for m in thread if m.get('sender') == 'lead']
        reply_count = len(user_replies)
        
        if reply_count > 0:
            total_replies_analyzed += reply_count
            
        item = {
            "email": email,
            "score": score,
            "state": state,
            "explanation": data.get('signals', []),
            "full_explanation": data.get('full_explanation', []),
            "cliff_flag": data.get('cliff_flag'),
            "momentum": data.get('momentum', 'Stable'),
            "profile": data.get('profile', {}),
            "last_reply": thread[-1]['timestamp'] if thread else 0,
            "tiebreaker": data.get('tiebreaker', {}),
            "score_history": data.get('score_history', []),
            "intent_jump_alert": data.get('intent_jump_alert'),
            "avg_response_time_min": data.get('avg_response_time_min'),
            "outcome": data.get('outcome')
        }
        
        # SLA tracking for high-intent threads (score >= 60)
        if score >= 60:
            avg_resp = data.get('avg_response_time_min')
            if avg_resp is not None:
                if avg_resp <= 30:
                    sla_under_30 += 1
                else:
                    sla_over_30 += 1
            elif data.get('last_lead_reply_at'):
                sla_no_response += 1
        
        if state == "Ready Now":
            ready_now.append(item)
        elif state in ["High Intent", "Evaluating"]:
            # High Intent (71-84) and Evaluating (51-70) share the 2nd column
            evaluating.append(item)
        elif state == "Light Interest":
            # Light Interest (31-50) maps to the 3rd column
            curious.append(item)
        else:  # Noise
            noise.append(item)
            if reply_count > 0:
                time_saved_minutes += (reply_count * 5)

    # Sort Ready Now by tie-breaker: eval_signals DESC, constraint_count DESC, velocity ASC
    ready_now.sort(key=lambda x: (
        x.get('tiebreaker', {}).get('eval_signals', 0),
        x.get('tiebreaker', {}).get('constraint_count', 0),
        x.get('tiebreaker', {}).get('timeline_urgency', 0),
        -x.get('tiebreaker', {}).get('velocity_hours', 999)
    ), reverse=True)
    evaluating.sort(key=lambda x: x['score'], reverse=True)
    curious.sort(key=lambda x: x['score'], reverse=True)
    noise.sort(key=lambda x: x['score'], reverse=False)
    
    # Comparative explanation layer
    comparative = []
    if len(ready_now) >= 2:
        ready_data = []
        for item in ready_now:
            email = item['email']
            db_entry = LEAD_DB.get(email, {})
            ready_data.append({
                "email": email,
                "score": item['score'],
                "signals": db_entry.get('raw_signals', {}),
                "metrics": db_entry.get('raw_metrics', {})
            })
        comparative = reply_engine.compare_leads(ready_data)
    
    # Band distribution
    total_leads = len(ready_now) + len(evaluating) + len(curious) + len(noise)
    band_distribution = {
        "ready_now": round(len(ready_now) / total_leads * 100) if total_leads else 0,
        "evaluating": round(len(evaluating) / total_leads * 100) if total_leads else 0,
        "curious": round(len(curious) / total_leads * 100) if total_leads else 0,
        "noise": round(len(noise) / total_leads * 100) if total_leads else 0
    }
    
    return jsonify({
        "sections": {
            "ready_now": ready_now,
            "evaluating": evaluating,
            "curious": curious,
            "noise": noise
        },
        "comparative": comparative,
        "stats": {
            "total_analyzed": total_replies_analyzed,
            "ready_count": len(ready_now),
            "evaluating_count": len(evaluating),
            "time_saved_minutes": time_saved_minutes
        },
        "sla": {
            "responded_under_30m": sla_under_30,
            "responded_over_30m": sla_over_30,
            "no_response_yet": sla_no_response
        },
        "band_distribution": band_distribution
    })

@app.route('/webhook/reply', methods=['POST'])
def ingest_reply():
    """
    Receives an inbound reply from a lead.
    Payload: { "email": "...", "body": "...", "timestamp": 1234567890, "sender": "lead" }
    """
    global LEAD_DB
    
    data = request.json
    email = data.get('email')
    body = data.get('body')
    timestamp = data.get('timestamp', time.time())
    sender = data.get('sender', 'lead') # 'lead' or 'agent'
    
    if not email or not body:
        return jsonify(error="Missing email or body"), 400
        
    # Ensure lead exists in DB with flat structure
    if email not in LEAD_DB:
        LEAD_DB[email] = {
            "email": email,
            "thread": [],
            "score": 0,
            "state": "Noise",
            "signals": [],
            "full_explanation": [],
            "last_updated": timestamp,
            "cliff_flag": None,
            "profile": {"name": "Unknown", "email": email},
            "score_history": [],
            "intent_jump_alert": None,
            "response_times": [],
            "avg_response_time_min": None,
            "outcome": None,
            "last_lead_reply_at": None,
            "disagreements": []
        }
    
    # ── Feature 3: Response-Time Tracking ──
    # When agent replies, measure time since last lead reply
    if sender == 'agent' and LEAD_DB[email].get('last_lead_reply_at'):
        lead_time = LEAD_DB[email]['last_lead_reply_at']
        response_seconds = timestamp - lead_time
        if response_seconds > 0:
            LEAD_DB[email]['response_times'].append(response_seconds)
            avg_sec = sum(LEAD_DB[email]['response_times']) / len(LEAD_DB[email]['response_times'])
            LEAD_DB[email]['avg_response_time_min'] = round(avg_sec / 60, 1)

        LEAD_DB[email]['last_lead_reply_at'] = None  # Reset after agent responds
    
    # Track last lead reply timestamp
    if sender == 'lead':
        LEAD_DB[email]['last_lead_reply_at'] = timestamp
    
    # ── HARDENING: IDEMPOTENCY CHECK ──
    # Check last 5 messages for duplicates to prevent webhook retries from double-scoring
    is_duplicate = False
    for msg in LEAD_DB[email]['thread'][-5:]:
        # Match body AND sender.
        if msg['body'] == body and msg['sender'] == sender:
            # If timestamp is within 5 minutes, treat as duplicate retry
            if abs(msg['timestamp'] - timestamp) < 300:
                is_duplicate = True
                break
    
    if is_duplicate:
        # Silent ignore
        return jsonify(success=True, status="ignored_duplicate")

    # Append to thread
    reply_obj = {
        "body": body,
        "timestamp": timestamp,
        "sender": sender
    }
    LEAD_DB[email]['thread'].append(reply_obj)
    
    # ── Feature 4: Intent Jump Detection ──
    # Capture previous score before re-analyzing
    previous_score = LEAD_DB[email]['score']
    
    # Analyze full thread (runs on even single replies)
    analysis_result = reply_engine.analyze_thread(LEAD_DB[email]['thread'])
    
    new_score = analysis_result.get('score', 0)
    
    # Flatten analysis into LEAD_DB entry
    LEAD_DB[email]['score'] = new_score
    LEAD_DB[email]['state'] = analysis_result.get('state', 'Noise')
    LEAD_DB[email]['signals'] = analysis_result.get('explanation', [])
    LEAD_DB[email]['full_explanation'] = analysis_result.get('full_explanation', [])
    LEAD_DB[email]['cliff_flag'] = analysis_result.get('cliff_flag')
    LEAD_DB[email]['momentum'] = analysis_result.get('momentum', 'Stable')
    LEAD_DB[email]['tiebreaker'] = analysis_result.get('tiebreaker', {})
    LEAD_DB[email]['raw_signals'] = analysis_result.get('signals', {})
    LEAD_DB[email]['raw_metrics'] = analysis_result.get('metrics', {})
    LEAD_DB[email]['last_updated'] = timestamp
    
    # Track score history (only on lead replies)
    if sender == 'lead':
        LEAD_DB[email]['score_history'].append(new_score)
    
    # Detect intent jump (delta >= 20)
    score_delta = new_score - previous_score
    intent_jump = None
    if sender == 'lead' and score_delta >= 20 and previous_score > 0:
        intent_jump = {
            "from": previous_score,
            "to": new_score,
            "delta": score_delta,
            "timestamp": timestamp
        }
        LEAD_DB[email]['intent_jump_alert'] = intent_jump
    
    response = {"success": True, "analysis": analysis_result}
    if intent_jump:
        response["intent_jump_alert"] = intent_jump
    
    return jsonify(response)

@app.route('/api/lead/<email>/set_outcome', methods=['POST'])
def set_outcome(email):
    """
    Sets the manual outcome for a lead (meeting, no_meeting, etc.)
    Payload: { "outcome": "meeting" }
    """
    global LEAD_DB
    
    data = request.json
    outcome = data.get('outcome')
    
    if email not in LEAD_DB:
        return jsonify(error="Lead not found"), 404
    
    LEAD_DB[email]['outcome'] = outcome
    return jsonify(success=True, email=email, outcome=outcome)

@app.route('/api/lead/<email>/disagree', methods=['POST'])
def log_disagreement(email):
    """
    Logs when an SDR disagrees with the score.
    Payload: { "direction": "higher" | "lower", "reason": "..." }
    """
    global LEAD_DB
    
    data = request.json
    direction = data.get('direction') # 'higher' or 'lower'
    
    if email not in LEAD_DB:
        return jsonify(error="Lead not found"), 404
    
    if 'disagreements' not in LEAD_DB[email]:
        LEAD_DB[email]['disagreements'] = []
        
    entry = {
        "direction": direction,
        "reason": data.get('reason'),
        "timestamp": time.time(),
        "score_at_time": LEAD_DB[email]['score']
    }
    LEAD_DB[email]['disagreements'].append(entry)
    
    return jsonify(success=True, email=email, direction=direction, logged=True)

if __name__ == '__main__':
    app.run(port=PORT, debug=False)
