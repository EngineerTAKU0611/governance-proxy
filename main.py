import uvicorn
import httpx
import hashlib
import time
# ↓ jsonライブラリを追加インポート
import json 
from fastapi import FastAPI, Request, HTTPException, Header
from schemas import ImmutableLog, ExecutionIntent, RiskAssessment

app = FastAPI(title="Governance-Proxy v0.1")

# 予算オーバー設定のまま維持
MOCK_BUDGET = {
    "prof_sato": {"limit": 10.0, "current_usage": 9.9} 
}

TARGET_API_URL = "https://api.openai.com/v1/chat/completions"

@app.post("/v1/chat/completions")
async def proxy_openai_request(
    request: Request,
    x_requester_id: str = Header(..., alias="X-Requester-ID"),
    x_budget_owner_id: str = Header(..., alias="X-Budget-Owner-ID"),
    x_intent_purpose: str = Header("debug", alias="X-Intent-Purpose"),
    authorization: str = Header(...)
):
    body = await request.json()
    estimated_cost = len(str(body)) * 0.00005 
    
    budget = MOCK_BUDGET.get(x_budget_owner_id, {"limit": 10.0, "current_usage": 0.0})
    current_total = budget["current_usage"] + estimated_cost
    usage_percent = (current_total / budget["limit"]) * 100
    
    risk_level = "low"
    if usage_percent > 100:
        risk_level = "critical"
    elif usage_percent > 80:
        risk_level = "high"

    log_entry = ImmutableLog(
        execution_id=f"exec_{int(time.time()*1000)}",
        requester_id=x_requester_id,
        budget_owner_id=x_budget_owner_id,
        target_url=TARGET_API_URL,
        intent=ExecutionIntent(purpose=x_intent_purpose, description="Proxy Request"),
        risk_assessment=RiskAssessment(
            estimated_cost_usd=estimated_cost,
            risk_level=risk_level,
            budget_impact_percent=usage_percent
        ),
        request_body_hash=hashlib.sha256(str(body).encode()).hexdigest()
    )
    log_entry.log_hash = log_entry.compute_canonical_hash()
    
    # --- 【ここが追加機能】ログをファイルに永久保存 ---
    # audit.jsonl というファイルに追記モード('a')で書き込む
    with open("audit.jsonl", "a", encoding="utf-8") as f:
        # JSON形式で1行書き込む
        f.write(log_entry.model_dump_json() + "\n")
    # -----------------------------------------------
    
    print(f"\n[AUDIT] ID: {log_entry.execution_id}")
    print(f"[AUDIT] Risk: {risk_level} (Budget: {usage_percent:.1f}%)")
    print(f"[AUDIT] >> Saved to audit.jsonl")  # 保存したことを表示

    if risk_level == "critical":
        print(">>> BLOCKED: Budget Exceeded <<<")
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Budget limit exceeded. Approval required.",
                "audit_id": log_entry.execution_id
            }
        )

    return {"message": "Proxy passed!", "audit_id": log_entry.execution_id}

# ポートは8001のまま
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)