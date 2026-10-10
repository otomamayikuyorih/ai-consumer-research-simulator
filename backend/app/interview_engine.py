import logging
from typing import Any
from .config import settings, has_gemini_api_key

logger = logging.getLogger(__name__)

def build_persona_system_prompt(persona: dict[str, Any], survey_answers: dict[str, Any] = None) -> str:
    """ペルソナになりきるための詳細なシステムプロンプトを構築"""
    hobbies_str = ", ".join(persona.get("hobbies", []))
    channels_str = ", ".join(persona.get("info_channels", []))

    survey_history = ""
    if survey_answers:
        survey_history = "\n### あなたが最近受けたアンケートでの回答履歴:\n"
        for q_id, ans in survey_answers.items():
            survey_history += f"- 設問 {q_id}: {ans}\n"

    interview_grounding_section = ""
    grounded = persona.get("grounded_interview") or {}
    verbatims = grounded.get("verbatim_quotes", [])
    if verbatims or persona.get("life_history"):
        interview_grounding_section = "\n### あなたが実際の質的インタビュー調査で語った発言記録（肉声）:\n"
        for v in verbatims:
            interview_grounding_section += f"- 『{v}』\n"
        if persona.get("life_history"):
            interview_grounding_section += f"- 生活背景・来歴: {persona.get('life_history')}\n"
        interview_grounding_section += "【重要】対話時は、上記の実際のインタビュー発言や生活実感と整合するよう回答してください。\n"

    system_prompt = f"""あなたは以下のプロフィールを持つ実在の日本人生活者として対話してください。
AIやアシスタントとしてのメタ発言は絶対にせず、あなた自身（{persona['name']}さん）として、生活実感のこもった口調で回答してください。

### あなたの基本プロフィール:
- 氏名: {persona['name']} (生成モード: {persona.get('generation_mode', 'mode_b')})
- 年齢: {persona['age']}歳 ({persona['age_group']})
- 性別: {persona['gender']}
- 居住地: {persona['prefecture']} ({persona['region']})
- 職業・働き方: {persona['occupation']} ({persona['employment_type']})
- 世帯構成: {persona['household']}
- 学歴: {persona['education']}
- 個人年収: {persona['personal_income']}万円 / 世帯年収: {persona['household_income']}万円
- 趣味・休日の過ごし方: {hobbies_str}
- 消費価値観: {persona['values_segment']}
- 購買決定の傾向: {persona['decision_style']}
- ライフスタイル: {persona['lifestyle']}
- 普段利用する情報源: {channels_str}
- 生活の背景: {persona['consumption_profile']}
{interview_grounding_section}
{survey_history}

### 対話のルール:
1. 自分の年齢や立場、性別、生活水準に見合った自然な日本語（丁寧かつ親しみやすいトーン）で話してください。
2. インタビュアー（マーケター）から「なぜそれを選んだのか」「普段どうしているか」などを聞かれたら、あなたの価値観（{persona['values_segment']}）や懐事情、家族構成を踏まえてリアルな本音を語ってください。
3. 過去のアンケート回答内容やインタビューでの発言内容と矛盾しないよう一貫性を保ってください。
4. 長すぎず、1〜3段落程度で人間らしくテンポよく答えてください。
"""
    return system_prompt

async def chat_with_persona(
    persona: dict[str, Any],
    history: list[dict[str, str]],
    user_message: str,
    survey_answers: dict[str, Any] = None,
    model_name: str = None
) -> str:
    """ペルソナとの1on1インタビュー対話メッセージ生成"""
    system_prompt = build_persona_system_prompt(persona, survey_answers)

    if has_gemini_api_key():
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            model = model_name or settings.DEFAULT_GEMINI_MODEL

            # 会話履歴の構築
            prompt_contents = [system_prompt]
            for msg in history:
                role = "User" if msg["role"] == "user" else "Model"
                prompt_contents.append(f"{role}: {msg['content']}")
            prompt_contents.append(f"User: {user_message}\nModel ({persona['name']}):")

            full_prompt = "\n\n".join(prompt_contents)

            response = client.models.generate_content(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                )
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API chat error: {e}. Falling back to mock persona response.")

    # オフライン／モック応答エンジン
    return generate_mock_interview_response(persona, user_message, survey_answers)

def generate_mock_interview_response(persona: dict[str, Any], user_message: str, survey_answers: dict[str, Any] = None) -> str:
    """オフライン時のリアルなペルソナ応答シミュレーター"""
    name = persona["name"]
    age = persona["age"]
    occupation = persona["occupation"]
    val = persona["values_segment"]
    dec = persona["decision_style"]
    income = persona["personal_income"]

    # 質問内容に応じたキーワードマッチング
    msg = user_message.lower()

    if "なぜ" in msg or "理由" in msg or "選んだ" in msg:
        return (
            f"そうですね、私は普段から『{val}』というスタンスを大事にしていて、無駄な買い物はできるだけ避けたいと考えているんです。"
            f"今回のアンケートでもお答えした通り、{dec}の傾向があるので、自分の生活や仕事（{occupation}）の合間に"
            f"無理なく続けられるかや、支払う対価以上のリターンが得られるかを一番に考えて選びました。"
        )
    elif "価格" in msg or "値段" in msg or "高" in msg or "いくら" in msg:
        return (
            f"価格面はかなりシビアに見ていますね。私の個人年収は約{income}万円なので、"
            f"毎月の固定費や貯蓄のバランスを考えると、あまり突飛な価格設定だと購入は見送ると思います。"
            f"もし価格が2〜3割上がるなら、他社のサービスや代替手段を徹底的にレビュー比較して、"
            f"本当にそれだけの付加価値があるか再検討しますね。"
        )
    elif "情報" in msg or "sns" in msg or "どこで" in msg or "メディア" in msg:
        channels = ", ".join(persona.get("info_channels", [])[:2])
        return (
            f"普段の情報収集は、主に{channels}を見ることが多いですね。"
            f"特に新しい商品や話題のサービスは、広告よりも実際の利用者のリアルな口コミやレビューを重視します。"
            f"気になったものはまずスマホで検索して、マイナス評価の理由まで確認してから決めるようにしています。"
        )
    elif "普段" in msg or "生活" in msg or "休日" in msg or "趣味" in msg:
        hobbies = ", ".join(persona.get("hobbies", [])[:2])
        return (
            f"平日は{occupation}の仕事でバタバタしていることも多いですが、休日は{hobbies}をしてリフレッシュしています。"
            f"生活スタイルとしては『{persona['lifestyle']}』を大事にしているので、自分のペースを崩さずに楽しめるものが好きですね。"
        )
    else:
        return (
            f"ご質問ありがとうございます。{age}歳の{persona['gender']}として、今の私の生活環境（{persona['household']}）から考えると、"
            f"やはり『{val}』という視点は外せません。もしこのサービスや商品が本当に私の生活の手間を減らしてくれたり、"
            f"価値を提供してくれるなら、ぜひ前向きに試してみたいと思っています。"
        )
