import streamlit as st
import pandas as pd
import json
import datetime

# ページ設定
st.set_page_config(page_title="Governance-Proxy Monitor", layout="wide")

st.title("🛡️ Governance-Proxy 監視センター")
st.markdown("API利用状況と予算超過リスクをリアルタイムで監視中")

# 1. データの読み込み
data = []
try:
    with open("audit.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
except FileNotFoundError:
    st.error("⚠️ ログファイル (audit.jsonl) が見つかりません。")
    st.stop()

if not data:
    st.warning("データがまだありません。リクエストを送ってください。")
    st.stop()

# データを扱いやすい表形式(DataFrame)に変換
df = pd.json_normalize(data)
# 時刻を見やすく変換
df['timestamp'] = pd.to_datetime(df['timestamp_utc'], unit='s') + datetime.timedelta(hours=9) # JST

# --- 2. KPI表示エリア ---
col1, col2, col3, col4 = st.columns(4)

total_requests = len(df)
blocked_requests = len(df[df['risk_assessment.risk_level'] == 'critical'])
total_cost = df['risk_assessment.estimated_cost_usd'].sum()
unique_users = df['requester_id'].nunique()

with col1:
    st.metric("総リクエスト数", f"{total_requests} 回")
with col2:
    st.metric("🚨 遮断数 (Block)", f"{blocked_requests} 回", delta=f"{blocked_requests/total_requests:.1%}", delta_color="inverse")
with col3:
    st.metric("💰 推定コスト総額", f"${total_cost:.5f}")
with col4:
    st.metric("アクティブユーザー", f"{unique_users} 人")

st.divider()

# --- 3. グラフエリア ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("ユーザー別の利用回数")
    user_counts = df['requester_id'].value_counts()
    st.bar_chart(user_counts)

with col_right:
    st.subheader("リスクレベルの割合")
    risk_counts = df['risk_assessment.risk_level'].value_counts()
    st.bar_chart(risk_counts, color="#ff4b4b")

# --- 4. 詳細ログテーブル ---
st.subheader("📝 最新の監査ログ")
# 表示したい列だけ選んで表示
display_df = df[[
    'timestamp', 
    'requester_id', 
    'budget_owner_id', 
    'risk_assessment.risk_level', 
    'risk_assessment.budget_impact_percent',
    'execution_id'
]].sort_values('timestamp', ascending=False)

# テーブル表示（条件付き書式）
def highlight_critical(val):
    color = 'red' if val == 'critical' else 'black'
    return f'color: {color}; font-weight: bold'

st.dataframe(
    display_df.style.applymap(highlight_critical, subset=['risk_assessment.risk_level']),
    use_container_width=True
)