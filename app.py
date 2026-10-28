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
    page_title="著作権法・関連法務 総合AIエキスパート",
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
**著作権法・関連法務 総合AIエキスパート** は、著作権法（全文）、施行令、施行規則に加え、**民法、不正競争防止法、プロバイダ責任制限法、独占禁止法、刑法** および **SARTRAS運用指針・重要判例** を網羅した法務特化RAGシステムです。
""")

st.sidebar.markdown("### 📚 参照法令・データベース")
st.sidebar.markdown("""
- **[著作権法・施行令・施行規則](https://laws.e-gov.go.jp/law/345AC0000000048)**: 全条文（第1条〜第124条＋附則）
- **[民法](https://laws.e-gov.go.jp/law/129AC0000000089)**: 不法行為（709条）、契約・損害賠償（415条・416条）等
- **[不正競争防止法](https://laws.e-gov.go.jp/law/405AC0000000047)**: 形態模倣・営業秘密・商品表示
- **[プロバイダ責任制限法](https://laws.e-gov.go.jp/law/413AC0000000137)**: 発信者情報開示請求、差止・送信防止
- **[独占禁止法](https://laws.e-gov.go.jp/law/322AC0000000054)**: 知的財産権の行使と独禁法21条
- **[SARTRAS運用指針](https://sartras.or.jp/)**: 授業目的公衆送信補償金制度
- **[裁判所 判例検索](https://www.courts.go.jp/hanrei/search7/index.html)**: 引用要件・教育利用の限界判例
""")

st.sidebar.markdown("---")
st.sidebar.caption("💡 クラウド上の無料枠LLMを活用しており、ユーザー登録やAPIキーの入力不要でどなたでもご利用いただけます。")

# Backend API Configuration (Hidden from end-users)
provider = get_secret("LLM_PROVIDER", "gemini")
api_key = get_secret("GEMINI_API_KEY") if provider == "gemini" else get_secret("OPENAI_API_KEY")
model_name = get_secret("LLM_MODEL", "gemini-3.8-flash")

# Main Interface
st.title("⚖️ 著作権法・関連法務 総合AIエキスパート")
st.caption("著作権法（全文）、民法、不正競争防止法、プロバイダ責任法、独占禁止法、SARTRAS指針、判例を横断検索して論理的に回答します。")

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
    with st.spinner("著作権法・関連法令・SARTRAS指針・判例を横断検索中..."):
        sources = search_knowledge(user_input, top_k=4)

    context_blocks = []
    for s in sources:
        context_blocks.append(f"【{s['category']}: {s['title']}】 (URL: {s['url']})\n{s['content']}")
    context_str = "\n\n".join(context_blocks)

    # 2. Build structured system prompt
    system_prompt = f"""あなたは日本の著作権法および関連法務（民法、不正競争防止法、プロバイダ責任制限法、独占禁止法、刑法）、知財裁判例、SARTRASの最高峰エキスパートです。
以下の【提供された法令・ガイドライン・判例】の記述を絶対的な根拠として、多角的かつ論理的に回答してください。

# エキスパート回答のルール
1. 該当する法令名と条項番号（例:「著作権法第41条」「民法第709条（不法行為）」「不正競争防止法第2条第1項」「プロバイダ責任制限法第3条」等）を必ず明示してください。
2. 著作権法上の判断だけでなく、民事上の損害賠償・不法行為責任や、インターネット上での開示請求・削除、不正競争の観点など、関連法が関係する場合は複合的な視点からわかりやすく整理してください。
3. 参照資料に直接記載のない事実関係については、「法令・ガイドライン上は明文規定がないため、契約約款や実務慣行の確認が必要」など、法的に誠実な注記をしてください。
4. 回答の最後には必ず以下の免責事項を記載してください：
「※ 本回答はAIによる情報提供であり、弁護士法第72条に基づく個別具体的な法的助言ではありません。実務上の判断や紛争対応にあたっては、弁護士または所管官庁（文化庁等）にご相談ください。」

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
