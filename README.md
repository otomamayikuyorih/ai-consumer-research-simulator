# 🧠 AI Consumer Research Simulator
### 〜 次世代自律型マルチエージェント消費者調査・受容性検証プラットフォーム 〜
**第5回 Agentic AI Hackathon with Google Cloud 提出プロジェクト**

[![Google Cloud](https://img.shields.io/badge/Google_Cloud-Cloud_Run-4285F4?logo=google-cloud&logoColor=white)](https://cloud.google.com/run)
[![Google Gemini](https://img.shields.io/badge/AI_Engine-Gemini_2.5_Flash-8E75B2?logo=google-gemini&logoColor=white)](https://ai.google.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_3.12-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18_TypeScript-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/UI-Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌟 プロジェクト概要と解決する課題

### 1. 開発の背景と着眼点
従来の消費者調査・マーケティングリサーチ・A/Bテストには、**「数週間の納期」「数百万円の調査コスト」「被験者リクルーティングの偏り」「アンケート回答の疲労・不真面目回答」** という本質的なボトルネックが存在しました。

本プロジェクト **「AI Consumer Research Simulator」** は、日本の公的統計データ（国勢調査・就業構造基本調査・家計調査等）に基づき、属性間の相関関係（年齢・年収・居住地域・消費価値観）を維持した仮想消費者集団を自律生成。さらに**米スタンフォード大学 AI for Public Benefit Lab（AI4PB）の最新研究**および**Nature誌（2026年）の社会科学実験予測手法**を取り入れた、自律型マルチエージェント消費者シミュレータです。

単なる「チャットボット」ではなく、**数百〜千人の独立した個性・信念・生活実感を持つAIエージェント群が、自律的に質問を評価し、心理的一貫性を保ちながら回答し、定性インタビューで理由を語り、新商品受容性を評価**します。

---

## 🏗️ システムアーキテクチャ

Google Cloud Run の完全サーバーレスコンテナ基盤上に、FastAPIバックエンドとReact SPAを統合ホスティング。Google Gemini 2.5 Flash / Vertex AI の高速並列推論基盤を活用し、高精度かつ低レイテンシ・ゼロアイドルコストを実現しています。

![システムアーキテクチャ図](docs/system_architecture.png)

### アーキテクチャの主要コンポーネント

| レイヤー | 採用技術・サービス | 役割・特徴 |
|---|---|---|
| **フロントエンド** | React 18, TypeScript, Vite, Tailwind CSS, Plotly.js | 2階層ナビゲーション、即時多変量解析可視化、レスポンシブUI |
| **実行基盤** | **Google Cloud Run** | 完全マネージドサーバーレスコンテナ、コールドスタート最小化、0〜N自動スケール |
| **AI推論基盤** | **Google Gemini 2.5 Flash / Vertex AI** | 高速並列推論、構造化JSON Schema出力、定性生声の忠実抽出 |
| **セキュリティ・認証** | **GCP Secret Manager** / 環境変数分離 | APIキー秘匿、個人情報マスク、セキュア実行 |
| **ガバナンス・可観測性** | **Cloud Logging** / 同意管理・撤回API | 構造化JSONログ、推論トレーシング、実在被験者データ削除（GDPR/個人情報保護法準拠） |
| **統計・機械学習** | pandas, scikit-learn, scipy, numpy | PCA（主成分分析）、K-Meansクラスタリング、カイ二乗検定、Cohen's d、t検定 |

---

## 🤖 自律的AIエージェントの特徴（エージェントらしさ）

本システムは、以下の6つの専門化されたAIエージェントが協調して動作するマルチエージェント基盤です：

```mermaid
flowchart TD
    subgraph Agents["自律型マルチエージェント協調フレームワーク"]
        A1["1. 統計ペルソナ生成エージェント<br/>(公的統計相関サンプリング)"] --> P["仮想生活者集団 (100〜1,000人)"]
        A2["2. インタビュー根拠化エージェント<br/>(AI4PB: 7次元特性+生声引用保持)"] --> P
        P --> A3["3. 自律回答推論エージェント<br/>(ペルソナ一貫性・心理バイアス維持)"]
        P --> A4["4. 仮想A/B実験エージェント<br/>(Nature 2026: 順序ランダム化・RCT)"]
        P --> A6["6. 1on1 定性深掘り対話エージェント<br/>(文脈適応マルチターン対話)"]
        A3 --> A5["5. Human-AI汎化検証エージェント<br/>(50/50 held-out検証・MAE/RMSE)"]
    end
```

1. **統計ペルソナ生成エージェント (Persona Synthesizer Agent)**:
   - 日本の国勢調査・就業構造基本調査・家計調査等の多変量結合確率分布に従い、非現実的な属性組み合わせ（例: 20代前半で世帯年収2000万の公務員等）を統計的に抑制しながら、100〜1,000人の生活者を自律生成。
2. **インタビュー根拠化エージェント (AI4PB Grounding Agent - Mode C)**:
   - スタンフォード大学 AI4PB 研究に準拠し、実際のインタビュー記録（テキスト/CSV）から「7つの心理行動次元（価値観・消費行動・購買動機・価格感度・意思決定傾向・生活習慣・興味関心）」と「生の発言（Verbatim Quotes）」を忠実に抽出し、ペルソナの記憶基盤を構築。
3. **自律回答推論エージェント (Survey Responding Agent)**:
   - 各仮想生活者が独立した意思決定主体として行動。設問間の文脈・購買心理の一貫性を保持しながら、単一選択・複数選択・5段階評価・自由記述を自律回答。
4. **仮想A/B実験エージェント (Virtual A/B RCT Agent - Nature 2026)**:
   - Nature誌（2026年）の社会科学実験手法に準拠。Control条件とTreatment条件の提示順序によるバイアス（アンカリング効果）を相殺するため、エージェントごとにランダム化（Counterbalancing）を実施し、効果量（Cohen's d）と対応のあるt検定を自律算出。
5. **Human-AI汎化検証エージェント (Empirical Validation Agent)**:
   - 実在の人間アンケートデータ（Benchmark）を50/50に自動分割（Calibration用/Held-out Test用）。過学習やハルシネーションを検知し、MAE、RMSE、Pearson相関係数 $r$ でAIの予測精度を客観検証。
6. **1on1 定性深掘り対話エージェント (Qualitative Interview Agent)**:
   - 調査結果から気になったペルソナを選択し、インタビュアーとして深掘りチャットを実施。「なぜこの商品を選んだのか？」という問いに対し、ペルソナの生活背景や過去の回答を参照して自律的に対話。

---

## 🔒 ガバナンス・セキュリティ・学術的誠実性

> **「自律的に動くAIエージェントを、ガバナンスとセキュリティまで含めて『本当に使えるもの』に。」（ハッカソン第5回テーマ）**

本システムでは、実務導入に耐えうるガバナンス・倫理設計を徹底しています：

1. **実在被験者データの同意管理と削除（GDPR / 個人情報保護法準拠）**:
   - Mode C（定性インタビュー取り込み）では、調査参加者の「同意取得確認フラグ (`is_consented_human_subject`)」を必須化。
   - 同意撤回時には `DELETE /api/interview-datasets/{id}` エンドポイントから即座にデータを完全削除可能。
2. **合成データと公的統計の明確な区分表示**:
   - UI全体に「統計データに基づくAI合成シミュレーションであり、実在の母集団調査結果と混同しないこと」を明記する警告バナー・メタデータを設置。
3. **Out-of-sample 検証によるハルシネーション防止**:
   - AIの回答を無批判に信じるのではなく、実測データとの誤差（MAE / RMSE）を常にダッシュボード上で可視化し、精度検証済みの領域でのみ利用できる安全設計。
4. **ゼロ・クレデンシャル・リーク**:
   - APIキーやシークレットは環境変数および GCP Secret Manager のみで管理し、ソースコード・Dockerイメージへの混入を完全に防止。

---

## 🚀 クイックスタート (ローカル開発)

### 必要要件
- Python 3.11 または 3.12
- Node.js 18+ (推奨 20+)
- Google Cloud SDK (`gcloud`) ※Cloud Run デプロイ時

### 1. リポジトリのクローンとセットアップ
```bash
git clone https://github.com/hiroyukiyamamoto/ai-consumer-research-simulator.git
cd ai-consumer-research-simulator
```

### 2. バックエンドの起動
```bash
cd backend
pip install -r requirements.txt

# Gemini APIキーを設定（未設定時はオフライン高精度統計シミュレーションモードで自動起動）
export GEMINI_API_KEY="your-gemini-api-key"

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API仕様書 (Swagger UI): `http://127.0.0.1:8000/docs`
- ヘルスチェック & GCPステータス: `http://127.0.0.1:8000/api/status`

### 3. フロントエンドの起動
```bash
cd ../frontend
npm install
npm run dev
```
- Web UI: `http://localhost:5173`

### 4. 自動結合テスト (E2E Test) の実行
```bash
cd ../backend
python test_e2e.py          # 基本機能全11工程の自動テスト
python test_ai4pb_e2e.py    # AI4PB / Nature 2026 拡張全6工程の自動テスト
```

---

## ☁️ Google Cloud Run へのデプロイ手順

本アプリケーションはフロントエンド（Vite build）とバックエンド（FastAPI）を1つのコンテナに統合したマルチステージ Dockerfile を完備しており、わずか 1 コマンドで Cloud Run にデプロイ可能です。

```bash
# 1. Google Cloud ログイン & プロジェクト設定
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Cloud Run へデプロイ実行 (東京リージョン: asia-northeast1)
gcloud run deploy ai-consumer-research \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 5 \
  --set-env-vars GEMINI_API_KEY="YOUR_GEMINI_API_KEY",GEMINI_MODEL="gemini-2.5-flash",GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
```

> [!TIP]
> `--min-instances 0` により、リクエストがないアイドル時の課金は **完全無料（¥0）** です。審査員アクセス時のみ数秒でオンデマンド起動します。

---

## 📊 主要機能一覧 (全9モジュール)

1. **ダッシュボード**: システム全体の統計概要、ペルソナ属性分布、公的統計ベンチマーク検証、直近調査・実験ステータスの一覧表示。
2. **ペルソナ生成・検証**: 100〜1,000人の仮想生活者を3つの生成モード（Mode A: 人口統計 / Mode B: 合成リッチ / Mode C: 定性インタビュー根拠化）で生成。
3. **アンケート作成**: 単一選択、複数選択、5段階評価尺度、自由記述形式の設問を自由自在にビジュアル設計。
4. **調査シミュレーション**: 生成したペルソナ群に対し、Gemini 2.5 Flash を用いて超高速に並列回答シミュレーションを実行。
5. **結果解析・多変量解析**:
   - 単純集計、クロス集計、カイ二乗検定（有意水準判定）。
   - 主成分分析 (PCA) によるブランド・受容性知覚マップ散布図。
   - K-Means クラスタリングによる自動セグメンテーション。
   - 自由記述コメントの AI 要約・感情比率（ポジティブ/ニュートラル/ネガティブ）分析。
   - Excel対応 UTF-8 BOM付き個票生データ CSVダウンロード。
6. **仮想A/B実験 (Nature 2026)**: Control / Treatment 条件の提示順序をランダム化し、平均差・割合差・効果量（Cohen's d）・対応のあるt検定を有意差検定。
7. **Human-AI汎化検証 (AI4PB)**: 実測アンケートデータを 50/50（Calibration / Held-out Test）に自動分割し、MAE、RMSE、Pearson 相関係数 $r$ で AI シミュレーションの予測精度を厳密に客観評価。
8. **AIインタビュー (1on1 Deep Talk)**: アンケート回答者の中から気になるペルソナを選択し、1対1で理由や生活背景を深掘りチャット。
9. **コンセプト評価 (商品受容性テスト)**: 新商品コンセプト案・価格・説明文を入力し、購入意向・価格受容性・利用シーン・改善提案を自動出力。

---

## 📜 ライセンス & 権利表記

- 本ソフトウェアは [MIT License](LICENSE) の下で公開されています。
- 電通の「People Model」「People Research」「AI For Growth Talk」のコンセプトおよび公開情報に着想を得ていますが、電通の独自データ・商標・特許・独自アルゴリズムを複製したものではなく、日本の公的統計データと一般的なオープン技術および最新学術論文に基づき独自にスクラッチ開発した独立システムです。
- 参考学術論文:
  - *Large Language Models Can Predict the Results of Social Science Experiments*, Nature (2026).
  - *LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals*, Stanford AI4PB Lab.
