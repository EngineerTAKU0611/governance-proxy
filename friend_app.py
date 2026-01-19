import requests
import json

# ==========================================
# 設定：ここをあなたのRenderのURLに変える
# （末尾に /v1/chat をつけるのがポイント！）
# ==========================================
BASE_URL = "https://governance-proxy.onrender.com/v1" 
# ↑ ※ xxxxの部分はあなたのURLのままにしてください

def test_proxy():
    print("🤖 友人のアプリ: プロキシ経由でGeminiに話しかけます...")
    
    # 送信先（部屋番号）
    url = f"{BASE_URL}/chat"
    
    # データ（手紙の中身）
    # Gemini版はシンプルに "message" だけを送るルールにしました
    payload = {
        "text": "Hello! 今日の東京の天気は？",
        "user_id": "friend_01"
    }

    try:
        # 送信！
        response = requests.post(url, json=payload)
        
        # 結果判定
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功！ Geminiの返事: {data['reply']}")
            print(f"💰 かかったコスト: {data['cost_yen']}円")
            print(f"📉 残り予算: {data['remaining_budget']}円")
        
        elif response.status_code == 402:
            print("🚫 ブロック発動！: 予算オーバーです (狙い通り！)")
            print(f"理由: {response.text}")
            
        else:
            print(f"🛑 失敗: エラーが発生しました (Code: {response.status_code})")
            print(f"理由: {response.text}")

    except Exception as e:
        print(f"💥 接続エラー: {e}")

if __name__ == "__main__":
    test_proxy()