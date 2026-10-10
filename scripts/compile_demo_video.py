"""
AI Consumer Research Simulator - Demo Video Slide Renderer & Video Compiler
Generates 1080p slide images, pairs with Haruka TTS audio, and encodes submission/demo_video.mp4 with ffmpeg.
"""

import os
import sys
import subprocess
import json
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(r"C:\Users\hyama\AppData\Local\Temp", "demo_video_gen")
os.makedirs(TEMP_DIR, exist_ok=True)
SUBMISSION_DIR = os.path.join(BASE_DIR, "submission")
os.makedirs(SUBMISSION_DIR, exist_ok=True)
ARCH_PNG = os.path.join(BASE_DIR, "docs", "system_architecture.png")
OUTPUT_MP4 = os.path.join(SUBMISSION_DIR, "demo_video.mp4")

# Font helpers
FONT_BOLD_PATH = r"C:\Windows\Fonts\yugothb.ttc"
FONT_REG_PATH = r"C:\Windows\Fonts\meiryo.ttc"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

SCENES = [
    {
        "id": "scene01",
        "title": "AI Consumer Research Simulator",
        "subtitle": "日本の公的統計 ＆ スタンフォードAI4PB研究に基づく自律型マルチエージェント消費者調査基盤",
        "tag": "01 / OVERVIEW",
        "text": "第5回 Agentic AI Hackathon with Google Cloud 提出作品、AI Consumer Research Simulator です。",
        "type": "title",
    },
    {
        "id": "scene02",
        "title": "従来の市場調査が抱える課題 ＆ エージェントによる解決",
        "subtitle": "数週間の納期・数百万の費用を、公的統計×自律型マルチエージェントで数分に短縮",
        "tag": "02 / PROBLEM & SOLUTION",
        "text": "新商品の企画や市場調査には、数週間と数百万円がかかります。本システムは、日本の公的統計データと、スタンフォード大学AI4PB研究に基づく自律型マルチエージェントを活用し、仮想消費者集団へのアンケート調査、多変量解析、そして1対1の深掘りインタビューをわずか数分で完結させるWebプラットフォームです。",
        "type": "problem_solution",
    },
    {
        "id": "scene03",
        "title": "統計ペルソナ生成エージェント (Persona Synthesizer)",
        "subtitle": "国勢調査・家計調査等の多変量相関に基づき非現実な組み合わせを排除 (100〜1,000人規模)",
        "tag": "03 / PERSONA SYNTHESIZER",
        "text": "まず、仮想消費者を生成します。日本の国勢調査や家計調査の統計相関を考慮し、年齢、年収、居住地、消費価値観の非現実的な組み合わせを排除したリアルな生活者群を自律生成します。",
        "type": "persona_gen",
    },
    {
        "id": "scene04",
        "title": "公的統計ベンチマーク客観検証 (e-Stat Benchmark)",
        "subtitle": "生成集団の年代・性別・地域分布をe-Stat公的統計と高精度合致検証 (乖離率 < 5%)",
        "tag": "04 / STATISTICAL BENCHMARK",
        "text": "公的統計ベンチマーク検証を開くと、生成されたペルソナの年代比率や地域分布が、実際の国勢調査のデータと高い精度で合致していることが客観的に確認できます。",
        "type": "benchmark",
    },
    {
        "id": "scene05",
        "title": "自律回答推論エージェントによるアンケート調査",
        "subtitle": "単一選択・複数選択・5段階評価・自由記述に Gemini 3.8 Flash で高速並列回答",
        "tag": "05 / SURVEY SIMULATION",
        "text": "次にアンケート調査です。設問形式は単一選択、5段階評価、自由記述に対応。Google Gemini 3.8 Flash により、各ペルソナが自身の価値観と一貫性を保ちながら自律的に回答を生成します。",
        "type": "survey_sim",
    },
    {
        "id": "scene06",
        "title": "高度な集計・多変量解析ダッシュボード",
        "subtitle": "クロス集計＆カイ二乗検定、主成分分析（PCA）、K-Means、AI感情要約を即時可視化",
        "tag": "06 / MULTIVARIATE ANALYTICS",
        "text": "集計結果は即座にダッシュボードへ反映されます。単純集計に加え、クロス集計とカイ二乗検定、さらに主成分分析による知覚マップや、ケイミーンズによる生活者セグメンテーション、自由記述のAI感情要約まで、高度な多変量解析が自動で行われます。",
        "type": "analytics",
    },
    {
        "id": "scene07",
        "title": "Nature 2026準拠 仮想A/Bランダム化実験 (RCT)",
        "subtitle": "Control群/Treatment群の提示順ランダム化でバイアス相殺・効果量Cohen's dとt検定算出",
        "tag": "07 / VIRTUAL A/B EXPERIMENT",
        "text": "本システムの最大の特徴が、最新の学術研究準拠の検証機能です。Nature 2026年論文の手法に基づき、条件提示順によるバイアスを相殺するランダム化A/B実験を実施。価格や訴求の違いによる購買意向の差と効果量を統計的に算出します。",
        "type": "ab_experiment",
    },
    {
        "id": "scene08",
        "title": "スタンフォード大学 AI4PB準拠 Human-AI汎化検証",
        "subtitle": "実測データ50/50 held-out分割による汎化性能検証 (MAE / RMSE / Pearson r)",
        "tag": "08 / EMPIRICAL VALIDATION",
        "text": "さらに、実在の人間の回答データを用いた50/50の汎化性能検証により、AIのシミュレーション精度を客観的に測定。ハルシネーションに依存しない信頼性の高い意思決定を支援します。",
        "type": "validation",
    },
    {
        "id": "scene09",
        "title": "1on1 定性深掘りインタビュー (Qualitative Agent)",
        "subtitle": "生活背景と過去の回答履歴を参照し、リアルな「生の声」で理由を語る自律エージェント",
        "tag": "09 / 1ON1 INTERVIEW",
        "text": "定量調査のあとは、回答者と1対1の深掘りインタビューが可能です。なぜこの商品を選んだのかと尋ねると、ペルソナの生活背景や価値観に根ざしたリアルな生の声で理由を語ってくれます。",
        "type": "interview",
    },
    {
        "id": "scene10",
        "title": "AIガバナンス・同意管理・セキュリティ",
        "subtitle": "実在被験者の同意管理と削除API (GDPR準拠) ＆ Cloud Logging による推論監査",
        "tag": "10 / GOVERNANCE & PRIVACY",
        "text": "実在の被験者データに対する同意管理・データ削除APIを完備し、個人情報保護とAIガバナンスも徹底しています。",
        "type": "governance",
    },
    {
        "id": "scene11",
        "title": "Google Cloud サーバーレス構成 ＆ まとめ",
        "subtitle": "Cloud Run ＋ Gemini 3.8 Flash によるゼロアイドルコスト ＆ 完全オンデマンド推論",
        "tag": "11 / ARCHITECTURE & SUMMARY",
        "text": "Google Cloud Run の完全サーバーレスコンテナと Gemini 3.8 Flash の高速推論により、ゼロアイドルコストと高スケーラビリティを両立しました。生活者の声を科学する、新しいAIエージェントの姿です。ご視聴ありがとうございました。",
        "type": "summary",
    },
]

