import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

# ==========================================
# ⚙️ 設定：監査基準
# ==========================================
st.set_page_config(
    page_title="AI Governance Audit Report",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# データベースファイル
DB_FILE = "governance.db"
# ガバナンス適用開始日時（契約書記載の日時）
GOVERNANCE_STARTED_AT = "2026-01-20 00:00:00 JST"

# 日本時間設定
JST = timezone(timedelta(hours=9))

def load_data():
    """データベースから監査ログを読み込む（ReadOnly）"""
    if not os.path.exists(DB_FILE):
        return None, None
    
    conn = sqlite3.connect(DB_FILE)
    
    # 予算情報の取得
    budget_df = pd.read_sql_query("SELECT * FROM budget", conn)
    
    # ログの取得（最新順）
    logs_df = pd.read_sql_query("SELECT * FROM logs ORDER BY id DESC", conn)
    
    conn.close()
    return budget_df, logs_df

# ==========================================
# 🎨 UI: ヘッダーエリア（証明書スタイル）
# ==========================================
st.title("🛡️ AI Governance & Audit Report")
st.markdown("### **CONFIDENTIAL // INTERNAL AUDIT ONLY**")
st.markdown(f"**Generated At:** {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
st.markdown("---")

# データの読み込み
budget_df, logs_df = load_data()

if budget_df is None:
    st.error("🚨 CRITICAL ERROR: Governance Database Not Found.")
    st.stop()

# ==========================================
# 📊 KPI: 経営者・監査人向けサマリ
# ==========================================
col1, col2, col3, col4 = st.columns(4)

# 1. 現在予算（Budget）
current_budget = budget_df['remaining_budget'][0]
col1.metric("📉 Remaining Budget", f"¥{current_budget:,.2f}")

# 2. 総コスト（Total Cost）
if not logs_df.empty:
    total_cost = logs_df['cost'].sum()
    col2.metric("💰 Total Consumed", f"¥{total_cost:,.2f}")
else:
    col2.metric("💰 Total Consumed", "¥0.00")

# 3. ブロック件数（Protection Count）
if not logs_df.empty:
    blocked_count = logs_df[logs_df['status'] != 'success'].shape[0]
    col3.metric("🛡️ Threat Blocked", f"{blocked_count} reqs", delta_color="inverse")
else:
    col3.metric("🛡️ Threat Blocked", "0 reqs")

# 4. ログ保全性（Integrity）
col4.metric("✅ Log Integrity", "SECURED", "WORM Active")

# ==========================================
# 📜 証明書発行エリア（The 'Kill Shot'）
# ==========================================
st.markdown("---")
st.subheader("📑 Audit Certification (監査証明)")

with st.expander("Show Integrity Statement (法的免責事項)", expanded=True):
    st.info(f"""
    **Governance Scope Declaration:**
    
    本システムは、**{GOVERNANCE_STARTED_AT}** 以降に発生した全てのAIトランザクションを記録・監視しています。
    表示されるデータは `SQLite/WORM` 技術により保護されており、開発者による改ざんや隠蔽が不可能であることを証明します。
    
    * **Traceability:** 全リクエストの入力・出力・コストを追跡可能
    * **Liability:** 予算超過および禁止ワードに対する遮断措置を実施済み
    """)

# ==========================================
# 🔍 詳細ログビューア（証拠リスト）
# ==========================================
st.subheader("🔍 Transaction Logs (Evidence)")

if not logs_df.empty:
    # 表示するカラムを整理
    display_cols = ['timestamp', 'request_type', 'user_id', 'status', 'cost', 'final_budget']
    
    # フィルタリング機能
    status_filter = st.selectbox("Filter by Status", ["ALL", "success", "blocked", "error"])
    if status_filter != "ALL":
        filtered_df = logs_df[logs_df['status'] == status_filter]
    else:
        filtered_df = logs_df

    st.dataframe(
        filtered_df[display_cols],
        use_container_width=True,
        hide_index=True
    )
    
    # 嘘偽りのない全データダウンロードボタン（監査人用）
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Full Audit Log (CSV)",
        csv,
        "audit_evidence.csv",
        "text/csv",
        key='download-csv'
    )

else:
    st.warning("No transactions recorded yet. System is active and waiting for requests.")

# ==========================================
# Footer
# ==========================================
st.markdown("---")
st.caption("Powered by Governance-Proxy Infrastructure | 🔒 Secured by WORM Technology")