from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os
import json

# ============================
# 1. 設定エリア
# ============================
# 自分のAPIキーを入れてください
GENAI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

# モデルの設定（安定のProモデル）
model = genai.GenerativeModel('gemini-pro')

# 予算ファイルの場所
BUDGET_FILE = "budget.json"

app = FastAPI()

# ============================
# 2. 便利な道具（関数）
# ============================
def get_budget():
    """予算ファイルから現在の残高を読み込む"""
    try:
        with open(BUDGET_FILE, "r") as f:
            data = json.load(f)
            return data.get("remaining_budget", 0.0)
    except:
        return 0.0 # ファイルがなければ0円

def update_budget(new_amount):
    """予算を新しい金額で上書き保存する"""
    with open(BUDGET_FILE, "w") as f:
        json.dump({"remaining_budget": new_amount}, f)

# ============================
# 3. AIと話す機能（アプリ用）
# ============================
class ChatRequest(BaseModel):
    text: str

@app.post("/v1/chat")
async def chat(request: ChatRequest):
    # ① まずノート（ファイル）を見て残高確認
    current_budget = get_budget()
    
    # 予算チェック（1円未満ならアウト）
    if current_budget < 1.0:
        raise HTTPException(status_code=402, detail=f"Budget exceeded! (Current: {current_budget} YEN)")

    # ② Geminiに質問する
    try:
        response = model.generate_content(request.text)
        reply_text = response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # ③ コスト計算（文字数 × 0.1円）
    input_char_count = len(request.text)
    output_char_count = len(reply_text)
    total_chars = input_char_count + output_char_count
    cost = total_chars * 0.1

    # ④ 予算を減らしてノートを更新
    new_budget = current_budget - cost
    update_budget(new_budget)

    # ⑤ 返事をする
    return {
        "reply": reply_text,
        "cost": cost,
        "remaining_budget": new_budget
    }

# ============================
# 4. 管理者チャージ機能
# ============================
class BudgetRequest(BaseModel):
    amount: float

@app.post("/admin/reset_budget")
def reset_budget(request: BudgetRequest):
    # ノートを直接書き換える
    update_budget(request.amount)
    return {"status": "success", "message": f"予算を {request.amount}円 にチャージしました！"}