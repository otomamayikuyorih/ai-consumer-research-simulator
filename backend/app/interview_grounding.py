import json
import logging
import re
from typing import Any
from .config import settings, has_gemini_api_key

logger = logging.getLogger(__name__)

# --- デモ用サンプルインタビューデータ（研究・検証用の公開インタビュー想定データ） ---
DEMO_INTERVIEW_SAMPLES = [
    {
        "participant_id": "SUBJ-001",
        "demographics": {
            "age": 34,
            "gender": "女性",
            "occupation": "会社員（マーケティング企画）",
            "region": "関東",
            "prefecture": "東京都",
            "household": "夫婦と子ども（1人・3歳）",
            "personal_income": 580,
            "household_income": 1150
        },
        "raw_transcript": """
【調査員】日頃のお買い物や生活の中で、一番重視していることは何ですか？
【対象者】一番は『時間と心のゆとり』ですね。共働きで3歳の子どもがいるので、平日はとにかく分刻みで動いています。だから日用品や食材は、多少割高でもネットスーパーや生協、Amazon定期おトク便に頼り切っています。スーパーで棚を探し回る30分を家族の時間や休息に充てられるなら、数百円の手数料は全く高いと感じません。
【調査員】最近買って良かったと感じた商品やサービスはありますか？
【対象者】ロボット掃除機と、食洗機対応の調理器具ですね。特にロボット掃除機は10万円くらいしましたが、床掃除の心理的ストレスから完全に解放されました。逆に、いくら安くても『手入れが面倒』『操作が複雑』なものは絶対に買いたくないです。
【調査員】商品を選ぶ際、どんな情報を参考にしますか？
【対象者】Instagramで同じように子育てと仕事を両立しているワーママさんの投稿や、YouTubeの忖度なしレビュー動画をよく見ます。メーカー公式のきれいな広告文句よりも、実際に使ってみて困った点（デメリット）を正直に書いてくれている口コミを一番信頼します。
【調査員】価格に対する考え方を教えてください。
【対象者】日々の消耗品はコスパを意識しますが、生活の質（QOL）を底上げしてくれるものや、子どもの安全に関わるものには惜しみなく投資します。メリハリ消費ですね。
""",
        "extracted_data": {
            "values": ["時間効率・タイパ最優先", "生活の質（QOL）向上", "メリハリ消費", "家族との時間の最大化"],
            "consumption_habits": ["ネットスーパー・定期便のフル活用", "時短家電への積極投資", "日用品はまとめ買い"],
            "purchase_triggers": ["時短効果の明確さ", "日々の家事・育児ストレスの解消", "信頼できるワーママの口コミ"],
            "price_sensitivity": "日用品は価格にシビアだが、時間を節約できる製品・サービスには10万円単位の支出も許容",
            "decision_style": "実体験レビュー・デメリット重視の徹底比較型",
            "daily_habits": "平日は分刻みのタイムスケジュール、夜にSNSで効率的に情報収集",
            "interests": ["時短家事", "知育・幼児教育", "ワーママライフハック", "健康的な手抜き料理"],
            "verbatim_quotes": [
                "スーパーで棚を探し回る30分を家族の時間や休息に充てられるなら、数百円の手数料は全く高いと感じません。",
                "いくら安くても『手入れが面倒』『操作が複雑』なものは絶対に買いたくないです。",
                "メーカー公式のきれいな広告文句よりも、実際に使ってみて困った点（デメリット）を正直に書いてくれている口コミを一番信頼します。"
            ]
        }
    },
    {
        "participant_id": "SUBJ-002",
        "demographics": {
            "age": 24,
            "gender": "男性",
            "occupation": "エンジニア（Webサービス開発）",
            "region": "近畿",
            "prefecture": "大阪府",
            "household": "単身",
            "personal_income": 420,
            "household_income": 420
        },
        "raw_transcript": """
【調査員】普段のお金の使い方や買い物で意識していることは何ですか？
【対象者】自分は典型的な『コスパ・実利重視』ですね。物を所有することへの執着はあまりなくて、服もUNIQLOで十分だし、サブスクも不要になったらその月ですぐ解約します。でも、PC周辺機器や睡眠グッズ、健康に直結するサプリメントにはこだわりを持ってお金を使います。
【調査員】購入のきっかけになるメディアや情報源は？
【対象者】X（旧Twitter）のテック系アカウントのレビューや、Zenn/Qiitaなどの知見共有、Redditや個人ブログの徹底検証記事です。インフルエンサーのタイアップ案件はステマっぽく見えてスルーします。一次情報や客観的なベンチマーク測定結果が載っているかを重視します。
【調査員】購入をためらう理由は何ですか？
【対象者】機能に対して価格が見合っていない『ブランド代』が乗っていると感じたときです。あとはUIが使いにくそうだったり、解約方法が分かりにくいサービスは最初から登録しません。
""",
        "extracted_data": {
            "values": ["実利・機能性重視", "ミニマリズム", "自己投資（生産性・睡眠・健康）", "ブランド名に踊らされない"],
            "consumption_habits": ["不要な固定費の徹底削減", "機能スペックと価格の比率（コスパ）による選定"],
            "purchase_triggers": ["客観的なベンチマーク数値", "一次情報に基づく実証レビュー"],
            "price_sensitivity": "日常支出は極めて低価格志向だが、PC周辺や健康投資には妥協しない",
            "decision_style": "スペック比較・一次情報検証型",
            "daily_habits": "フルリモート勤務、XやWebで技術情報収集、無駄な人間関係や浪費を避ける",
            "interests": ["ガジェット", "プログラミング", "睡眠改善", "サウナ", "資産運用・オルカン"],
            "verbatim_quotes": [
                "物を所有することへの執着はあまりなくて、服もUNIQLOで十分だし、サブスクも不要になったらその月ですぐ解約します。",
                "インフルエンサーのタイアップ案件はステマっぽく見えてスルーします。一次情報や客観的なベンチマーク測定結果が載っているかを重視します。",
                "機能に対して価格が見合っていない『ブランド代』が乗っていると感じたときは絶対に買いません。"
            ]
        }
    },
    {
        "participant_id": "SUBJ-003",
        "demographics": {
            "age": 67,
            "gender": "男性",
            "occupation": "定年退職（元メーカー管理職）",
            "region": "中部",
            "prefecture": "愛知県",
            "household": "夫婦のみ",
            "personal_income": 260,
            "household_income": 450
        },
        "raw_transcript": """
【調査員】現在のご生活とお買い物のスタンスについて教えてください。
【対象者】数年前に定年を迎え、今は妻と2人で穏やかに暮らしています。年齢とともに『健康の維持』と『日々のささやかな楽しみ』が何よりの関心事になりました。食品はできるだけ国産や減農薬、添加物の少ないものを近所の専門店や生協で選んでいます。
【調査員】新しい製品やサービスを利用する際に不安に思うことはありますか？
【対象者】やはりスマートフォンのアプリやデジタル決済ですね。使いこなせれば便利なのでしょうが、文字が小さかったり、問い合わせ先がAIチャットだけで人間の担当者と話せないサービスは途方に暮れてしまいます。困ったときに電話で丁寧に教えてくれるサポート体制があるかが、私にとっては最大の安心材料です。
【調査員】価格についてはいかがですか？
【対象者】年金暮らしですので派手な贅沢はできませんが、安物買いの銭失いにはなりたくありません。信頼できる老舗や、しっかりアフターサービスをしてくれる企業のものであれば、少々高くても納得して購入します。
""",
        "extracted_data": {
            "values": ["健康長寿への配慮", "安心・安全・信頼感", "本物志向・丁寧な暮らし", "国産・老舗への愛着"],
            "consumption_habits": ["高品質・無添加食品の選定", "信頼できる実店舗での購入", "衝動買いはしない"],
            "purchase_triggers": ["分かりやすい説明", "電話など人間による手厚いアフターサポート"],
            "price_sensitivity": "価格の安さよりも、安全性と耐久性、トラブル時の対応力を最重視",
            "decision_style": "慎重・信頼重視型（アフターフォロー重視）",
            "daily_habits": "朝の散歩、新聞通読、家庭菜園、夫婦での旅行計画",
            "interests": ["ウォーキング", "家庭菜園", "温泉旅行", "歴史・読書", "孫との交流"],
            "verbatim_quotes": [
                "問い合わせ先がAIチャットだけで人間の担当者と話せないサービスは途方に暮れてしまいます。困ったときに電話で丁寧に教えてくれるサポート体制があるかが最大の安心材料です。",
                "年金暮らしですので派手な贅沢はできませんが、安物買いの銭失いにはなりたくありません。",
                "信頼できる老舗や、しっかりアフターサービスをしてくれる企業のものであれば、少々高くても納得して購入します。"
            ]
        }
    }
]

