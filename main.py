from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from reply_intelligence import decide_lead
import csv
import io
import json
from datetime import datetime

app = FastAPI()


class LeadInput(BaseModel):
    text: str
    created_at: str = None # ISO format preferred
    last_reply_from_us: bool = False


# ---------- Single lead scoring ----------
@app.post("/score")
def score(data: LeadInput):
    # UNIFIED PATH: Call decide_lead directly
    metadata = {
        "created_at": data.created_at,
        "last_reply_from_us": data.last_reply_from_us
    }
    result = decide_lead(data.text, metadata=metadata)
    
    return {
        "score": result["priority_score"], 
        "tier": result["tier"],
        "action": result["action"],
        "confidence": result["confidence_bucket"],
        "priority_score": result["priority_score"],
        "priority_level": result["priority_level"],
        "ranking_rationale": "See explanation.",
        "confidence_rationale": "Determined by strict rules.",
        "explanation": result["explanation"],
        "beta_feedback_prompt": result["feedback_prompt"],
        "disposition": result["disposition"]
    }


# ---------- Batch CSV scoring ----------
@app.post("/score-batch-csv")
async def score_batch_csv(file: UploadFile = File(...)):
    content = await file.read()
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError:
        decoded = content.decode("latin-1") 
        
    reader = csv.DictReader(io.StringIO(decoded))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "thread_text",
        "priority_level",      
        "ranking_rationale",  
        "confidence_rationale",
        "action",              
        "tier",                
        "confidence_bucket",   
        "explanation",         
        "feedback_question",   
        "disposition",
        "stage",
        "status",
        "follow_up"
    ])

    sorted_rows = []
    
    headers = reader.fieldnames or []
    date_col = next((h for h in headers if h.lower() in ["created_at", "date", "timestamp", "received_at"]), None)
    reply_col = next((h for h in headers if h.lower() in ["replied", "last_reply_from_us", "is_replied"]), None)
    status_col = next((h for h in headers if h.lower() in ["status", "state"]), None)
    id_col = next((h for h in headers if h.lower() in ["id", "email_id", "email", "lead_id"]), "id")

    # Read all rows first
    all_rows = list(reader)

    for index, row in enumerate(all_rows, start=1):
        text = row.get("thread_text", "").strip()
        if not text:
             pass

        row_id = row.get(id_col, str(index))
        
        # Extract Metadata
        created_at = row.get(date_col) if date_col else None
        
        last_reply = False
        if reply_col:
            val = row.get(reply_col, "").lower()
            if val in ["true", "yes", "1", "y"]:
                last_reply = True
        elif status_col:
            val = row.get(status_col, "").lower()
            if "replied" in val or "handled" in val:
                last_reply = True

        metadata = {
            "created_at": created_at,
            "last_reply_from_us": last_reply,
            "email_id": row_id 
        }

        # UNIFIED PATH
        result = decide_lead(text, metadata=metadata)
        
        feedback_q = result["feedback_prompt"]
        p_score = result["priority_score"]
        p_level = result["priority_level"]
        
        # Metrics for Tie-Breaker
        q_count = text.count("?")
        word_count = len(text.split())

        sorted_rows.append({
            "row": [
                row_id,
                text,
                p_level,
                "Determined by rule engine.",
                "Strict confidence rules.",
                result["action"],
                result["tier"],
                result["confidence_bucket"],
                result["explanation"],
                feedback_q,
                result["disposition"],
                result.get("stage", ""),
                result.get("status", ""),
                result.get("follow_up", "")
            ],
            # Sort Key
            "sort_data": {
                "action": result["action"],
                "score": p_score,
                "q_count": q_count,
                "word_count": word_count,
                "index": index
            }
        })

    # Sort priority: respond_now > respond_later > do_not_respond
    action_rank = {"respond_now": 3, "respond_later": 2, "do_not_respond": 1, "dont_respond": 1}
    
    sorted_rows.sort(key=lambda x: (
        action_rank.get(x["sort_data"]["action"], 0),
        x["sort_data"]["score"],
        x["sort_data"]["q_count"],
        -x["sort_data"]["word_count"],
        -x["sort_data"]["index"]
    ), reverse=True)

    # ==========================================
    # HARDENING 5: BATCH MONITORING
    # ==========================================
    try:
        total_processed = len(sorted_rows)
        if total_processed > 0:
            actions = {"respond_now": 0, "respond_later": 0, "do_not_respond": 0}
            total_score = 0
            
            for item in sorted_rows:
                act = item["sort_data"]["action"]
                if act == "dont_respond": act = "do_not_respond"
                actions[act] = actions.get(act, 0) + 1
                total_score += item["sort_data"]["score"]
            
            avg_score = round(total_score / total_processed, 1)
            
            log_entry = (
                f"{datetime.now().isoformat()} | BATCH | "
                f"Total: {total_processed} | AvgScore: {avg_score} | "
                f"Actions: {json.dumps(actions)}\n"
            )
            
            with open("batch_metrics.log", "a") as f:
                f.write(log_entry)
    except Exception as e:
        print(f"Monitoring Log Error: {e}")

    for item in sorted_rows:
        writer.writerow(item["row"])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=scored_leads.csv"},
    )


# ---------- Beta JSON summary ----------
@app.post("/beta-summary-json")
async def beta_summary_json(file: UploadFile = File(...)):
    content = await file.read()
    try:
         decoded = content.decode("utf-8")
    except UnicodeDecodeError:
         decoded = content.decode("latin-1")
         
    reader = csv.DictReader(io.StringIO(decoded))

    total = 0
    actions = {
        "respond_now": 0,
        "respond_later": 0,
        "do_not_respond": 0
    }
    
    tiers = {}
    
    for k in ["respond_now", "respond_later", "do_not_respond"]:
        actions[k] = 0

    for row in reader:
        text = row.get("thread_text", "").strip()
        if not text:
            continue

        total += 1
        result = decide_lead(text)
        
        act = result["action"]
        tier = result["tier"]
        
        actions[act] = actions.get(act, 0) + 1
        tiers[tier] = tiers.get(tier, 0) + 1

    return {
        "beta_summary": {
            "total_leads": total,
            "action_breakdown": actions,
            "tier_breakdown": tiers,
            "suggested_focus": f"Reply to {actions.get('respond_now', 0)} 'Respond Now' leads today",
            "note": "Summary computed via decide_lead logic."
        }
    }