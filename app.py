# -*- coding: utf-8 -*-
"""
Copyright & SARTRAS Legal Assistant - Web Application (Streamlit)
"""

import os
import streamlit as st
from dotenv import load_dotenv

from src.db import search_knowledge
from src.llm import generate_streaming_response, get_secret

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="著作権法・SARTRAS 法令相談AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .reportview-container {
        margin-top: -2em;
    }
    .badge {
        display: inline-block;
        padding: 0.25em 0.5em;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 4px;
        background-color: #e0f2fe;
        color: #0369a1;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("📖 このシステムについて")
st.sidebar.info("""
**著作権法・判例・SARTRAS 相談AI** は、学校教育やオンライン授業における著作物の利用ルールについて、公式法令とガイドラインを根拠に即時回答する無料の公開アシスタントです。
""")

st.sidebar.markdown("### 📚 参照ナレッジベース")
st.sidebar.markdown("""
- **[著作権法](https://laws.e-gov.go.jp/law/345AC0000000048)**: 第30条(私的利用), 第32条(引用), 第35条(学校教育・公衆送信補償金)等
- **[SARTRAS運用指針](https://sartras.or.jp/)**: 授業目的公衆送信補償金制度、問題集・ドリル等の利用制限
- **[裁判所 判例検索](https://www.courts.go.jp/hanrei/search7/index.html)**: 引用要件（最判昭55 パロディ事件等）、試験問題利用の限界
""")

st.sidebar.markdown("---")
st.sidebar.caption("💡 クラウド上の無料枠LLMを活用しており、ユーザー登録やAPIキーの入力不要でどなたでもご利用いただけます。")

# Backend API Configuration (Hidden from end-users)
provider = get_secret("LLM_PROVIDER", "gemini")
api_key = get_secret("GEMINI_API_KEY") if provider == "gemini" else get_secret("OPENAI_API_KEY")
model_name = get_secret("LLM_MODEL", "gemini-2.5-flash")

# Main Interface
st.title("⚖️ 著作権法・判例・SARTRAS 相談アシスタント")
st.caption("教育機関における著作物の複製・オンライン公衆送信・引用の適法性を、公式法令と運用指針に基づいて判定・解説します。")

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Quick Prompt Buttons
st.markdown("##### 💡 よくある相談事例（クリックして即座に質問）")
col1, col2, col3 = st.columns(3)
quick_q = None

if col1.button("📌 第35条とSARTRAS補償金制度の基本"):
    quick_q = "著作権法第35条とSARTRAS（授業目的公衆送信補償金制度）について、学校の授業での利用という観点から要点を教えてください。"
if col2.button("📌 問題集・ドリルのPDF配信"):
    quick_q = "オンライン授業で、市販の計算ドリルやワークブックをスキャンしてPDFにし、受講生徒全員に配ることは認められますか？"
if col3.button("📌 授業解説動画での他人の画像引用"):
    quick_q = "授業用の解説動画で他人の著作物（イラストや写真）を『引用』として掲載する場合、判例上どのような要件が求められますか？"

# Render conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("🔍 参照した根拠条文・ガイドライン・判例"):
                for s in msg["sources"]:
                    st.markdown(f"**[{s['category']}] [{s['title']}]({s['url']})**\n\n```text\n{s['content']}\n```")

# User Input
user_input = st.chat_input("著作権や授業での利用、SARTRASについて質問を入力してください...")
if quick_q:
    user_input = quick_q

if user_input:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 1. Retrieve relevant legal context
    with st.spinner("根拠条文・SARTRAS指針・判例を検索中..."):
        sources = search_knowledge(user_input, top_k=3)

    context_blocks = []
    for s in sources:
        context_blocks.append(f"【{s['category']}: {s['title']}】 (URL: {s['url']})\n{s['content']}")
    context_str = "\n\n".join(context_blocks)

    # 2. Build structured system prompt
    system_prompt = f"""あなたは日本の著作権法、知財裁判例、およびSARTRAS（授業目的公衆送信補償金制度）の専門アドバイザーです。
以下の【提供された法令・ガイドライン・判例】の記述を絶対的な根拠として、質問に明快かつ論理的に回答してください。

# 回答のルール
1. 根拠条文（例:「著作権法第35条第1項ただし書」「SARTRAS共通目的運用指針」等）を必ず明示して解説してください。
2. 補償金支払義務の有無や、認められる利用形態・認められない例外（ドリルの全員配布等）を明確に伝えてください。
3. 参照資料に記載のない推測は避け、「法令・指針上明確な規定がない」旨を注記してください。
4. 回答の最後には必ず以下の免責事項を記載してください：
「※ 本回答はAIによる情報提供であり、弁護士法に基づく法的助言ではありません。具体的な紛争や運用判断については弁護士やSARTRASにお問い合わせください。」

【提供された法令・ガイドライン・判例】:
{context_str}
"""

    messages_payload = [{"role": "system", "content": system_prompt}]
    for m in st.session_state.messages:
        messages_payload.append({"role": m["role"], "content": m["content"]})

    # 3. Stream response from LLM
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        response_stream = generate_streaming_response(
            messages=messages_payload,
            provider=provider,
            api_key=api_key,
            model_name=model_name
        )

        for chunk in response_stream:
            full_response += chunk
            placeholder.markdown(full_response + "▌")
            
        placeholder.markdown(full_response)

        if sources:
            with st.expander("🔍 参照した根拠条文・ガイドライン・判例"):
                for s in sources:
                    st.markdown(f"**[{s['category']}] [{s['title']}]({s['url']})**\n\n```text\n{s['content']}\n```")

        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "sources": sources
        })
