import json
import logging
import random
from typing import Any
from .config import settings, has_gemini_api_key

logger = logging.getLogger(__name__)

def build_batch_prompt(personas: list[dict[str, Any]], questions: list[dict[str, Any]]) -> str:
    """複数ペルソナに対する一括アンケート回答プロンプトを作成"""
    questions_desc = []
    for q in questions:
        q_info = f"- 設問ID: {q['id']}, 設問文: {q['text']}, 形式: {q['type']}"
        if q.get("options"):
            q_info += f", 選択肢: {', '.join(q['options'])}"
        if q['type'] == 'scale5':
            q_info += " (1: 全くそう思わない 〜 5: 非常にそう思う)"
        questions_desc.append(q_info)
    
    questions_text = "\n".join(questions_desc)

    personas_desc = []
    for p in personas:
        mode = p.get("generation_mode", "mode_b")
        if mode == "mode_a":
            # Mode A: Demographic Persona（属性情報のみ）
            p_info = (
                f"【ペルソナID: {p['persona_code']} (Mode A: 人口統計属性のみ)】\n"
                f"年齢: {p['age']}歳 ({p['age_group']}), 性別: {p['gender']}, 居住地: {p['prefecture']} ({p['region']})\n"
                f"職業: {p['occupation']} ({p['employment_type']}), 学歴: {p['education']}\n"
                f"個人年収: {p['personal_income']}万円, 世帯年収: {p['household_income']}万円, 世帯構成: {p['household']}\n"
            )
        elif mode == "mode_c":
            # Mode C: Interview-Grounded Persona（実測インタビュー接地）
            grounded = p.get("grounded_interview") or {}
            quotes = grounded.get("verbatim_quotes", [])
            quotes_str = "\n".join(f"  ・肉声引用: 「{q}」" for q in quotes[:3]) if quotes else "  ・インタビュー記録に基づく生活実感"
            p_info = (
                f"【ペルソナID: {p['persona_code']} (Mode C: 実測インタビュー接地)】\n"
                f"年齢: {p['age']}歳, 性別: {p['gender']}, 職業: {p['occupation']}, 居住地: {p['prefecture']}\n"
                f"個人年収: {p['personal_income']}万円, 世帯構成: {p['household']}\n"
                f"消費価値観: {p['values_segment']}, 価格感度: {grounded.get('price_sensitivity', '状況に応じてメリハリをつける')}\n"
                f"インタビュー発言記録（Verbatim Quotes）:\n{quotes_str}\n"
            )
        else:
            # Mode B: Synthetic Rich Persona（合成生活史＋合成購買経験）
            experiences = p.get("purchase_experiences") or []
            exp_str = f"過去の購買経験: {', '.join(experiences[:2])}\n" if experiences else ""
            p_info = (
                f"【ペルソナID: {p['persona_code']} (Mode B: 仮想生活史リッチ)】\n"
                f"年齢: {p['age']}歳 ({p['age_group']}), 性別: {p['gender']}, 居住地: {p['prefecture']} ({p['region']})\n"
                f"職業: {p['occupation']} ({p['employment_type']}), 学歴: {p['education']}\n"
                f"個人年収: {p['personal_income']}万円, 世帯年収: {p['household_income']}万円, 世帯構成: {p['household']}\n"
                f"消費価値観: {p['values_segment']}, 意思決定スタイル: {p['decision_style']}, ライフスタイル: {p['lifestyle']}\n"
                f"趣味: {', '.join(p.get('hobbies', []))}\n"
                f"仮想生活史: {p.get('life_history', '')}\n"
                f"{exp_str}"
                f"生活・消費プロファイル: {p['consumption_profile']}\n"
            )
        personas_desc.append(p_info)

    personas_text = "\n".join(personas_desc)

    prompt = f"""あなたは日本国内の多様な消費者になりきって、アンケート調査に回答するAIシミュレーターです。
以下の各ペルソナの性格、年齢、性別、収入、消費価値観、ライフスタイルを完全に憑依させ、それぞれの生活背景と一貫性のある真実味のある回答を生成してください。

### 設問一覧:
{questions_text}

### 対象ペルソナ一覧:
{personas_text}

### 出力フォーマット指示:
必ず以下のJSON形式のみを出力してください。Markdownのコードブロック (```json ... ```) で囲んでください。
JSON構造:
{{
  "responses": [
    {{
      "persona_code": "P-0001",
      "answers": {{
        "q1": "選択肢文字列または数値",
        "q2": ["選択肢1", "選択肢2"],
        "q3": 4,
        "q4": "自由記述のリアルな感想や理由"
      }},
      "reasoning": "このペルソナがこの回答を選んだ背景理由の簡単な要約"
    }}
  ]
}}

注意事項:
1. single形式の回答は、選択肢の中から必ず1つ選んでください。
2. multiple形式の回答は、選択肢の中から0個以上を選び、配列で返してください。
3. scale5形式の回答は、1から5の整数値で返してください。
4. text形式の回答は、ペルソナの口調・価値観・生活実感に沿った自然な日本語の文章（2〜3文程度）で回答してください。
5. ペルソナ内の全設問への回答は論理的に一貫している必要があります。
"""
    return prompt