def parse_interview_csv(csv_text: str) -> list[dict[str, Any]]:
    """CSV形式のインタビュー回答をパース"""
    import csv
    import io
    f = io.StringIO(csv_text.strip())
    reader = csv.DictReader(f)
    records = []
    for row in reader:
        records.append(row)
    return records

async def extract_interview_grounding(raw_text: str, metadata: dict[str, Any] = None) -> dict[str, Any]:
    """Gemini APIを用いてインタビューテキストから7次元の生活者属性と肉声発言を抽出"""
    if not has_gemini_api_key():
        # オフライン・モック抽出
        return extract_grounding_heuristic(raw_text, metadata)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = f"""
あなたは質的社会調査および生活者インサイト分析のエキスパートです。
以下のインタビュー記録（文字起こし）から、生活者の意思決定モデルを構築するための要素を抽出してください。

重要指示：
1. 「verbatim_quotes」（元の肉声・発言）には、生活者の価値観や感情、購買の決め手が最もよく表れている実際の発言文を原文のまま（一字一句変えずに）3〜5件抽出してください。要約による情報損失を避けてください。
2. 以下のJSONスキーマで厳密に出力してください。

【インタビュー記録】
{raw_text}

【出力JSONスキーマ】
{{
  "demographics_inferred": {{
    "age": 整数またはnull,
    "gender": "男性" or "女性" or "不明",
    "occupation": "職業",
    "household": "世帯構成"
  }},
  "values": ["価値観1", "価値観2", "価値観3"],
  "consumption_habits": ["消費行動の特徴1", "特徴2"],
  "purchase_triggers": ["購買動機・決め手1", "決め手2"],
  "price_sensitivity": "価格に対する感度・考え方の要約文",
  "decision_style": "意思決定の傾向（徹底比較型、直感型、口コミ重視型など）",
  "daily_habits": "生活習慣や日常の時間の使い方",
  "interests": ["興味・趣味1", "興味2"],
  "verbatim_quotes": [
    "対象者の実際の発言そのままの引用文1",
    "対象者の実際の発言そのままの引用文2"
  ]
}}
"""
        response = client.models.generate_content(
            model=settings.DEFAULT_GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            )
        )
        data = json.loads(response.text.strip())
        return data
    except Exception as e:
        logger.error(f"Gemini interview extraction failed: {e}. Falling back to heuristic.")
        return extract_grounding_heuristic(raw_text, metadata)

