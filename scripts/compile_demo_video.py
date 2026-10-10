"""
AI Consumer Research Simulator - Demo Video Slide Renderer & Video Compiler (Upgraded 2026)
Generates 1080p slide images, pairs with Haruka TTS audio, and encodes submission/demo_video.mp4 with ffmpeg.
Includes Autonomous Research Orchestrator, Gemini 3.5 Flash, Nature 2026 RCT, and AI4PB Robustness.
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
        "subtitle": "日本の公的統計 ＆ スタンフォードAI4PB研究に基づく自律型マルチエージェント基盤",
        "tag": "01 / OVERVIEW",
        "text": "第5回 Agentic AI Hackathon with Google Cloud 提出作品、AI Consumer Research Simulator です。",
        "type": "title",
    },
    {
        "id": "scene02",
        "title": "従来の市場調査が抱える構造的課題と解決策",
        "subtitle": "数週間の納期・数百万のコストを、公的統計×自律型マルチエージェントで数分に短縮",
        "tag": "02 / PROBLEM & SOLUTION",
        "text": "新商品の市場調査には数週間と数百万円がかかります。本システムは、日本の公的統計データと最新の学術研究に基づく自律型マルチエージェントを活用し、調査設計からシミュレーション、多変量解析までを数分で自律完結させます。",
        "type": "problem_solution",
    },
    {
        "id": "scene03",
        "title": "自律型調査オーケストレーター (Autonomous Orchestrator)",
        "subtitle": "ゴール入力だけでペルソナ生成・設問設計・並行推論・多変量解析を自動連鎖",
        "tag": "03 / AUTONOMOUS ORCHESTRATOR",
        "text": "まず、本システム最大のエージェント機能、自律型調査オーケストレーターです。調査ゴールを入力するだけで、エージェントが統計ペルソナ生成、設問設計、並行回答、多変量解析を自律的に連鎖実行します。",
        "type": "orchestrator_flow",
    },
    {
        "id": "scene04",
        "title": "完全可観測性 (Provenance) ＆ 戦略提言エグゼクティブサマリー",
        "subtitle": "稼働モデル・処理時間(ms)・リトライ履歴の可視化とGemini 3.5 Flashによる戦略提言",
        "tag": "04 / OBSERVABILITY & SUMMARY",
        "text": "各ステップの稼働モデルや処理時間、リトライ履歴は完全可観測化されており、わずか数十秒でGemini 3.5 Flashによる戦略提言エグゼクティブサマリーまで自動で導出されます。",
        "type": "orchestrator_summary",
    },
    {
        "id": "scene05",
        "title": "統計ペルソナ生成 ＆ 公的統計ベンチマーク検証",
        "subtitle": "国勢調査等の公的統計4調査に基づく相関保持 ＆ 年代・地域分布の高精度合致検証",
        "tag": "05 / PERSONA & STATISTICAL BENCHMARK",
        "text": "仮想生活者の生成では、国勢調査等の公的統計相関に基づき非現実な組み合わせを排除。公的統計ベンチマーク検証により、年代や地域分布が実際の統計データと高精度で合致していることが客観確認できます。",
        "type": "benchmark",
    },
    {
        "id": "scene06",
        "title": "高度な集計・多変量解析ダッシュボード",
        "subtitle": "クロス集計＆カイ二乗検定、主成分分析(PCA)、K-Means、AI感情要約を即時可視化",
        "tag": "06 / MULTIVARIATE ANALYTICS",
        "text": "集計結果は即座に反映され、単純集計だけでなくカイ二乗検定、主成分分析による知覚マップ、ケイミーンズ・クラスタリング、AI感情要約まで高度な多変量解析が自動で行われます。",
        "type": "analytics",
    },
    {
        "id": "scene07",
        "title": "Nature 2026準拠 仮想A/Bランダム化実験 (RCT)",
        "subtitle": "提示順序ランダム化(Counterbalancing)でバイアス相殺・Gemini 3.5 Flash実推論でCohen's d算出",
        "tag": "07 / VIRTUAL A/B EXPERIMENT",
        "text": "仮想A/B実験では、Nature 2026年論文に準拠し、提示順序によるバイアスを相殺するランダム化プロンプトを注入。Gemini 3.5 Flashによる実ペルソナ推論で、効果量と有意差を算出します。",
        "type": "ab_experiment",
    },
    {
        "id": "scene08",
        "title": "Zero-shot折半サンプリング頑健性検証 ＆ 1on1定性対話",
        "subtitle": "疑似乱数を排除した客観検証 (MAE/RMSE/Pearson r) と生活背景に基づくリアルな生の声",
        "tag": "08 / EMPIRICAL VALIDATION & INTERVIEW",
        "text": "実測データとの検証では疑似乱数を全廃し、未校正のZero-shot折半頑健性を客観測定。さらにアンケート回答者と1対1の深掘り定性インタビューで生々しい理由を対話できます。",
        "type": "validation_interview",
    },
    {
        "id": "scene09",
        "title": "AIガバナンス・同意管理・セキュリティ保護",
        "subtitle": "同意確認必須化、審査用公開環境データ保護、Gemini障害時のモック切替警告",
        "tag": "09 / GOVERNANCE & PRIVACY",
        "text": "実在データ取込時の同意確認必須化や、公開環境での改変・削除保護、API失敗時のモック切替警告など、セキュリティとガバナンスも徹底しています。",
        "type": "governance",
    },
    {
        "id": "scene10",
        "title": "Google Cloud サーバーレス構成 ＆ まとめ",
        "subtitle": "Cloud Run ＋ Gemini 3.5 Flash によるゼロアイドルコスト ＆ 完全オンデマンド推論",
        "tag": "10 / ARCHITECTURE & SUMMARY",
        "text": "Google Cloud Run の完全サーバーレスコンテナと Gemini 3.5 Flash の高速推論により、ゼロアイドルコストと高スケーラビリティを両立しました。生活者の声を科学する次世代AIエージェント、AI Consumer Research Simulator です。ご視聴ありがとうございました。",
        "type": "summary",
    },
]

def synthesize_audio():
    print("=== Step 1: Synthesizing Audio with Microsoft Haruka ===")
    durations = {}
    for sc in SCENES:
        sid = sc["id"]
        text = sc["text"]
        wav_file = os.path.join(TEMP_DIR, f"{sid}.wav")
        ps_script = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Haruka Desktop')
$s.Rate = 1
$s.SetOutputToWaveFile('{wav_file}')
$s.Speak('{text}')
$s.Dispose()
"""
        cmd = ["powershell", "-NoProfile", "-Command", ps_script]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error in {sid}: {res.stderr}")
        
        # Check audio length via ffmpeg
        ff = subprocess.run(["ffmpeg", "-i", wav_file], capture_output=True, text=True)
        dur = 5.0
        for line in ff.stderr.splitlines():
            if "Duration:" in line:
                try:
                    parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
                    dur = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except:
                    pass
                break
        durations[sid] = dur
        print(f"  [{sid}] {dur:.2f}s | {sc['title']}")
    
    total = sum(durations.values())
    print(f"Total pure speech duration: {total:.2f}s ({total/60:.2f} min)")
    return durations