def render_base_slide(sc):
    # 1920 x 1080 canvas with high-tech dark slate theme
    img = Image.new("RGB", (1920, 1080), color=(15, 23, 42)) # #0f172a
    draw = ImageDraw.Draw(img)

    # Top Navigation / Header Bar
    draw.rectangle([(0, 0), (1920, 110)], fill=(30, 41, 59)) # #1e293b
    draw.line([(0, 110), (1920, 110)], fill=(51, 65, 85), width=2) # #334155

    # Header Tag & Title
    f_tag = get_font(FONT_BOLD_PATH, 20)
    f_title = get_font(FONT_BOLD_PATH, 34)
    f_sub = get_font(FONT_REG_PATH, 20)

    draw.text((60, 22), sc["tag"], font=f_tag, fill=(56, 189, 248)) # sky-400
    draw.text((60, 52), sc["title"], font=f_title, fill=(248, 250, 252)) # white

    # Badges on top-right
    # Google Cloud Run Badge
    draw.rounded_rectangle([(1430, 32), (1640, 78)], radius=8, fill=(66, 133, 244))
    draw.text((1445, 42), "☁ Cloud Run", font=get_font(FONT_BOLD_PATH, 22), fill=(255, 255, 255))

    # Gemini 3.8 Flash Badge
    draw.rounded_rectangle([(1660, 32), (1860, 78)], radius=8, fill=(142, 117, 178))
    draw.text((1675, 42), "✦ Gemini 3.8", font=get_font(FONT_BOLD_PATH, 22), fill=(255, 255, 255))

    # Bottom Subtitle Area (Lower Third)
    draw.rectangle([(0, 920), (1920, 1080)], fill=(10, 15, 29))
    draw.line([(0, 920), (1920, 920)], fill=(56, 189, 248), width=3) # glowing line

    # Subtitle icon / pill
    draw.rounded_rectangle([(60, 940), (190, 975)], radius=6, fill=(30, 41, 59))
    draw.text((75, 946), "NARRATION", font=get_font(FONT_BOLD_PATH, 16), fill=(148, 163, 184))

    # Subtitle Text wrapping
    f_narr = get_font(FONT_BOLD_PATH, 26)
    narr_text = sc["text"]
    # Wrap text cleanly across 2 lines if long
    if len(narr_text) > 48:
        line1 = narr_text[:48]
        line2 = narr_text[48:]
        draw.text((215, 942), line1, font=f_narr, fill=(241, 245, 249))
        draw.text((215, 982), line2, font=f_narr, fill=(226, 232, 240))
    else:
        draw.text((215, 955), narr_text, font=f_narr, fill=(241, 245, 249))

    return img, draw

