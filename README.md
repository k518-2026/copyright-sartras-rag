# ⚖️ 著作権法・判例・SARTRAS 相談AI (Copyright & SARTRAS Legal RAG)

日本の著作権法、知財裁判例、および [SARTRAS（授業目的公衆送信補償金制度）](https://sartras.or.jp/) に関する疑問に対して、公式な根拠条文や運用指針を引用しながら回答する専門RAG Webアプリケーションです。

---

## 🌟 主な機能

- **正確な法的根拠の引用**:
  - [e-Gov 著作権法](https://laws.e-gov.go.jp/law/345AC0000000048)（第30条、第32条、第35条など）
  - SARTRAS公式運用指針（問題集・ドリルの制限、送信対象範囲、補償金支払い要件）
  - 最高裁・知財高裁の重要裁判例（パロディ事件等の引用要件）
- **高速ストリーミング推論**:
  - Google Gemini API (`gemini-2.5-flash` / `gemini-2.5-pro`) または OpenAI API (`gpt-4o`) による瞬時の回答生成
- **ハルシネーション（誤認）防止**:
  - ベクトル類似度検索により関連条文・指針を抽出し、プロンプトに注入するRAGアーキテクチャ
- **参照条文の可視化**:
  - 各回答の下部に、参照した根拠条文と公式URLをアコーディオン形式で表示

---

## 🚀 クラウドへのデプロイ（Streamlit Community Cloud 推奨・無料）

GitHub上に本リポジトリを配置すれば、**Streamlit Community Cloud** を使って数分で全世界（または限定公開）にWebサイトを公開できます。

1. 本リポジトリを自身の GitHub アカウントにプッシュ（またはフォーク）します。
2. [Streamlit Community Cloud](https://share.streamlit.io/) にアクセスし、GitHub連携でログインします。
3. **「New app」** をクリックし、以下を設定します：
   - **Repository**: `あなたのユーザー名/copyright-sartras-rag`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. **「Advanced settings...」** を開き、**Secrets** に API キーを設定します：
   ```toml
   LLM_PROVIDER = "gemini"
   GEMINI_API_KEY = "あなたのGemini_API_Key"
   # または OpenAI の場合
   # LLM_PROVIDER = "openai"
   # OPENAI_API_KEY = "あなたのOpenAI_API_Key"
   ```
5. **「Deploy!」** をクリックすると、自動でビルドされ、公開URLが発行されます。

---

## 💻 ローカル環境での起動手順

ローカルPCで動かしたい場合は以下の手順で実行できます。

### 1. リポジトリのクローンと移動
```bash
git clone https://github.com/あなたのユーザー名/copyright-sartras-rag.git
cd copyright-sartras-rag
```

### 2. 仮想環境の作成とライブラリのインストール
```bash
python -m venv venv
# Windowsの場合
venv\Scripts\activate
# Mac / Linuxの場合
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 環境変数の設定
`.env.example` をコピーして `.env` を作成し、APIキーを入力します。
```bash
cp .env.example .env
```

### 4. アプリケーションの起動
```bash
streamlit run app.py
```
ブラウザが開き、`http://localhost:8501` でチャット画面が利用可能になります。

---

## 📁 ディレクトリ構成

```text
copyright-sartras-rag/
├── data/
│   ├── copyright_law.json       # 著作権法重要条文
│   ├── sartras_guidelines.json  # SARTRAS運用指針データ
│   └── precedents.json          # 知財高裁・最高裁判例
├── src/
│   ├── db.py                    # ChromaDBベクトル検索モジュール
│   └── llm.py                   # Gemini / OpenAI API クライアント
├── app.py                       # Streamlit Web アプリ本体
├── ingest.py                    # ナレッジ更新用スクリプト
├── requirements.txt             # 必要パッケージ
├── .env.example                 # 環境変数サンプル
└── README.md                    # 本ドキュメント
```

---

## ⚠️ 免責事項 (Disclaimer)
本アプリケーションは情報提供および学習支援を目的としており、弁護士法第72条に規定される「法律事務の取扱い（法的アドバイス）」を提供するものではありません。具体的な法的紛争、契約、実務運用については、必ず弁護士または関係機関（文化庁・SARTRAS）にお問い合わせください。
