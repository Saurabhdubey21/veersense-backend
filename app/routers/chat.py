import httpx
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

OFFICER_SYSTEM_PROMPT = (
    "You are an expert AI Welfare Advisor for CAPF (Central Armed Police Forces) "
    "officers in India. Help welfare officers understand stress patterns, plan "
    "interventions, and support battalion mental health. Be practical, "
    "evidence-based, and sensitive to the military context. Keep responses "
    "concise and actionable."
)

PERSONNEL_SYSTEM_PROMPT = (
    "You are a compassionate AI Health Advisor for CAPF personnel in India. "
    "Provide warm, practical, culturally sensitive advice. Be empathetic, never "
    "clinical. Always recommend speaking to a Welfare Officer or Medical Officer "
    "for serious concerns, and mention the CAPF helpline for anything urgent. "
    "Keep responses to 2-3 short paragraphs."
)


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest):
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is not configured on the server. Set it in .env / Render env vars.",
        )

    is_officer = False
    if body.context:
        is_officer = body.context.get("role") == "officer"
    system_prompt = OFFICER_SYSTEM_PROMPT if is_officer else PERSONNEL_SYSTEM_PROMPT

    if body.context:
        risk = body.context.get("risk")
        score = body.context.get("score")
        if risk and not is_officer:
            system_prompt += f" The person's current stress score is {score}/100 ({risk} risk level)."

    payload = {
        "model": settings.GROQ_MODEL,
        "max_tokens": 800,
        "messages": [
            {"role": "system", "content": system_prompt},
            *[{"role": m.role, "content": m.content} for m in body.messages],
        ],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Groq API error: {resp.text}")

    data = resp.json()
    reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    return ChatResponse(reply=reply or "I'm here — could you tell me a bit more?")
