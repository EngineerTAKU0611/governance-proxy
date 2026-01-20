from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import os
import database  # 作成したデータベースモジュールを接続

# ============================
# 1. 設定エリア
# ============================
GENAI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GENAI_API_KEY)

# 最新モデル (1.5-flash)
model = genai.GenerativeModel('gemini-1.5-flash')

app = FastAPI()

# ============================
# 2. AI対話エンドポイント
# ============================
class ChatRequest(BaseModel):
    text: str
    user_id: str = "guest" # 誰からのアクセスか

@app.post("/v1/chat")
async def chat(request: ChatRequest):
    # ① データベースから正確な残高を取得
    current_budget = database.get_budget()
    
    # 予算チェック
    if current_budget < 1.0:
        # ログに残すために失敗トランザクションを記録しても良いが、
        # ここでは簡易的にエラーを返す
        raise HTTPException(status_code=402, detail=f"Budget Cap Reached! Current: {current_budget} JPY")

    # ② Gemini実行
    try:
        response = model.generate_content(request.text)
        reply_text = response.text
        status = "success"
    except Exception as e:
        reply_text = f"Error: {str(e)}"
        status = "error"

    # ③ コスト計算
    cost = (len(request.text) + len(reply_text)) * 0.1

    # ④ 【重要】DBへの安全な書き込み（トランザクション）
    log_data = {
        "request_type": "chat",
        "user_id": request.user_id,
        "input_text": request.text,  # 将来的にはここでPIIマスク
        "output_text": reply_text,
        "status": status
    }
    
    # 予算減算とログ保存を同時に実行
    new_budget = database.update_budget_and_log_transaction(cost, log_data)

    return {
        "reply": reply_text,
        "cost": cost,
        "remaining_budget": new_budget
    }

# ============================
# 3. 管理者チャージ機能
# ============================
class BudgetRequest(BaseModel):
    amount: float

@app.post("/admin/reset_budget")
def reset_budget(request: BudgetRequest):
    # チャージもログに残す（不正チャージ防止）
    log_data = {
        "request_type": "admin_charge",
        "user_id": "admin",
        "input_text": f"Charge: {request.amount}",
        "output_text": "Approved",
        "status": "success"
    }
    
    # チャージはコストがマイナス（＝予算が増える）として扱う
    # 現在の予算を上書きするのではなく「加算/設定」するロジックだが
    # 今回はシンプルに「セット」するために、update関数を応用するか、
    # 本来は専用関数を作るべき。
    # ★今回は「リセット(上書き)」ロジックをDBモジュールで簡易実装もできるが、
    # 整合性を保つため、古い残高との差額を計算してupdateに流すのが美しい。
    
    current = database.get_budget()
    diff = current - request.amount # 現在100, 目標1000なら、コストは -900
    
    # 予算を request.amount にする
    new_budget = database.update_budget_and_log_transaction(diff, log_data)
    
    return {"status": "success", "message": f"予算を {new_budget}円 に更新しました (監査ログ保存済み)"}