def generate_mock_answers_for_persona(persona: dict[str, Any], questions: list[dict[str, Any]]) -> dict[str, Any]:
    """オフライン時またはAPI未設定時用の高度なヒューリスティック回答シミュレーター"""
    answers = {}
    p_age = persona["age"]
    p_val = persona["values_segment"]
    p_dec = persona["decision_style"]
    p_income = persona["personal_income"]

    reasons = []

    for q in questions:
        q_id = q["id"]
        q_type = q["type"]
        options = q.get("options", [])

        if q_type == "single":
            if not options:
                answers[q_id] = "回答なし"
                continue
            # 属性連動バイアスを付与
            weights = [1.0] * len(options)
            for idx, opt in enumerate(options):
                if "安" in opt or "コスパ" in opt or "価格" in opt:
                    if p_val == "コスパ・実利重視" or p_income < 400:
                        weights[idx] += 2.5
                if "質" in opt or "安心" in opt or "高級" in opt or "ブランド" in opt:
                    if p_val == "品質・本物志向" or p_income > 700:
                        weights[idx] += 2.5
                if "トレンド" in opt or "新しい" in opt or "SNS" in opt:
                    if p_age < 35 or p_val == "トレンド・体験消費":
                        weights[idx] += 3.0
                if "健康" in opt or "サステナ" in opt or "自然" in opt:
                    if p_val in ["サステナビリティ・エシカル", "健康・ウェルネス投資"] or p_age >= 50:
                        weights[idx] += 2.5
            chosen = random.choices(options, weights=weights, k=1)[0]
            answers[q_id] = chosen

        elif q_type == "multiple":
            if not options:
                answers[q_id] = []
                continue
            chosen_list = []
            for opt in options:
                prob = 0.35
                if ("安" in opt or "お得" in opt or "ポイント" in opt) and (p_val == "コスパ・実利重視" or "節約" in p_val):
                    prob = 0.75
                if ("品質" in opt or "機能" in opt) and (p_val == "品質・本物志向"):
                    prob = 0.70
                if ("SNS" in opt or "話題" in opt) and (p_age < 35):
                    prob = 0.65
                if ("健康" in opt or "国産" in opt) and (p_age >= 50):
                    prob = 0.70
                if random.random() < prob:
                    chosen_list.append(opt)
            if not chosen_list and options:
                chosen_list.append(random.choice(options))
            answers[q_id] = chosen_list

        elif q_type == "scale5":
            # 基準スコア (3) に価値観・属性によるオフセットを加味
            base = 3.0
            if p_val in ["トレンド・体験消費", "品質・本物志向"]:
                base += 0.6
            if p_val in ["堅実・節約・保守的"]:
                base -= 0.4
            noise = random.gauss(0, 0.8)
            score = int(round(max(1, min(5, base + noise))))
            answers[q_id] = score

        elif q_type == "text":
            # 属性に応じた自然な定性テキスト
            templates = [
                f"{persona['age']}歳の{persona['occupation']}として生活していますが、普段は{persona['values_segment']}を意識しています。今回の内容は{persona['decision_style']}な私にとって非常に納得感があり、生活に取り入れやすいと感じます。",
                f"世帯年収{persona['household_income']}万円で{persona['household']}の暮らしをしているため、支出には慎重です。もう少し価格や手間の面でメリットが明確であれば前向きに検討したいです。",
                f"{persona['lifestyle']}を重視しているため、日々のタイパや利便性が向上するならぜひ使ってみたいと思いました。特に{', '.join(persona['hobbies'][:2])}などの時間も確保しやすくなりそうです。",
                f"自分のような{persona['age_group']}の視点で見ると、信頼できる情報源やクチコミでの評価が気になります。機能や使い勝手が直感的に分かるのであれば魅力的です。"
            ]
            answers[q_id] = random.choice(templates)

    reasoning = f"{persona['age_group']}{persona['gender']}・{p_val}の生活観を反映し、{p_dec}の観点から回答。"

    return {
        "persona_code": persona["persona_code"],
        "answers": answers,
        "reasoning": reasoning
    }

async def run_batch_with_gemini(personas: list[dict[str, Any]], questions: list[dict[str, Any]], model_name: str = None) -> list[dict[str, Any]]:
    """Gemini APIを使用してペルソナバッチの回答を生成"""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        model = model_name or settings.DEFAULT_GEMINI_MODEL
        prompt = build_batch_prompt(personas, questions)

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            )
        )

        text = response.text.strip()
        # JSON解析
        data = json.loads(text)
        if isinstance(data, dict) and "responses" in data:
            return data["responses"]
        elif isinstance(data, list):
            return data
        else:
            logger.warning("Unexpected JSON format from Gemini, falling back to mock parser")
            return [generate_mock_answers_for_persona(p, questions) for p in personas]

    except Exception as e:
        logger.error(f"Gemini API execution error: {e}. Falling back to statistical mock generator.")
        # エラー発生時は安全に相関シミュレーターへフォールバック
        return [generate_mock_answers_for_persona(p, questions) for p in personas]

async def execute_survey_simulation(
    personas: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    model_name: str = None,
    use_mock: bool = False,
    batch_size: int = 10
) -> list[dict[str, Any]]:
    """コホート全員に対してアンケート調査を実行"""
    all_responses = []
    total = len(personas)

    # APIキーが無い、またはモック指定の場合は高速相関シミュレーターを使用
    can_use_gemini = has_gemini_api_key() and not use_mock

    for i in range(0, total, batch_size):
        batch = personas[i:i + batch_size]
        if can_use_gemini:
            batch_res = await run_batch_with_gemini(batch, questions, model_name=model_name)
            # コード突合チェック
            res_dict = {r.get("persona_code"): r for r in batch_res if isinstance(r, dict)}
            for p in batch:
                if p["persona_code"] in res_dict:
                    all_responses.append(res_dict[p["persona_code"]])
                else:
                    all_responses.append(generate_mock_answers_for_persona(p, questions))
        else:
            for p in batch:
                all_responses.append(generate_mock_answers_for_persona(p, questions))

    return all_responses
