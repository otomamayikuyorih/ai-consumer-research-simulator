import json
import logging
import random
from typing import Any
import numpy as np
from .config import settings, has_gemini_api_key

logger = logging.getLogger(__name__)

async def evaluate_concept_with_gemini(
    concept: dict[str, Any],
    sample_personas: list[dict[str, Any]],
    model_name: str = None,
    use_mock: bool = False
) -> dict[str, Any]:
    """Gemini APIを用いた新商品・サービスコンセプトの受容性評価"""
    if use_mock or not has_gemini_api_key():
        return evaluate_concept_heuristic(concept, sample_personas)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        model = model_name or settings.DEFAULT_GEMINI_MODEL

        personas_summary = []
        for p in sample_personas[:15]:
            personas_summary.append(
                f"- {p['persona_code']}: {p['age']}歳{p['gender']}, {p['occupation']}, 個人年収{p['personal_income']}万円, 価値観:{p['values_segment']}"
            )

        prompt = f"""あなたは消費者リサーチの専門アナリストです。
以下の新商品／サービスコンセプトについて、提示された仮想消費者サンプル群（{len(sample_personas)}名）の属性・年収・消費価値観に基づき、定量スコアと定性分析を実施してください。

### コンセプト情報:
- 商品・サービス名: {concept['name']}
- 想定価格: {concept['price']}円（税込）
- 対象カテゴリー: {concept['target_category']}
- コンセプト詳細・特徴: {concept['description']}

### 評価対象ペルソナ（抜粋）:
{chr(10).join(personas_summary)}

### 出力フォーマット指示:
必ず以下のJSON形式のみを出力してください。
{{
  "concept_name": "{concept['name']}",
  "mean_purchase_intent": 3.8, // 1〜5の平均購入意向
  "mean_interest": 4.1, // 1〜5の平均興味関心
  "price_perception": {{
    "安すぎる・お買い得": 15, // パーセント (合計100)
    "妥当・適正価格": 55,
    "やや高い": 25,
    "高すぎる": 5
  }},
  "top_appeal_segments": ["20〜30代の共働き世帯", "タイパ・実利志向層"],
  "assumed_usage_scenes": ["平日の退勤後のリラックス時間", "休日の家族との団らん"],
  "hesitation_reasons": ["初期費用の負担感", "既存代替品との差別化の分かりにくさ"],
  "improvement_suggestions": ["初回お試しプランの導入", "具体的な費用対効果の数値提示"],
  "overall_critique": "総評コメント（2〜3文）"
}}
"""
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.6,
            )
        )
        data = json.loads(response.text.strip())
        return data
    except Exception as e:
        logger.error(f"Gemini concept eval error: {e}. Falling back to heuristic.")
        return evaluate_concept_heuristic(concept, sample_personas)

def evaluate_concept_heuristic(concept: dict[str, Any], personas: list[dict[str, Any]]) -> dict[str, Any]:
    """オフライン／モック用のコンセプト受容性ヒューリスティック評価"""
    price = concept.get("price", 3000)
    desc = concept.get("description", "")
    target = concept.get("target_category", "")

    # 年収や価値観に基づく受容性スコアリング
    intents = []
    interests = []
    price_counts = {"安すぎる・お買い得": 0, "妥当・適正価格": 0, "やや高い": 0, "高すぎる": 0}

    for p in personas:
        income = p["personal_income"]
        val = p["values_segment"]

        # 興味関心
        interest_base = 3.2
        if val in ["トレンド・体験消費", "品質・本物志向"]:
            interest_base += 0.8
        if "AI" in desc or "自動" in desc or "スマート" in desc:
            if "ガジェット" in val or p["age"] < 40:
                interest_base += 0.6
        interest_score = min(5.0, max(1.0, interest_base + random.gauss(0, 0.6)))
        interests.append(interest_score)

        # 価格感
        # 1ヶ月あたりの許容度（年収の目安）
        ratio = price / max(100, income * 100)
        if ratio < 0.005:
            price_counts["安すぎる・お買い得"] += 1
            intent_offset = 0.5
        elif ratio < 0.02:
            price_counts["妥当・適正価格"] += 1
            intent_offset = 0.2
        elif ratio < 0.05:
            price_counts["やや高い"] += 1
            intent_offset = -0.3
        else:
            price_counts["高すぎる"] += 1
            intent_offset = -0.9

        # 購入意向
        intent_base = interest_score + intent_offset
        if val == "コスパ・実利重視" and intent_offset < 0:
            intent_base -= 0.5
        intent_score = min(5.0, max(1.0, intent_base + random.gauss(0, 0.5)))
        intents.append(intent_score)

    total = len(personas)
    price_perc = {k: round((v / total) * 100, 1) for k, v in price_counts.items()}

    return {
        "concept_name": concept["name"],
        "mean_purchase_intent": round(float(np.mean(intents)), 2),
        "mean_interest": round(float(np.mean(interests)), 2),
        "price_perception": price_perc,
        "top_appeal_segments": ["タイパ・効率重視層", "30〜40代現役世代", "品質・利便性を求める共働き層"],
        "assumed_usage_scenes": ["日常のルーチン業務・家事の効率化", "忙しい平日の時短活用", "自己投資・余暇時間の創出"],
        "hesitation_reasons": ["月額・単体価格に対する継続的納得感", "競合無料ツールや従来代替品との違い", "導入の手間や初期設定のハードル"],
        "improvement_suggestions": [
            "無料トライアルまたは低価格なスタータープランの用意",
            "利用者の具体的な導入ビフォーアフター事例の明示",
            "既存習慣からの乗り換えをスムーズにするチュートリアルの充実"
        ],
        "overall_critique": (
            f"『{concept['name']}』は興味関心スコア（{round(float(np.mean(interests)), 2)}点）が高く、"
            f"生活効率化や新規性を求めるセグメントにおいて強い引きがあります。"
            f"価格面では{price_perc.get('妥当・適正価格', 50)}%が妥当と評価する一方、"
            f"「やや高い・高すぎる」と感じる層に対しては費用対効果の明確な提示が成否を分けるポイントとなります。"
        )
    }

async def run_concept_comparison(
    concepts: list[dict[str, Any]],
    personas: list[dict[str, Any]],
    model_name: str = None,
    use_mock: bool = False
) -> dict[str, Any]:
    """複数コンセプトの比較評価を実行"""
    evaluations = []
    for c in concepts:
        ev = await evaluate_concept_with_gemini(c, personas, model_name=model_name, use_mock=use_mock)
        evaluations.append(ev)

    # 比較サマリーの作成
    winner_intent = max(evaluations, key=lambda x: x["mean_purchase_intent"])
    winner_interest = max(evaluations, key=lambda x: x["mean_interest"])

    comparison_summary = {
        "evaluated_concepts": evaluations,
        "best_purchase_intent": {
            "name": winner_intent["concept_name"],
            "score": winner_intent["mean_purchase_intent"]
        },
        "best_interest": {
            "name": winner_interest["concept_name"],
            "score": winner_interest["mean_interest"]
        },
        "strategic_recommendation": (
            f"購入意向の観点では『{winner_intent['concept_name']}』が最も高く、市場での初期受容性が期待できます。"
            f"各コンセプトの価格感とためらい理由を考慮し、ターゲット層の価値観（コスパ重視 vs 品質重視）に応じた訴求の使い分けが有効です。"
        )
    }

    return comparison_summary