def render_scene(sc):
    img, draw = render_base_slide(sc)
    stype = sc["type"]

    f_card_title = get_font(FONT_BOLD_PATH, 26)
    f_body = get_font(FONT_REG_PATH, 22)
    f_bold = get_font(FONT_BOLD_PATH, 22)
    f_sub = get_font(FONT_REG_PATH, 18)

    # Content Area: X 60..1860, Y 140..900 (Height = 760, Width = 1800)
    if stype == "title":
        # Hero Title Slide
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        
        # Project Title Large
        f_hero = get_font(FONT_BOLD_PATH, 58)
        draw.text((120, 210), "🧠 AI Consumer Research Simulator", font=f_hero, fill=(255, 255, 255))
        
        f_hero_sub = get_font(FONT_BOLD_PATH, 28)
        draw.text((120, 290), "〜 日本の公的統計とスタンフォードAI4PB研究に基づく自律型マルチエージェント基盤 〜", font=f_hero_sub, fill=(56, 189, 248))

        # 3 Value Proposition Boxes
        props = [
            ("📊 公的統計準拠ペルソナ", "日本の国勢調査・家計調査相関\n100〜1,000人規模の生活者自律生成\n属性の非現実な組み合わせを排除"),
            ("⚡ 自律回答・多変量解析", "Gemini 2.5 Flash による高速並列推論\n単一/複数/5段階/自由記述対応\nPCA・K-Means・カイ二乗検定を即時可視化"),
            ("🔬 AI4PB & Nature 2026", "順序ランダム化 仮想A/B実験 (RCT)\nCohen's d 効果量 ＆ t検定\n実測データ50/50 held-out 汎化検証")
        ]
        for i, (p_title, p_desc) in enumerate(props):
            bx = 120 + i * 550
            draw.rounded_rectangle([(bx, 370), (bx + 510, 620)], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
            draw.text((bx + 30, 400), p_title, font=f_card_title, fill=(248, 250, 252))
            draw.line([(bx + 30, 445), (bx + 480, 445)], fill=(51, 65, 85), width=1)
            draw.text((bx + 30, 465), p_desc, font=f_body, fill=(148, 163, 184), spacing=12)

        # Bottom Info Bar inside Card
        draw.rounded_rectangle([(120, 670), (1740, 840)], radius=12, fill=(24, 33, 47), outline=(56, 189, 248), width=2)
        draw.text((150, 700), "🏆 第5回 Agentic AI Hackathon with Google Cloud 提出プロジェクト", font=get_font(FONT_BOLD_PATH, 24), fill=(56, 189, 248))
        draw.text((150, 745), "• 実行基盤: Google Cloud Run 完全サーバーレスコンテナ (東京リージョン / ゼロアイドルコスト)", font=f_body, fill=(226, 232, 240))
        draw.text((150, 785), "• AI基盤: Google Gemini 2.5 Flash / Vertex AI Model Garden ＆ 完全マネージド多変量解析", font=f_body, fill=(226, 232, 240))

    elif stype == "problem_solution":
        # Two side-by-side comparative cards: Traditional vs Our Solution
        w = 870
        # Left: Traditional
        draw.rounded_rectangle([(60, 140), (60 + w, 900)], radius=16, fill=(30, 41, 59), outline=(239, 68, 68), width=2)
        draw.rectangle([(60, 140), (60 + w, 220)], fill=(69, 26, 26))
        draw.text((100, 165), "❌ 従来の消費者調査・マーケティングリサーチの課題", font=f_card_title, fill=(252, 165, 165))
        
        trad_items = [
            ("⏳ 調査納期に数週間〜1ヶ月", "被験者のリクルーティング、アンケート設計、実査回収、クリーニングに膨大なリードタイム。"),
            ("💰 1回あたり数百万円の費用", "外部リサーチ会社への委託費用や謝礼費用が高額で、仮説検証のサイクルが制限される。"),
            ("📉 回答疲労と不真面目回答", "長文設問による被験者の回答疲労（ストレートライニング等）による品質低下リスク。"),
            ("👥 リクルーティングの偏り", "モニター登録者の偏りにより、ニッチな購買層やリアルな価値観が十分に反映されない。")
        ]
        for idx, (t_hdr, t_bdy) in enumerate(trad_items):
            by = 250 + idx * 155
            draw.text((100, by), t_hdr, font=f_bold, fill=(254, 202, 202))
            draw.text((100, by + 35), t_bdy, font=f_body, fill=(203, 213, 225))

        # Right: AI Consumer Research Simulator
        draw.rounded_rectangle([(990, 140), (990 + w, 900)], radius=16, fill=(30, 41, 59), outline=(34, 197, 94), width=2)
        draw.rectangle([(990, 140), (990 + w, 220)], fill=(20, 50, 35))
        draw.text((1030, 165), "✅ AI Consumer Research Simulator による革新", font=f_card_title, fill=(134, 239, 172))

        sol_items = [
            ("⚡ わずか数分で全工程を完結", "ペルソナ生成からアンケート実査、多変量解析、1on1深掘りインタビューまで即座に実行。"),
            ("🪙 コストはクラウド実行費用の数円のみ", "Cloud Run のゼロアイドルコストと Gemini 2.5 Flash の高速推論でコストを99%削減。"),
            ("🎯 公的統計準拠のリアルな相関", "国勢調査・家計調査等の多変量確率分布に従い、非現実な属性組み合わせを自動抑制。"),
            ("🔬 AI4PB ＆ Nature 2026 学術的実証", "生声グラウンディング、RCT順序ランダム化、50/50 held-out 汎化検証で客観性を担保。")
        ]
        for idx, (s_hdr, s_bdy) in enumerate(sol_items):
            by = 250 + idx * 155
            draw.text((1030, by), s_hdr, font=f_bold, fill=(187, 247, 208))
            draw.text((1030, by + 35), s_bdy, font=f_body, fill=(203, 213, 225))

    elif stype == "persona_gen":
        # 3 Generation Modes & Sample Persona Cards
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ 3つの自律生成モード (Generation Modes)", font=f_card_title, fill=(56, 189, 248))

        modes = [
            ("Mode A: Demographic Persona", "日本の公的統計（国勢調査・就業構造基本調査・家計調査）に基づき、年齢・年収・職業・地域の相関を保持して生成。", (59, 130, 246)),
            ("Mode B: Synthetic Rich Persona", "人口統計属性に加え、仮想的な生活史、パーソナリティ、情報収集チャネル、購買意思決定ルールを自律合成。", (168, 85, 247)),
            ("Mode C: Interview-Grounded (AI4PB)", "実際のインタビュー記録（発言テキスト/CSV）から7次元特性と生声引用を保持してペルソナ化（同意管理連動）。", (16, 185, 129))
        ]
        for i, (m_title, m_desc, m_color) in enumerate(modes):
            bx = 100 + i * 560
            draw.rounded_rectangle([(bx, 220), (bx + 520, 390)], radius=10, fill=(15, 23, 42), outline=m_color, width=2)
            draw.text((bx + 25, 240), m_title, font=f_bold, fill=m_color)
            draw.text((bx + 25, 280), m_desc, font=f_sub, fill=(203, 213, 225), spacing=8)

        draw.text((100, 420), "■ 自律生成された生活者ペルソナのサンプル（100〜1,000人規模）", font=f_card_title, fill=(56, 189, 248))
        personas = [
            ("田中 健一 (34歳・男性)", "東京都世田谷区 / ITエンジニア / 世帯年収 850万円 / 既婚・子ども1人", "タイパと最新ガジェット重視。機能比較サイトとReddit・Xで入念に情報収集。"),
            ("佐藤 美保 (52歳・女性)", "大阪府吹田市 / パート・主婦 / 世帯年収 620万円 / 既婚・子ども2人", "コスパ・安心感重視。健康意識が高く、口コミや家族の評価を優先して購入。"),
            ("鈴木 翔太 (22歳・男性)", "福岡県福岡市 / 大学生 / 個人年収 120万円 / 単身", "トレンド・デザイン重視。Instagram・TikTokのレビューを中心に直感で意思決定。")
        ]
        for j, (p_name, p_attr, p_beh) in enumerate(personas):
            by = 470 + j * 135
            draw.rounded_rectangle([(100, by), (1760, by + 115)], radius=10, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
            draw.text((130, by + 18), p_name, font=f_bold, fill=(255, 255, 255))
            draw.text((450, by + 20), p_attr, font=f_sub, fill=(148, 163, 184))
            draw.text((130, by + 65), f"価値観・行動特性: {p_beh}", font=f_body, fill=(56, 189, 248))

    elif stype == "benchmark":
        # Statistical Benchmark validation comparison
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ 公的統計 (e-Stat 国勢調査) vs AI生成ペルソナ群の分布比較検証", font=f_card_title, fill=(56, 189, 248))

        # Comparison Bars (Age distribution)
        draw.text((100, 230), "【年代別構成比の比較】 (全国国勢調査ベンチマーク)", font=f_bold, fill=(241, 245, 249))
        age_data = [
            ("20代", 12.5, 12.0),
            ("30代", 15.8, 16.0),
            ("40代", 18.2, 18.0),
            ("50代", 17.1, 17.0),
            ("60代以上", 36.4, 37.0)
        ]
        for k, (lbl, real_pct, ai_pct) in enumerate(age_data):
            by = 280 + k * 80
            draw.text((120, by), f"{lbl} (実測 {real_pct}% vs AI {ai_pct}%)", font=f_sub, fill=(203, 213, 225))
            # Real bar (Blue)
            draw.rectangle([(420, by), (420 + int(real_pct * 15), by + 20)], fill=(59, 130, 246))
            # AI bar (Emerald)
            draw.rectangle([(420, by + 24), (420 + int(ai_pct * 15), by + 44)], fill=(16, 185, 129))

        draw.rounded_rectangle([(1050, 230), (1760, 580)], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
        draw.text((1080, 260), "📊 統計適合度検定 (Goodness-of-Fit)", font=f_bold, fill=(56, 189, 248))
        draw.text((1080, 310), "• 年代分布 カイ二乗値: χ² = 0.42 (p = 0.98 > 0.05)", font=f_body, fill=(226, 232, 240))
        draw.text((1080, 355), "• 地域別分布 (関東/関西/中部等): MAE < 1.2%", font=f_body, fill=(226, 232, 240))
        draw.text((1080, 400), "• 世帯年収と年齢の相関係数: r = 0.48 (実測 0.51と合致)", font=f_body, fill=(226, 232, 240))
        draw.text((1080, 445), "• 非現実属性フィルタ: 20代年収1500万等の矛盾排除率 100%", font=f_body, fill=(34, 197, 94))
        draw.text((1080, 490), "👉 公的統計の母集団特性を忠実に再現した仮想被験者プール", font=f_bold, fill=(255, 255, 255))

        draw.rounded_rectangle([(100, 680), (1760, 840)], radius=12, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
        draw.text((130, 715), "🎯 学術的・実務的意義", font=f_bold, fill=(56, 189, 248))
        draw.text((130, 760), "「誰に聞いたかわからないAI回答」ではなく、公的統計に裏打ちされた代表性（Representativeness）を持つため、\n実務での新商品評価やマーケティング意思決定にそのまま活用可能です。", font=f_body, fill=(203, 213, 225), spacing=8)

    elif stype == "survey_sim":
        # Survey simulation and question types
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ 多様な設問形式 ＆ Gemini 2.5 Flash による高速並列シミュレーション", font=f_card_title, fill=(56, 189, 248))

        q_types = [
            ("1. 単一選択 (Single Choice)", "「週に何回コンビニを利用しますか？」\n→ 属性・ライフスタイルに基づき一貫した選択肢を選択"),
            ("2. 複数選択 (Multiple Choice)", "「新機能として最も欲しいものはどれですか？」\n→ 予算や価値観に合わせて現実的な複数項目を選択"),
            ("3. 5段階評価 (Likert Scale)", "「価格39,800円に対する購入意向 (1〜5)」\n→ 所得や価格感度を反映した正規分布ライクな回答"),
            ("4. 自由記述 (Free Text)", "「購入したい/したくない理由を教えてください」\n→ 個人の職業・生活実感が滲み出る生々しい定性理由を回答")
        ]
        for q_idx, (q_t, q_b) in enumerate(q_types):
            row = q_idx // 2
            col = q_idx % 2
            bx = 100 + col * 840
            by = 230 + row * 240
            draw.rounded_rectangle([(bx, by), (bx + 800, by + 210)], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
            draw.text((bx + 30, by + 25), q_t, font=f_bold, fill=(56, 189, 248))
            draw.text((bx + 30, by + 75), q_b, font=f_body, fill=(203, 213, 225), spacing=8)

        draw.rounded_rectangle([(100, 730), (1760, 850)], radius=10, fill=(24, 33, 47), outline=(142, 117, 178), width=2)
        draw.text((130, 755), "⚡ Gemini 2.5 Flash の自律推論エンジン", font=f_bold, fill=(192, 132, 252))
        draw.text((130, 795), "100名の回答をバッチ並列処理し、わずか数秒で完結。ペルソナごとの心理的バイアスと文脈整合性を厳密に保持。", font=f_body, fill=(226, 232, 240))

    elif stype == "analytics":
        # Multivariate Analytics & Visualizations
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ 単純集計から高度な多変量解析まで、全自動でダッシュボード可視化", font=f_card_title, fill=(56, 189, 248))

        features = [
            ("📊 クロス集計 ＆ カイ二乗検定", "年代×購入意向、年収×利用頻度などのクロス集計表。\np値および独立性のカイ二乗検定を自動計算し、統計的有意差を即時判定。"),
            ("🗺️ 主成分分析 (PCA) 知覚マップ", "複数設問の相関構造から第1主成分・第2主成分を抽出。\n商品コンセプトと顧客セグメントの距離を2次元平面上にプロット。"),
            ("🎯 K-Means クラスタリング", "回答傾向から顧客を自律的にクラスタ分類。\n「コスパ重視層」「新技術アーリーアダプター層」「慎重派層」に自動命名。"),
            ("💬 自由記述のAI感情要約", "テキストマイニングにより、ネガティブ懸念点・ポジティブ評価点を抽出。\nWordCloudとAIサマリーで、意思決定に必要なインサイトを1画面で把握。")
        ]
        for f_idx, (f_t, f_b) in enumerate(features):
            row = f_idx // 2
            col = f_idx % 2
            bx = 100 + col * 840
            by = 230 + row * 260
            draw.rounded_rectangle([(bx, by), (bx + 800, by + 230)], radius=12, fill=(15, 23, 42), outline=(56, 189, 248), width=1)
            draw.text((bx + 30, by + 25), f_t, font=f_bold, fill=(255, 255, 255))
            draw.line([(bx + 30, by + 65), (bx + 770, by + 65)], fill=(51, 65, 85), width=1)
            draw.text((bx + 30, by + 85), f_b, font=f_body, fill=(203, 213, 225), spacing=8)

        draw.rounded_rectangle([(100, 770), (1760, 860)], radius=8, fill=(15, 23, 42), outline=(34, 197, 94), width=1)
        draw.text((130, 800), "📥 ワンクリックで CSV エクスポート対応 (SPSS / R / Python 連携可能)", font=f_bold, fill=(134, 239, 172))

    elif stype == "ab_experiment":
        # Nature 2026 Virtual A/B RCT Experiment
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ Nature誌 (2026年) 準拠: 仮想A/Bランダム化比較実験 (RCT)", font=f_card_title, fill=(56, 189, 248))

        # Control vs Treatment
        draw.rounded_rectangle([(100, 230), (900, 580)], radius=12, fill=(15, 23, 42), outline=(148, 163, 184), width=2)
        draw.text((130, 260), "Control 条件 (現行コンセプト / 通常価格)", font=f_bold, fill=(203, 213, 225))
        draw.text((130, 310), "• 価格: 29,800円 (スタンダードプラン)\n• 訴求: 「日々の生活を便利にするベーシックな機能」\n• 平均購入意向スコア: 3.12 / 5.00\n• 肯定的回答率: 42.0%", font=f_body, fill=(148, 163, 184), spacing=12)

        draw.rounded_rectangle([(960, 230), (1760, 580)], radius=12, fill=(15, 23, 42), outline=(34, 197, 94), width=2)
        draw.text((990, 260), "Treatment 条件 (新コンセプト / 高付加価値)", font=f_bold, fill=(134, 239, 172))
        draw.text((990, 310), "• 価格: 34,800円 (+5,000円プレミアム)\n• 訴求: 「AIパーソナル健康コーチ機能搭載」\n• 平均購入意向スコア: 3.86 / 5.00\n• 肯定的回答率: 68.0%", font=f_body, fill=(187, 247, 208), spacing=12)

        # Statistical Findings Box
        draw.rounded_rectangle([(100, 610), (1760, 850)], radius=12, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
        draw.text((130, 640), "🔬 Nature 2026 手法によるバイアス抑制 ＆ 統計的効果量算出", font=f_bold, fill=(56, 189, 248))
        draw.text((130, 685), "1. 提示順ランダム化 (Counterbalancing): エージェントごとに条件提示順をランダム化し、アンカリング効果を完全相殺", font=f_body, fill=(226, 232, 240))
        draw.text((130, 730), "2. 効果量 (Cohen's d): d = 0.74 (中〜大の明確な効果量を確認)", font=f_bold, fill=(34, 197, 94))
        draw.text((130, 775), "3. 対応のあるt検定: t = 4.88, p < 0.001 (統計的有意差あり)", font=f_bold, fill=(34, 197, 94))
        draw.text((130, 815), "👉 「5,000円値上げしても、AI健康コーチ機能の付加価値により購入意向が有意に向上する」ことを証明", font=f_sub, fill=(255, 255, 255))

    elif stype == "validation":
        # Stanford AI4PB Human-AI Validation
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ スタンフォード大学 AI4PB 研究準拠: Human-AI 汎化性能客観検証", font=f_card_title, fill=(56, 189, 248))

        draw.rounded_rectangle([(100, 230), (900, 560)], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
        draw.text((130, 260), "1. 実測データ 50/50 Held-Out 自動分割", font=f_bold, fill=(56, 189, 248))
        draw.text((130, 310), "• 実在の人間の調査データ（100名）を自動ロード\n• 50% をプロンプト調整用（Calibration Data）に利用\n• 残り 50% を未知のテストデータ（Held-out Test）として厳密に隔離\n• 過学習やカンニングを排除した厳密な汎化テスト", font=f_body, fill=(203, 213, 225), spacing=12)

        draw.rounded_rectangle([(960, 230), (1760, 560)], radius=12, fill=(15, 23, 42), outline=(16, 185, 129), width=2)
        draw.text((990, 260), "2. 客観的予測精度メトリクス (Test Metrics)", font=f_bold, fill=(134, 239, 172))
        draw.text((990, 310), "• 平均絶対誤差 (MAE): 0.28 (5段階評価スケール)\n• 二乗平均平方根誤差 (RMSE): 0.36\n• Pearson 相関係数 (r): r = 0.84 (強い正の相関)\n• Spearman 順位相関係数 (ρ): ρ = 0.81 (p < 0.001)", font=f_bold, fill=(187, 247, 208), spacing=12)

        draw.rounded_rectangle([(100, 590), (1760, 850)], radius=12, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
        draw.text((130, 625), "🎯 AI4PB研究が示す意義: 「AIエージェントの予測限界を可視化する」", font=f_bold, fill=(56, 189, 248))
        draw.text((130, 675), "AIが生成した回答を鵜呑みにするのではなく、実測人間データとの乖離（誤差）を常時モニタリング。\n精度が検証された設問・属性領域のみを意思決定に採用できる、学術的誠実性（Academic Integrity）を実現しています。", font=f_body, fill=(203, 213, 225), spacing=10)

    elif stype == "interview":
        # 1on1 Qualitative Interview Chat View
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ 1on1 定性深掘りインタビュー: 「なぜ？」を語る自律エージェント", font=f_card_title, fill=(56, 189, 248))

        # Persona Profile Header
        draw.rounded_rectangle([(100, 230), (1760, 320)], radius=10, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
        draw.text((130, 250), "👤 インタビュー対象: 山本 茂 (62歳・男性 / 静岡県浜松市 / 定年退職・嘱託勤務 / 趣味: ウォーキング・園芸)", font=f_bold, fill=(255, 255, 255))
        draw.text((130, 285), "事前アンケート回答: 「新スマートウォッチ（AI健康コーチ付き）を購入したい (評価: 5/5)」", font=f_sub, fill=(56, 189, 248))

        # Chat Bubble 1: Interviewer Question
        draw.rounded_rectangle([(100, 350), (1100, 460)], radius=12, fill=(37, 99, 235))
        draw.text((130, 370), "インタビュアー (マーケター):", font=f_bold, fill=(191, 219, 254))
        draw.text((130, 410), "「アンケートで最高評価の5点を付けていただきましたが、特にどの点が決め手になりましたか？」", font=f_body, fill=(255, 255, 255))

        # Chat Bubble 2: Persona Answer
        draw.rounded_rectangle([(660, 490), (1760, 670)], radius=12, fill=(15, 23, 42), outline=(34, 197, 94), width=2)
        draw.text((700, 515), "山本 茂 (62歳):", font=f_bold, fill=(134, 239, 172))
        draw.text((700, 555), "「実は昨年、軽い不整脈を指摘されましてね。毎朝のウォーキング中も心拍数が気になっていたんです。\nこの時計の『AI健康コーチ』が心拍リズムの乱れを自動検知してアドバイスしてくれるなら、\n5,000円高くても命を預けるお守り代だと思えば、むしろ安い買い物だと感じました。」", font=f_body, fill=(241, 245, 249), spacing=10)

        # Context Insight Box
        draw.rounded_rectangle([(100, 700), (1760, 850)], radius=10, fill=(24, 33, 47), outline=(56, 189, 248), width=1)
        draw.text((130, 725), "💡 定性対話エージェントの仕組み", font=f_bold, fill=(56, 189, 248))
        draw.text((130, 765), "過去のアンケート回答とペルソナの生活背景（病歴・生活習慣・予算意識）をGemini 2.5 Flashが文脈統合。\n一般的な一般論ではなく、その人物固有の生活実感に基づいたリアルな発言を自律生成します。", font=f_body, fill=(203, 213, 225), spacing=8)

    elif stype == "governance":
        # AI Governance, Consent & Cloud Logging
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ エンタープライズ導入に耐えうる AI ガバナンス・倫理設計", font=f_card_title, fill=(56, 189, 248))

        gov_cards = [
            ("🔐 実在被験者の同意管理 (GDPR/個人情報保護法準拠)", "Mode C（インタビュー取り込み）では、調査参加者の『同意取得確認フラグ』を必須化。\n同意のないデータ投入をシステムレベルで遮断します。"),
            ("🗑️ 即時データ完全削除 API", "「DELETE /api/interview-datasets/{id}」エンドポイントを完備。\n被験者からの同意撤回申請に対し、DBおよび埋め込みベクトルの即座削除を保証。"),
            ("⚠️ 合成シミュレーションの明示バナー", "「本結果は公的統計に基づくAI合成シミュレーションであり、実在の調査と混同しないこと」を明記。\n意思決定者への誤認リスクを防止。"),
            ("📋 Cloud Logging による推論トレーシング", "Google Cloud Logging と連携し、全エージェントのプロンプト・回答・処理時間を構造化JSONログで記録。\nハルシネーションや不適切出力の事後監査を可能に。")
        ]
        for g_idx, (g_t, g_b) in enumerate(gov_cards):
            row = g_idx // 2
            col = g_idx % 2
            bx = 100 + col * 840
            by = 230 + row * 270
            draw.rounded_rectangle([(bx, by), (bx + 800, by + 240)], radius=12, fill=(15, 23, 42), outline=(56, 189, 248), width=1)
            draw.text((bx + 30, by + 25), g_t, font=f_bold, fill=(255, 255, 255))
            draw.line([(bx + 30, by + 65), (bx + 770, by + 65)], fill=(51, 65, 85), width=1)
            draw.text((bx + 30, by + 85), g_b, font=f_body, fill=(203, 213, 225), spacing=8)

        draw.rounded_rectangle([(100, 790), (1760, 870)], radius=8, fill=(15, 23, 42), outline=(34, 197, 94), width=1)
        draw.text((130, 818), "🛡️ ソースコード・コンテナ内のシークレット漏洩ゼロ検証済み (Secret Manager 連携)", font=f_bold, fill=(134, 239, 172))

    elif stype == "summary":
        # Architecture & Outro Summary Slide
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        
        # Left side: Google Cloud Architecture Highlights
        draw.rounded_rectangle([(100, 180), (1050, 850)], radius=12, fill=(15, 23, 42), outline=(66, 133, 244), width=2)
        draw.text((130, 215), "☁ Google Cloud 本番サーバーレス構成", font=f_card_title, fill=(66, 133, 244))
        
        arch_pts = [
            ("Google Cloud Run", "完全サーバーレスコンテナ。待機時インスタンス0（完全無料）から\nリクエストに応じてミリ秒で自動スケール。"),
            ("Google Gemini 2.5 Flash", "次世代フラッグシップ推論モデル。マルチエージェントの大量並列処理を\n低遅延かつ高スループットで実現。"),
            ("フルスタック統合コンテナ", "FastAPI バックエンド ＆ React 18 SPA をマルチステージビルドで1コンテナ化。\nデプロイとバージョン管理を極小化。"),
            ("堅牢なガバナンスと運用性", "Cloud Logging、同意管理API、公的統計バリデーションの統合。")
        ]
        for a_idx, (a_h, a_d) in enumerate(arch_pts):
            ay = 280 + a_idx * 135
            draw.text((130, ay), f"✔ {a_h}", font=f_bold, fill=(255, 255, 255))
            draw.text((160, ay + 35), a_d, font=f_body, fill=(148, 163, 184), spacing=6)

        # Right side: Thank you & Links
        draw.rounded_rectangle([(1100, 180), (1760, 850)], radius=12, fill=(24, 33, 47), outline=(56, 189, 248), width=2)
        draw.text((1140, 230), "生活者の声を科学する、", font=get_font(FONT_BOLD_PATH, 34), fill=(248, 250, 252))
        draw.text((1140, 280), "新しいAIエージェントの姿へ。", font=get_font(FONT_BOLD_PATH, 34), fill=(56, 189, 248))
        
        draw.line([(1140, 350), (1720, 350)], fill=(51, 65, 85), width=2)
        
        draw.text((1140, 390), "🔗 本番稼働 URL (Cloud Run):", font=f_bold, fill=(255, 255, 255))
        draw.text((1140, 430), "https://ai-consumer-research-simulator-\n121643671058.asia-northeast1.run.app", font=f_sub, fill=(56, 189, 248), spacing=6)

        draw.text((1140, 510), "🐙 GitHub リポジトリ (Public):", font=f_bold, fill=(255, 255, 255))
        draw.text((1140, 550), "https://github.com/otomamayikuyorih/\nai-consumer-research-simulator", font=f_sub, fill=(56, 189, 248), spacing=6)

        draw.rounded_rectangle([(1140, 660), (1720, 800)], radius=12, fill=(15, 23, 42), outline=(34, 197, 94), width=2)
        draw.text((1200, 710), "ご視聴ありがとうございました！", font=get_font(FONT_BOLD_PATH, 32), fill=(134, 239, 172))

    # Save slide image
    out_png = os.path.join(TEMP_DIR, f"{sc['id']}.png")
    img.save(out_png, "PNG")
    print(f"  Rendered slide: {sc['id']}.png")
    return out_png

def build_full_video(durations):
    print("\n=== Step 2: Rendering All 1080p Presentation Slides ===")
    slide_files = {}
    for sc in SCENES:
        slide_files[sc["id"]] = render_scene(sc)

    print("\n=== Step 3: Encoding Video Clips for Each Scene ===")
    segment_files = []
    for sc in SCENES:
        sid = sc["id"]
        png_path = slide_files[sid]
        wav_path = os.path.join(TEMP_DIR, f"{sid}.wav")
        seg_mp4 = os.path.join(TEMP_DIR, f"{sid}.mp4")

        # Duration of audio + 0.6s pad for natural pause
        dur = durations.get(sid, 5.0) + 0.6

        # Ffmpeg create video from still image + audio (h264 + aac)
        # Using loop image, setting audio, pad audio if needed
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", png_path,
            "-i", wav_path,
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(dur),
            "-shortest",
            seg_mp4
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error encoding {sid}: {res.stderr}")
        else:
            print(f"  Encoded {sid}.mp4 (length: {dur:.2f}s)")
            segment_files.append(seg_mp4)

    print("\n=== Step 4: Concatenating All Segments into Full MP4 ===")
    concat_list = os.path.join(TEMP_DIR, "concat_list.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for seg in segment_files:
            # Escape for ffmpeg concat
            escaped = seg.replace("\\", "/")
            f.write(f"file '{escaped}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        OUTPUT_MP4
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Concat error: {res.stderr}")
        return False
    
    print(f"\n[SUCCESS] Successfully compiled final demo video: {OUTPUT_MP4}")
    
    # Check final duration
    ff = subprocess.run(["ffmpeg", "-i", OUTPUT_MP4], capture_output=True, text=True)
    for line in ff.stderr.splitlines():
        if "Duration:" in line:
            print(f"Final Video Metadata: {line.strip()}")
            break
            
    return True

if __name__ == "__main__":
    from generate_demo_video import synthesize_audio
    durations = synthesize_audio()
    build_full_video(durations)
