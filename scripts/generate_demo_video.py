"""
AI Consumer Research Simulator - 3-Minute Demo Video Generator
Automates:
1. Speech synthesis for 11 scenes (Microsoft Haruka Desktop via System.Speech)
2. Slide rendering with 1080p graphics, architecture diagram, screenshots, cards & subtitles
3. Video synthesis with ffmpeg into submission/demo_video.mp4
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

# 11 Demo Scenes
SCENES = [
    {
        "id": "scene01",
        "title": "AI Consumer Research Simulator",
        "subtitle": "第5回 Agentic AI Hackathon with Google Cloud 提出作品",
        "tag": "01 / OVERVIEW",
        "text": "第5回 Agentic AI Hackathon with Google Cloud 提出作品、AI Consumer Research Simulator です。",
        "type": "title",
    },
    {
        "id": "scene02",
        "title": "従来の市場調査が抱える構造的課題と解決策",
        "subtitle": "数週間の納期・数百万のコストを、公的統計×自律型マルチエージェントで数分に短縮",
        "tag": "02 / PROBLEM & SOLUTION",
        "text": "新商品の企画や市場調査には、数週間と数百万円がかかります。本システムは、日本の公的統計データと、スタンフォード大学AI4PB研究に基づく自律型マルチエージェントを活用し、仮想消費者集団へのアンケート調査、多変量解析、そして1対1の深掘りインタビューをわずか数分で完結させるWebプラットフォームです。",
        "type": "problem_solution",
    },
    {
        "id": "scene03",
        "title": "統計ペルソナ生成エージェント",
        "subtitle": "国勢調査・家計調査等の多変量相関に基づき非現実な組み合わせを排除",
        "tag": "03 / PERSONA SYNTHESIZER",
        "text": "まず、仮想消費者を生成します。日本の国勢調査や家計調査の統計相関を考慮し、年齢、年収、居住地、消費価値観の非現実的な組み合わせを排除したリアルな生活者群を自律生成します。",
        "type": "persona_gen",
    },
    {
        "id": "scene04",
        "title": "公的統計ベンチマーク客観検証",
        "subtitle": "生成集団の年代・性別・地域分布をe-Stat公的統計と高精度合致検証",
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
        "title": "Nature 2026準拠 仮想A/Bランダム化実験",
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
        "title": "1on1 定性深掘りインタビュー",
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

if __name__ == "__main__":
    synthesize_audio()
