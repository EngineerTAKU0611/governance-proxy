import sqlite3
import json
from datetime import datetime, timezone, timedelta
import os

# ==========================================
# 🛡️ 監査防衛データベース設定
# ==========================================
DB_FILE = "governance.db"
# 日本時間 (JST) の定義 - 監査証跡は現地時間が必須
JST = timezone(timedelta(hours=9))

def init_db():
    """
    データベースの初期構築
    テキストファイルとは異なり、構造化されたテーブルを作成します。
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. 予算管理テーブル (Budget Ledger)
    # 常に1行のみを維持し、書き込み競合を防ぐ
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS budget (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        remaining_budget REAL NOT NULL,
        last_updated_at TEXT NOT NULL
    )
    ''')

    # 2. 監査ログテーブル (Audit Logs)
    # WORM (Write Once Read Many) を意識した、削除を想定しない構造
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,       -- ISO 8601形式 (JST)
        request_type TEXT NOT NULL,    -- 'chat' or 'admin_charge'
        user_id TEXT,                  -- 誰が
        input_text TEXT,               -- 何を (PIIマスク済み)
        output_text TEXT,              -- 結果
        cost REAL,                     -- 変動コスト
        final_budget REAL,             -- その時点での残高
        status TEXT,                   -- 'success', 'blocked', 'error'
        evidence_hash TEXT             -- 将来的な改ざん検知用 (v1は空でも可)
    )
    ''')
    
    # 初期予算データが存在しない場合のみ作成 (デフォルト 0円)
    cursor.execute('SELECT count(*) FROM budget')
    if cursor.fetchone()[0] == 0:
        now_str = datetime.now(JST).isoformat()
        cursor.execute(
            'INSERT INTO budget (id, remaining_budget, last_updated_at) VALUES (1, 0, ?)',
            (now_str,)
        )
        print("✅ Database Initialized: Budget set to 0 JPY")
    
    conn.commit()
    conn.close()

def get_budget():
    """現在の予算残高を安全に読み取る"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT remaining_budget FROM budget WHERE id = 1')
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0.0

def update_budget_and_log_transaction(cost, log_data):
    """
    【重要】銀行レベルのトランザクション処理
    「予算を減らす」と「ログを書く」を不可分な操作として実行。
    片方だけ成功することはあり得ない（All or Nothing）。
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # トランザクション開始
        now_str = datetime.now(JST).isoformat()
        
        # 1. 予算のロックと更新
        cursor.execute('SELECT remaining_budget FROM budget WHERE id = 1')
        current_budget = cursor.fetchone()[0]
        new_budget = current_budget - cost
        
        cursor.execute(
            'UPDATE budget SET remaining_budget = ?, last_updated_at = ? WHERE id = 1',
            (new_budget, now_str)
        )
        
        # 2. 監査ログの追記
        cursor.execute('''
        INSERT INTO logs (timestamp, request_type, user_id, input_text, output_text, cost, final_budget, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            now_str,
            log_data.get("request_type"),
            log_data.get("user_id"),
            log_data.get("input_text"),
            log_data.get("output_text"),
            cost,
            new_budget, # その瞬間の残高も記録（検算用）
            log_data.get("status")
        ))
        
        # コミット：ここで初めて世界に記録される
        conn.commit()
        return new_budget
        
    except Exception as e:
        conn.rollback() # エラー時は時間を巻き戻す（データ矛盾を防ぐ）
        raise e
    finally:
        conn.close()

# モジュール読み込み時に自動初期化
init_db()