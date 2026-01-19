import requests

# 【重要】あなたのRenderのURLに書き換えてください（.onrender.comまで）
BASE_URL = "https://governance-proxy.onrender.com"

def charge_budget():
    print("========================================")
    print("💰 AIガバナンス・管理システム")
    print("========================================")
    
    try:
        # 金額を入力させる
        amount_str = input("チャージしたい金額を入力してください (例: 1000) > ")
        amount = float(amount_str)

        # サーバーに命令を送る
        url = f"{BASE_URL}/admin/reset_budget"
        payload = {"amount": amount}
        
        print("通信中...")
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功！: {data['message']}")
        else:
            print(f"🛑 失敗: {response.text}")

    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    charge_budget()