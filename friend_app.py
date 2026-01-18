import urllib.request
import json
import time

# --- ここが「インジェクション」ポイント ---
# 本来は "https://api.openai.com/v1" ですが、
# これをあなたのプロキシに向けさせます。
BASE_URL = "https://governance-proxy.onrender.com/v1" 
# ---------------------------------------

def chat_with_ai(prompt):
    print(f"🤖 友人のアプリ: 「{prompt}」と送信中...")
    
    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-dummy-key", # 本物は不要
        # 以下のヘッダーは、あなたが友人に「これ入れておいて」と頼むIDです
        "X-Requester-ID": "friend_takashi",
        "X-Budget-Owner-ID": "prof_sato",
        "X-Intent-Purpose": "research"
    }
    data = json.dumps({
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as res:
            response = json.load(res)
            print("✅ 成功: プロキシを通過しました！")
            print(f"   サーバーからの返事: {response}")
            
    except urllib.error.HTTPError as e:
        print(f"🛑 失敗: エラーが発生しました (Code: {e.code})")
        error_body = json.load(e)
        print(f"   理由: {error_body.get('detail', 'Unknown error')}")

if __name__ == "__main__":
    # テスト1: 短い文章（予算内のはず）
    chat_with_ai("Hello!")
    
    print("-" * 30)
    time.sleep(1)
    
    # テスト2: 長い文章（予算オーバーを狙う）
    long_prompt = "A" * 5000 # 文字数を稼いでコストを上げる
    chat_with_ai(long_prompt)