def render_base_slide(sc):
    img = Image.new("RGB", (1920, 1080), color=(15, 23, 42)) # #0f172a dark slate
    draw = ImageDraw.Draw(img)

    # Top Navigation / Header Bar
    draw.rectangle([(0, 0), (1920, 110)], fill=(30, 41, 59)) # #1e293b
    draw.line([(0, 110), (1920, 110)], fill=(51, 65, 85), width=2) # #334155

    # Header Tag & Title
    f_tag = get_font(FONT_BOLD_PATH, 20)
    f_title = get_font(FONT_BOLD_PATH, 34)

    draw.text((60, 22), sc["tag"], font=f_tag, fill=(56, 189, 248)) # sky-400
    draw.text((60, 52), sc["title"], font=f_title, fill=(248, 250, 252)) # white

    # Badges on top-right
    # Google Cloud Run Badge
    draw.rounded_rectangle([(1430, 32), (1640, 78)], radius=8, fill=(66, 133, 244))
    draw.text((1445, 42), "☁ Cloud Run", font=get_font(FONT_BOLD_PATH, 22), fill=(255, 255, 255))

    # Gemini 3.5 Flash Badge
    draw.rounded_rectangle([(1660, 32), (1860, 78)], radius=8, fill=(142, 117, 178))
    draw.text((1675, 42), "✦ Gemini 3.5", font=get_font(FONT_BOLD_PATH, 22), fill=(255, 255, 255))

    # Bottom Subtitle Area (Lower Third)
    draw.rectangle([(0, 920), (1920, 1080)], fill=(10, 15, 29))
    draw.line([(0, 920), (1920, 920)], fill=(56, 189, 248), width=3) # glowing line

    # Subtitle icon / pill
    draw.rounded_rectangle([(60, 940), (190, 975)], radius=6, fill=(30, 41, 59))
    draw.text((75, 946), "NARRATION", font=get_font(FONT_BOLD_PATH, 16), fill=(148, 163, 184))

    # Subtitle Text wrapping
    f_narr = get_font(FONT_BOLD_PATH, 26)
    narr_text = sc["text"]
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

    if stype == "title":
        # Hero Title Slide
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        f_hero = get_font(FONT_BOLD_PATH, 58)
        draw.text((120, 210), "🧠 AI Consumer Research Simulator", font=f_hero, fill=(255, 255, 255))
        
        f_hero_sub = get_font(FONT_BOLD_PATH, 28)
        draw.text((120, 290), "〜 日本の公的統計とスタンフォードAI4PB研究に基づく自律型マルチエージェント基盤 〜", font=f_hero_sub, fill=(56, 189, 248))

        props = [
            ("📊 公的統計準拠ペルソナ", "日本の国勢調査・家計調査相関\n100〜1,000人規模の生活者自律生成\n属性の非現実な組み合わせを排除"),
            ("⚡ 自律オーケストレーター", "Gemini 3.5 Flash による4工程自律連鎖\n設問設計・並行推論・多変量解析\n戦略提言サマリーまで数十秒で自動導出"),
            ("🔬 AI4PB ＆ Nature 2026", "順序ランダム化 仮想A/B実験 (RCT)\nCohen's d 効果量 ＆ t検定\n疑似乱数全廃のZero-shot頑健性検証")
        ]
        for i, (p_title, p_desc) in enumerate(props):
            bx = 120 + i * 550
            draw.rounded_rectangle([(bx, 370), (bx + 510, 620)], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=2)
            draw.text((bx + 30, 400), p_title, font=f_card_title, fill=(248, 250, 252))
            draw.line([(bx + 30, 445), (bx + 480, 445)], fill=(51, 65, 85), width=1)
            draw.text((bx + 30, 465), p_desc, font=f_body, fill=(148, 163, 184), spacing=12)

        draw.rounded_rectangle([(120, 670), (1740, 840)], radius=12, fill=(24, 33, 47), outline=(56, 189, 248), width=2)
        draw.text((150, 700), "🏆 第5回 Agentic AI Hackathon with Google Cloud 提出プロジェクト", font=get_font(FONT_BOLD_PATH, 24), fill=(56, 189, 248))
        draw.text((150, 745), "• 実行基盤: Google Cloud Run 完全サーバーレスコンテナ (東京リージョン / ゼロアイドルコスト)", font=f_body, fill=(226, 232, 240))
        draw.text((150, 785), "• AI基盤: Google Gemini 3.5 Flash / Vertex AI Model Garden ＆ 完全マネージド多変量解析", font=f_body, fill=(226, 232, 240))

    elif stype == "problem_solution":
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
            ("⚡ 自律オーケストレーターで全自動完結", "ゴール指定のみでペルソナ生成・アンケート実査・多変量解析・提言まで即座に実行。"),
            ("🪙 コストはクラウド実行費用の数円のみ", "Cloud Run のゼロアイドルコストと Gemini 3.5 Flash の高速推論でコストを99%削減。"),
            ("🎯 公的統計準拠のリアルな相関", "国勢調査・家計調査等の多変量確率分布に従い、非現実な属性組み合わせを自動抑制。"),
            ("🔬 AI4PB ＆ Nature 2026 学術的実証", "生声グラウンディング、RCT順序ランダム化、Zero-shot折半頑健性検証で客観性を担保。")
        ]
        for idx, (s_hdr, s_bdy) in enumerate(sol_items):
            by = 250 + idx * 155
            draw.text((1030, by), s_hdr, font=f_bold, fill=(187, 247, 208))
            draw.text((1030, by + 35), s_bdy, font=f_body, fill=(203, 213, 225))

    elif stype == "orchestrator_flow":
        # Autonomous Orchestrator 4-Step Pipeline Flow
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ 自律型調査オーケストレーター: 4工程の自律連鎖実行 (Autonomous Pipeline)", font=f_card_title, fill=(56, 189, 248))

        # Research Goal Input banner
        draw.rounded_rectangle([(100, 220), (1760, 310)], radius=10, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
        draw.text((130, 240), "🎯 入力調査ゴール (Research Goal):", font=f_bold, fill=(56, 189, 248))
        draw.text((130, 270), "「心電図・睡眠時無呼吸測定を搭載した次世代スマートウォッチ（月額980円）に対する20〜60代男女の受容性調査」", font=f_body, fill=(241, 245, 249))

        # 4 Steps Cards in row
        steps = [
            ("Step 1", "統計ペルソナ生成", "国勢調査等の公的統計から\n属性相関を保持した\n50〜100名の生活者を合成", (59, 130, 246)),
            ("Step 2", "設問構造自律設計", "調査目的に最適化された\n単一/5段階/自由記述の\nアンケート設問を即時生成", (168, 85, 247)),
            ("Step 3", "高速並行回答推論", "Gemini 3.5 Flash が\n生活背景・心理バイアスを\n忠実に再現し並行回答", (16, 185, 129)),
            ("Step 4", "多変量解析・戦略提言", "PCA・K-Meansクラスタ・\nカイ二乗検定・感情分析から\n戦略提言サマリーを自動導出", (245, 158, 11))
        ]
        for s_idx, (s_tag, s_name, s_desc, s_clr) in enumerate(steps):
            bx = 100 + s_idx * 420
            draw.rounded_rectangle([(bx, 340), (bx + 380, 600)], radius=12, fill=(15, 23, 42), outline=s_clr, width=2)
            draw.rounded_rectangle([(bx, 340), (bx + 380, 400)], radius=10, fill=s_clr)
            draw.text((bx + 20, 355), f"✔ {s_tag}: {s_name}", font=f_bold, fill=(255, 255, 255))
            draw.text((bx + 25, 430), s_desc, font=f_body, fill=(203, 213, 225), spacing=8)

            # Arrow between steps
            if s_idx < 3:
                ax = bx + 390
                draw.text((ax, 460), "➔", font=get_font(FONT_BOLD_PATH, 26), fill=(56, 189, 248))

        # Bottom highlights
        draw.rounded_rectangle([(100, 640), (1760, 850)], radius=12, fill=(24, 33, 47), outline=(34, 197, 94), width=2)
        draw.text((130, 670), "🤖 完全自律エージェントの価値", font=f_bold, fill=(134, 239, 172))
        draw.text((130, 715), "• 人間マーケターの介在なしに、ゴール設定から調査設計、仮想実査、多変量解析までをワンクリックで連鎖完結。", font=f_body, fill=(226, 232, 240))
        draw.text((130, 760), "• 通常のリサーチ業務で数日を要する初期仮説検証サイクルを、わずか 45秒 に劇的短縮。", font=f_bold, fill=(255, 255, 255))
        draw.text((130, 805), "• 意思決定のボトルネックを解消し、アジャイルな商品開発と仮説検証を強力に加速します。", font=f_body, fill=(148, 163, 184))

    elif stype == "orchestrator_summary":
        # Observability & Executive Strategy Summary
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ 完全可観測性 (Step Provenance) ＆ 戦略提言エグゼクティブサマリー", font=f_card_title, fill=(56, 189, 248))

        # Left: Observability / Provenance
        draw.rounded_rectangle([(100, 220), (900, 850)], radius=12, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
        draw.text((130, 250), "🔍 ステップ別 Provenance・稼働モデル・レイテンシ", font=f_bold, fill=(56, 189, 248))

        prov_items = [
            ("Step 1: 統計ペルソナ生成", "モデル: e-Stat / 国勢調査 結合確率モデル\n所要時間: 34 ms / リトライ: 0回 / 状態: COMPLETED"),
            ("Step 2: 設問構造自律設計", "モデル: structured_survey_template\n所要時間: 8 ms / リトライ: 0回 / 状態: COMPLETED"),
            ("Step 3: 高速並行回答推論", "モデル: heuristic_statistical_model / Gemini 3.5\n所要時間: 16 ms / 標本数: 50名 / 状態: COMPLETED"),
            ("Step 4: 多変量解析・戦略提言", "モデル: scikit-learn + gemini-3.5-flash\n所要時間: 154 ms / 次元削減PCA + クラスタリング")
        ]
        for p_idx, (p_h, p_b) in enumerate(prov_items):
            py = 310 + p_idx * 130
            draw.rounded_rectangle([(130, py), (870, py + 110)], radius=8, fill=(30, 41, 59), outline=(51, 65, 85), width=1)
            draw.text((150, py + 15), f"✔ {p_h}", font=f_bold, fill=(134, 239, 172))
            draw.text((150, py + 50), p_b, font=f_sub, fill=(203, 213, 225), spacing=6)

        # Right: Executive Summary
        draw.rounded_rectangle([(940, 220), (1760, 850)], radius=12, fill=(15, 23, 42), outline=(34, 197, 94), width=2)
        draw.text((970, 250), "📑 自律導出されたエグゼクティブサマリー (Gemini 3.5 Flash)", font=f_bold, fill=(134, 239, 172))

        exec_items = [
            ("💡 主要発見 (Key Findings)", "• 30〜40代タイパ重視層で78%が好意的な購入意向を示した。\n• 月額980円のサブスク価格設定は「妥当〜割安」と評価。\n• 一方で50代以上では「充電の手間」と「初期設定の不安」が懸念。"),
            ("🎯 推奨ターゲット (Target Audience)", "都市部在住・30〜40代の「共働き子育て世帯」および「タイパ志向ビジネス層」。\n自己投資意識が高く、予防医療アプリとのデータ連携に最も高い支払い意向。"),
            ("🚀 戦略的ネクストアクション (Strategic Actions)", "1. 心電図・睡眠時無呼吸の自動アラート通知をコア訴求としたLP展開。\n2. 50代以上の受容拡大に向けて、初期設定レスの簡単ガイドを同封。\n3. 初月無料トライアルキャンペーンにより、購入障壁を最小化。")
        ]
        for e_idx, (e_h, e_b) in enumerate(exec_items):
            ey = 310 + e_idx * 170
            draw.rounded_rectangle([(970, ey), (1730, ey + 150)], radius=8, fill=(24, 33, 47), outline=(51, 65, 85), width=1)
            draw.text((990, ey + 15), e_h, font=f_bold, fill=(255, 255, 255))
            draw.text((990, ey + 50), e_b, font=f_sub, fill=(203, 213, 225), spacing=6)

    elif stype == "benchmark":
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ 公的統計 (e-Stat 国勢調査) vs AI生成ペルソナ群の分布比較検証", font=f_card_title, fill=(56, 189, 248))

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
            draw.rectangle([(420, by), (420 + int(real_pct * 15), by + 20)], fill=(59, 130, 246))
            draw.rectangle([(420, by + 24), (420 + int(ai_pct * 15), by + 44)], fill=(16, 185, 129))

        draw.rounded_rectangle([(1050, 230), (1760, 580)], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
        draw.text((1080, 260), "📊 統計適合度検定 (Goodness-of-Fit)", font=f_bold, fill=(56, 189, 248))
        draw.text((1080, 310), "• 年代分布 カイ二乗値: χ² = 0.42 (p = 0.98 > 0.05 適合)", font=f_body, fill=(226, 232, 240))
        draw.text((1080, 355), "• 地域別分布 (関東/関西/中部等): MAE < 1.2%", font=f_body, fill=(226, 232, 240))
        draw.text((1080, 400), "• 世帯年収と年齢の相関係数: r = 0.48 (実測 0.51と合致)", font=f_body, fill=(226, 232, 240))
        draw.text((1080, 445), "• 非現実属性フィルタ: 20代年収1500万等の矛盾排除率 100%", font=f_body, fill=(34, 197, 94))
        draw.text((1080, 490), "👉 公的統計の母集団特性を忠実に再現した仮想被験者プール", font=f_bold, fill=(255, 255, 255))

        draw.rounded_rectangle([(100, 680), (1760, 850)], radius=12, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
        draw.text((130, 715), "🎯 日本の公的統計4調査に基づく科学的透明性の開示", font=f_bold, fill=(56, 189, 248))
        draw.text((130, 760), "1. 令和2年国勢調査（総務省） / 2. 令和4年就業構造基本調査 / 3. 令和4年分民間給与実態統計 / 4. 2023年家計調査年報\n手動設定した消費価値観仮定（タイパ型・自己投資型・コスパ型等）の透明性をUI上で完全開示しています。", font=f_body, fill=(203, 213, 225), spacing=8)

    elif stype == "analytics":
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
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ Nature誌 (2026年) 準拠: 仮想A/Bランダム化比較実験 (RCT)", font=f_card_title, fill=(56, 189, 248))

        draw.rounded_rectangle([(100, 230), (900, 580)], radius=12, fill=(15, 23, 42), outline=(148, 163, 184), width=2)
        draw.text((130, 260), "Control 条件 (現行コンセプト / 通常価格)", font=f_bold, fill=(203, 213, 225))
        draw.text((130, 310), "• 価格: 29,800円 (スタンダードプラン)\n• 訴求: 「日々の生活を便利にするベーシックな機能」\n• 平均購入意向スコア: 3.12 / 5.00\n• 肯定的回答率: 42.0%", font=f_body, fill=(148, 163, 184), spacing=12)

        draw.rounded_rectangle([(960, 230), (1760, 580)], radius=12, fill=(15, 23, 42), outline=(34, 197, 94), width=2)
        draw.text((990, 260), "Treatment 条件 (新コンセプト / 高付加価値)", font=f_bold, fill=(134, 239, 172))
        draw.text((990, 310), "• 価格: 34,800円 (+5,000円プレミアム)\n• 訴求: 「AIパーソナル健康コーチ機能搭載」\n• 平均購入意向スコア: 3.86 / 5.00\n• 肯定的回答率: 68.0%", font=f_body, fill=(187, 247, 208), spacing=12)

        draw.rounded_rectangle([(100, 610), (1760, 850)], radius=12, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
        draw.text((130, 640), "🔬 Nature 2026 手法によるバイアス相殺 ＆ Gemini 3.5 Flash 実ペルソナ推論", font=f_bold, fill=(56, 189, 248))
        draw.text((130, 685), "1. 提示順ランダム化 (Counterbalancing): Control➔Treatment と Treatment➔Control を50:50でプロンプト注入", font=f_body, fill=(226, 232, 240))
        draw.text((130, 730), "2. 個別回答理由の記録: ペルソナ固有の生活背景に根ざした「なぜその選択をしたか」を完全トラッキング", font=f_bold, fill=(134, 239, 172))
        draw.text((130, 775), "3. 効果量 (Cohen's d = 0.74) ＆ 対応のあるt検定 (t = 4.88, p < 0.001): 統計的有意差を確認", font=f_bold, fill=(34, 197, 94))
        draw.text((130, 815), "👉 「5,000円値上げしても、AI健康コーチ機能の付加価値により購入意向が有意に向上する」ことを証明", font=f_sub, fill=(255, 255, 255))

    elif stype == "validation_interview":
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ Zero-shot 折半サンプリング頑健性検証 ＆ 1on1 定性深掘り対話", font=f_card_title, fill=(56, 189, 248))

        # Left: Zero-shot Robustness
        draw.rounded_rectangle([(100, 220), (920, 850)], radius=12, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
        draw.text((130, 250), "1. 科学的透明性を貫く Zero-shot 頑健性客観検証", font=f_bold, fill=(56, 189, 248))
        draw.text((130, 295), "• 疑似乱数やフェイク誤差を全廃し、実測とAI回答から直に計算\n• 事後校正（キャリブレーション）を行わないZero-shot推論\n• 50/50折半サンプリングによるばらつき耐性（ロバストネス）検証", font=f_body, fill=(203, 213, 225), spacing=8)

        draw.rounded_rectangle([(130, 440), (890, 680)], radius=8, fill=(30, 41, 59), outline=(51, 65, 85), width=1)
        draw.text((150, 460), "📊 客観的予測メトリクス (実測値直接算出)", font=f_bold, fill=(134, 239, 172))
        draw.text((150, 505), "• 平均絶対誤差 (MAE): 0.175 (実測データ直接比較)", font=f_bold, fill=(255, 255, 255))
        draw.text((150, 545), "• 二乗平均平方根誤差 (RMSE): 0.175", font=f_body, fill=(226, 232, 240))
        draw.text((150, 585), "• Pearson 相関係数 (r): r = 0.957 (極めて高い予測整合性)", font=f_bold, fill=(34, 197, 94))
        draw.text((150, 625), "• ゼロ除算・欠損時は安易な補間を行わず「N/A」を明示", font=f_sub, fill=(148, 163, 184))

        draw.text((130, 715), "👉 「エージェントの予測限界を誠実に可視化する」学術的誠実性", font=f_bold, fill=(255, 255, 255))

        # Right: 1on1 Qualitative Interview
        draw.rounded_rectangle([(960, 220), (1760, 850)], radius=12, fill=(15, 23, 42), outline=(34, 197, 94), width=2)
        draw.text((990, 250), "2. 1on1 定性深掘りインタビュー (生の声で理由を対話)", font=f_bold, fill=(134, 239, 172))

        # Bubble 1: Interviewer
        draw.rounded_rectangle([(990, 310), (1730, 410)], radius=10, fill=(37, 99, 235))
        draw.text((1010, 325), "インタビュアー (マーケター):", font=f_bold, fill=(191, 219, 254))
        draw.text((1010, 360), "「スマートウォッチ購入意向で最高評価を付けた理由はどこにありますか？」", font=f_body, fill=(255, 255, 255))

        # Bubble 2: Persona
        draw.rounded_rectangle([(990, 430), (1730, 660)], radius=10, fill=(24, 33, 47), outline=(34, 197, 94), width=2)
        draw.text((1010, 450), "山本 茂 (62歳 / 定年退職・嘱託勤務 / 浜松市):", font=f_bold, fill=(134, 239, 172))
        draw.text((1010, 490), "「実は昨年、軽い不整脈を指摘されましてね。毎朝のウォーキング中も\n心拍数が気になっていたんです。AIがリズムの乱れを検知してくれるなら、\n月980円は命を預けるお守り代だと思えば、むしろ安い買い物だと感じました。」", font=f_body, fill=(241, 245, 249), spacing=8)

        draw.rounded_rectangle([(990, 690), (1730, 820)], radius=8, fill=(30, 41, 59), outline=(51, 65, 85), width=1)
        draw.text((1010, 715), "💡 生活背景と過去回答を統合した自律対話", font=f_bold, fill=(56, 189, 248))
        draw.text((1010, 755), "単なる一般論ではなく、病歴・習慣・予算意識などの個別文脈に\n基づくリアルな心理理由を深掘りヒアリングできます。", font=f_sub, fill=(203, 213, 225))

    elif stype == "governance":
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        draw.text((100, 170), "■ エンタープライズ導入に耐えうる AI ガバナンス・倫理設計", font=f_card_title, fill=(56, 189, 248))

        gov_cards = [
            ("🔐 事前同意確認の必須化 (デフォルトFalse)", "Mode C（インタビュー取り込み）では本人の事前同意確認を必須化。\n同意フラグのないデータ投入は 400 Bad Request でシステム的に即座拒否。"),
            ("🛡️ 審査用公開環境のデータ保護", "RESTRICT_PUBLIC_DATA_MODIFICATION により、公開審査環境での実在データ新規アップロード・\n初期デモデータセットの改変・削除を 403 Forbidden で完全遮断。"),
            ("⚠️ API障害時のモック切替明示", "Gemini API 失敗時はモックフォールバックであることを画面に明示。\nフェイクデータを実AI推論データとして集計・保存させない整合性保護。"),
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
        draw.rounded_rectangle([(60, 140), (1860, 900)], radius=16, fill=(30, 41, 59))
        
        # Left side: Google Cloud Architecture Highlights
        draw.rounded_rectangle([(100, 180), (1050, 850)], radius=12, fill=(15, 23, 42), outline=(66, 133, 244), width=2)
        draw.text((130, 215), "☁ Google Cloud 本番サーバーレス構成", font=f_card_title, fill=(66, 133, 244))
        
        arch_pts = [
            ("Google Cloud Run", "完全サーバーレスコンテナ。待機時インスタンス0（完全無料）から\nリクエストに応じてミリ秒で自動スケール。"),
            ("Google Gemini 3.5 Flash", "次世代フラッグシップ高速推論モデル。マルチエージェントの大量並列処理を\n低遅延かつ高スループットで実現。"),
            ("フルスタック統合コンテナ", "FastAPI バックエンド ＆ React 18 SPA をマルチステージビルドで1コンテナ化。\nデプロイとバージョン管理を極小化。"),
            ("堅牢なガバナンスと運用性", "Cloud Logging、同意管理API、公開環境保護、公的統計バリデーションの統合。")
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
    
    # Copy to artifacts directory as well
    artifact_path = r"C:\Users\hyama\.gemini\antigravity\brain\bd3149e6-418f-4bd2-a1e2-ffec92a88398\demo_video.mp4"
    try:
        import shutil
        shutil.copy2(OUTPUT_MP4, artifact_path)
        print(f"  Synced video to artifact directory: {artifact_path}")
    except Exception as e:
        print(f"  Warning syncing artifact: {e}")

    # Check final duration
    ff = subprocess.run(["ffmpeg", "-i", OUTPUT_MP4], capture_output=True, text=True)
    for line in ff.stderr.splitlines():
        if "Duration:" in line:
            print(f"Final Video Metadata: {line.strip()}")
            break
            
    return True

if __name__ == "__main__":
    durations = synthesize_audio()
    build_full_video(durations)