def extract_grounding_heuristic(raw_text: str, metadata: dict[str, Any] = None) -> dict[str, Any]:
    """オフライン用ヒューリスティック抽出器"""
    quotes = []
    for line in raw_text.splitlines():
        line = line.strip()
        if "【対象者】" in line:
            content = line.replace("【対象者】", "").strip()
            if len(content) > 15:
                quotes.append(content)

    if not quotes:
        quotes = [
            line.strip() for line in raw_text.splitlines() if len(line.strip()) > 20
        ][:3]

    return {
        "demographics_inferred": metadata.get("demographics", {}) if metadata else {
            "age": 35,
            "gender": "女性",
            "occupation": "会社員",
            "household": "核家族"
        },
        "values": ["実利性重視", "時間効率", "安心・信頼"],
        "consumption_habits": ["レビューを事前確認", "無駄遣いを抑制", "納得感のあるものに支出"],
        "purchase_triggers": ["日常のストレス解消", "利便性の向上"],
        "price_sensitivity": "機能と利便性に見合っていれば適正な支出を惜しまない",
        "decision_style": "客観的レビューと使い勝手を重視する実利型",
        "daily_habits": "効率的な生活リズムを心掛け、情報収集はスマートフォンで実施",
        "interests": ["効率化", "生活改善", "良質な日用品"],
        "verbatim_quotes": quotes[:4] if quotes else [
            "日々の生活をより豊かで無理のないものにするために、商品やサービスを吟味しています。"
        ]
    }
