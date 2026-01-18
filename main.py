import os
import time
import json
import logging
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# --- 設定 ---
# Renderの環境変数からキーを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    # ローカルテスト用（もし環境変数がなければ警告）
    print("Warning: GEMINI_API_KEY not found.")

# Geminiの設定
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 予算設定（仮想通貨：YEN）
BUDGET_LIMIT_YEN = 100.0  # 100円まで
CURRENT_USAGE_YEN = 0.0   # 現在の使用額
COST_PER_CHAR = 0.1       # 1文字0.1円（仮想コスト）

# ログファイル
AUDIT_LOG_FILE = "audit.jsonl"

# アプリの準備
app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    user_id: str = "guest"

def log_audit(event_type: str, user: str, cost: float, detail: str):
    """監査ログを記録する"""
    log_entry = {
        "timestamp": time.time(),
        "event": event_type,
        "user": user,
        "cost_yen": cost,
        "detail": detail
    }
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

@app.post("/v1/chat")
async def chat_proxy(request: ChatRequest):
    global CURRENT_USAGE_YEN
    
    user_msg = request.message
    
    # 1. 予算チェック（Governance）
    # 入力文字数から仮想コストを試算
    estimated_cost = len(user_msg) * COST_PER_CHAR
    
    if CURRENT_USAGE_YEN + estimated_cost > BUDGET_LIMIT_YEN:
        # 遮断発動！
        log_audit("BLOCK", request.user_id, 0, "Budget exceeded")
        raise HTTPException(
            status_code=402, 
            detail=f"Budget exceeded! (Limit: {BUDGET_LIMIT_YEN} YEN)"
        )

    # 2. Gemini APIを実行（Real Execution）
    try:
        response = model.generate_content(user_msg)
        bot_reply = response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 3. コスト確定とログ記録（Audit）
    # 入力+出力の文字数で課金
    total_chars = len(user_msg) + len(bot_reply)
    actual_cost = total_chars * COST_PER_CHAR
    CURRENT_USAGE_YEN += actual_cost
    
    log_audit("SUCCESS", request.user_id, actual_cost, f"Used {total_chars} chars")
    
    return {
        "reply": bot_reply,
        "cost_yen": actual_cost,
        "remaining_budget": BUDGET_LIMIT_YEN - CURRENT_USAGE_YEN
    }

@app.get("/")
def read_root():
    return {"status": "Governance Proxy is Active (Gemini Edition)"}