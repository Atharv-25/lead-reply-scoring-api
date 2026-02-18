from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from reply_intelligence import score_lead
import csv
import io

app = FastAPI()


class LeadInput(BaseModel):
    text: str


@app.get("/")
def home():
    return {"status": "Server is running"}


# ---------- Single lead scoring ----------
@app.post("/score")
def score(data: LeadInput):
    result = score_lead(data.text)
    score_value = result.get("confidence", 0)
    reasons = result.get("reason", [])

    if score_value >= 85:
        tier = "Ready Now"
        state = "Respond immediately"
        next_action = "Reply today. Push meeting or close."
        beta_feedback_prompt = "Did this help you reply faster today? (yes/no)"
    elif score_value >= 71:
        tier = "High Intent"
        state = "Active evaluation"
        next_action = "Reply within 24h. Clarify decision criteria."
        beta_feedback_prompt = "Did this clarify priority vs other leads? (yes/no)"
    elif score_value >= 51:
        tier = "Evaluating"
        state = "Considering options"
        next_action = "Follow up in 3–5 days. Ask timeline."
        beta_feedback_prompt = "Did this clarify follow-up timing? (yes/no)"
    elif score_value >= 31:
        tier = "Light Interest"
        state = "Low urgency"
        next_action = "Nurture. Add to follow-up sequence."
        beta_feedback_prompt = "Did this prevent premature follow-up? (yes/no)"
    else:
        tier = "Noise"
        state = "No buying signal"
        next_action = "Ignore or archive."
        beta_feedback_prompt = "Did this confirm deprioritization? (yes/no)"

    return {
        "score": score_value,
        "tier": tier,
        "state": state,
        "reason": reasons,
        "next_action": next_action,
        "beta_feedback_prompt": beta_feedback_prompt
    }


# ---------- Batch CSV scoring ----------
@app.post("/score-batch-csv")
async def score_batch_csv(file: UploadFile = File(...)):
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "thread_text",
        "score",
        "tier",
        "state",
        "reason",
        "next_action",
        "beta_feedback_prompt"
    ])

    rows = []

    for index, row in enumerate(reader, start=1):
        text = row.get("thread_text", "").strip()
        row_id = row.get("id", index)

        if not text:
            rows.append([
                row_id,
                "",
                0,
                "Noise",
                "No buying signal",
                "Missing thread_text",
                "Ignore or archive.",
                "Did this confirm deprioritization? (yes/no)"
            ])
            continue

        result = score_lead(text)
        score_value = result.get("confidence", 0)
        reasons = result.get("reason", [])

        if score_value >= 85:
            tier = "Ready Now"
            state = "Respond immediately"
            next_action = "Reply today. Push meeting or close."
            beta_feedback_prompt = "Did this help you reply faster today? (yes/no)"
        elif score_value >= 71:
            tier = "High Intent"
            state = "Active evaluation"
            next_action = "Reply within 24h. Clarify decision criteria."
            beta_feedback_prompt = "Did this clarify priority vs other leads? (yes/no)"
        elif score_value >= 51:
            tier = "Evaluating"
            state = "Considering options"
            next_action = "Follow up in 3–5 days. Ask timeline."
            beta_feedback_prompt = "Did this clarify follow-up timing? (yes/no)"
        elif score_value >= 31:
            tier = "Light Interest"
            state = "Low urgency"
            next_action = "Nurture. Add to follow-up sequence."
            beta_feedback_prompt = "Did this prevent premature follow-up? (yes/no)"
        else:
            tier = "Noise"
            state = "No buying signal"
            next_action = "Ignore or archive."
            beta_feedback_prompt = "Did this confirm deprioritization? (yes/no)"

        rows.append([
            row_id,
            text,
            score_value,
            tier,
            state,
            " | ".join(reasons),
            next_action,
            beta_feedback_prompt
        ])

    rows.sort(key=lambda x: x[2], reverse=True)

    for r in rows:
        writer.writerow(r)

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=scored_leads.csv"
        }
    )


# ---------- Beta JSON summary ----------
@app.post("/beta-summary-json")
async def beta_summary_json(file: UploadFile = File(...)):
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    total = 0
    ready_now = 0
    evaluating = 0
    noise = 0

    for row in reader:
        total += 1
        score_value = int(row.get("score", 0))

        if score_value >= 85:
            ready_now += 1
        elif score_value >= 51:
            evaluating += 1
        else:
            noise += 1

    return {
        "beta_summary": {
            "total_leads": total,
            "ready_now": ready_now,
            "evaluating": evaluating,
            "noise": noise,
            "suggested_focus": f"Reply to {ready_now} Ready Now leads today",
            "confidence_check": "Does this match your intuition?"
        }
    }