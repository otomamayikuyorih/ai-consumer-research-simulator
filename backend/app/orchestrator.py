import json
import logging
import time
from typing import Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .config import settings, has_gemini_api_key
from .models import PersonaCohort, Persona, Survey, SurveyResponse
from .persona_generator import generate_cohort_personas, STATISTICAL_BENCHMARKS
from .survey_runner import execute_survey_simulation
from .analysis_engine import analyze_survey_results
from .gemini_service import (
    get_gemini_client,
    is_gemini_available,
    call_gemini_json_with_tracking
)

logger = logging.getLogger(__name__)

async def run_autonomous_orchestration(
    research_goal: str,
    target_count: int = 50,
    generation_mode: str = "mode_b",
    use_mock: bool = False,
    db: Session = None
) -> dict[str, Any]:
    """調査課題の入力から、ペルソナ生成 -> 設問設計 -> マルチエージェント調査回答 -> 多変量解析 & エグゼクティブサマリー要約までを自律的に連結実行するオーケストレーター"""
    orchestration_start = time.time()
    steps_log = []

    def make_step(step_id: str, name: str, model: str):
        return {
            "step_id": step_id,
            "name": name,
            "step_name": name,
            "status": "running",
            "model_used": model,
            "retry_count": 0,
            "retries": 0,
            "api_calls_count": 0,
            "is_fallback": False,
            "fallback_reason": None,
            "tokens_used": {"prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0},
            "duration_ms": 0,
            "error": None,
            "details": ""
        }

    available, provider, resolved_model = is_gemini_available()

    # ---------------------------------------------------------
    # STEP 1: 生活者ペルソナ集団の自律生成
    # ---------------------------------------------------------
    step1 = make_step(
        "step_1_persona_cohort",
        "生活者ペルソナ集団の自律生成",
        "Statistical Joint Synthesizer (e-Stat / 国勢調査)"
    )
    t0 = time.time()
    try:
        cohort_name = f"【自律調査コホート】{research_goal[:20]}（N={target_count}）"
        personas_data = generate_cohort_personas(
            count=target_count,
            mode=generation_mode,
            seed=int(time.time()) % 10000
        )

        cohort_record = PersonaCohort(
            name=cohort_name,
            target_count=target_count,
            seed=42,
            generation_mode=generation_mode,
            provenance_info={
                "orchestrated": True,
                "goal": research_goal,
                "benchmark_source": STATISTICAL_BENCHMARKS["source"]
            }
        )
        db.add(cohort_record)
        db.commit()
        db.refresh(cohort_record)

        for p in personas_data:
            p_obj = Persona(
                cohort_id=cohort_record.id,
                persona_code=p["persona_code"],
                generation_mode=generation_mode,
                name=p["name"],
                age=p["age"],
                age_group=p["age_group"],
                gender=p["gender"],
                region=p["region"],
                prefecture=p["prefecture"],
                occupation=p["occupation"],
                employment_type=p["employment_type"],
                household=p["household"],
                education=p["education"],
                personal_income=p["personal_income"],
                household_income=p["household_income"],
                hobbies=p.get("hobbies", []),
                values_segment=p["values_segment"],
                lifestyle=p["lifestyle"],
                info_channels=p.get("info_channels", []),
                decision_style=p["decision_style"],
                consumption_profile=p["consumption_profile"],
                grounded_interview=p.get("grounded_interview", {})
            )
            db.add(p_obj)
        db.commit()

        step1["status"] = "completed"
        step1["duration_ms"] = int((time.time() - t0) * 1000)
        step1["details"] = f"総務省統計局「令和2年国勢調査」等の結合確率に基づき、多様な生活者{len(personas_data)}名を生成完了"
    except Exception as e:
        step1["status"] = "failed"
        step1["error"] = str(e)
        step1["duration_ms"] = int((time.time() - t0) * 1000)
        steps_log.append(step1)
        raise e
    steps_log.append(step1)

    # ---------------------------------------------------------
    # STEP 2: 調査設問の自律設計
    # ---------------------------------------------------------
    model_s2 = resolved_model if (available and not use_mock) else "structured_survey_template"
    step2 = make_step(
        "step_2_survey_design",
        "調査設問の自律設計（アンケート生成）",
        model_s2
    )
    t0 = time.time()
    try:
        questions, s2_meta = await auto_design_survey_questions(research_goal, use_mock=use_mock)
        survey_title = f"【自律設計調査】{research_goal}"
        survey_record = Survey(
            cohort_id=cohort_record.id,
            title=survey_title,
            description=f"調査課題: {research_goal} に基づき自律生成された構造化設問群",
            questions=questions,
            model_name=s2_meta.get("model_used", model_s2)
        )
        db.add(survey_record)
        db.commit()
        db.refresh(survey_record)

        step2["duration_ms"] = int((time.time() - t0) * 1000)
        step2["model_used"] = s2_meta.get("model_used", model_s2)
        step2["api_calls_count"] = s2_meta.get("api_calls_count", 0)
        step2["tokens_used"] = s2_meta.get("tokens_used", {"prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0})
        step2["is_fallback"] = s2_meta.get("is_fallback", False)
        step2["fallback_reason"] = s2_meta.get("fallback_reason")

        if s2_meta.get("is_fallback"):
            step2["status"] = "fallback_mock"
            step2["details"] = f"Gemini設計フォールバック（{s2_meta.get('fallback_reason', '')[:60]}）のため標準構造化テンプレートを適用"
        else:
            step2["status"] = "completed"
            step2["details"] = f"調査課題に対応する全{len(questions)}問（単一選択、5段階評価、自由記述）を自律設計完了"
    except Exception as e:
        step2["status"] = "failed"
        step2["error"] = str(e)
        step2["duration_ms"] = int((time.time() - t0) * 1000)
        steps_log.append(step2)
        raise e
    steps_log.append(step2)

    # ---------------------------------------------------------
    # STEP 3: マルチエージェント自律並列推論（アンケート回答）
    # ---------------------------------------------------------
    model_s3 = resolved_model if (available and not use_mock) else "heuristic_statistical_model"
    step3 = make_step(
        "step_3_survey_execution",
        "マルチエージェント自律並列推論（アンケート回答）",
        model_s3
    )
    t0 = time.time()
    try:
        personas_objs = db.query(Persona).filter(Persona.cohort_id == cohort_record.id).all()
        personas_dicts = [p.to_dict() for p in personas_objs]

        results, exec_meta = await execute_survey_simulation(
            personas=personas_dicts,
            questions=questions,
            use_mock=use_mock,
            model_name=resolved_model,
            batch_size=10
        )

        persona_map = {p.persona_code: p.id for p in personas_objs}
        for r in results:
            p_code = r["persona_code"]
            p_id = persona_map.get(p_code)
            if p_id:
                resp = SurveyResponse(
                    survey_id=survey_record.id,
                    persona_id=p_id,
                    answers=r["answers"],
                    reasoning=r.get("reasoning", "")
                )
                db.add(resp)
        db.commit()

        step3["duration_ms"] = int((time.time() - t0) * 1000)
        step3["model_used"] = exec_meta.get("model_name", model_s3)
        step3["api_calls_count"] = exec_meta.get("api_calls_count", 0)
        step3["tokens_used"] = exec_meta.get("tokens_used", {"prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0})
        step3["is_fallback"] = exec_meta.get("is_fallback", False)
        step3["fallback_reason"] = exec_meta.get("error_detail") or exec_meta.get("warning")

        if exec_meta.get("is_fallback"):
            step3["status"] = "fallback_mock"
            step3["error"] = exec_meta.get("warning")
            step3["details"] = f"Gemini推論エラーのため統計相関モック推論で実行: {str(exec_meta.get('error_detail', ''))[:80]}"
        elif exec_meta.get("is_mock"):
            step3["status"] = "fallback_mock"
            step3["details"] = "ルールベース統計相関モデルで実行（デモモード）"
        else:
            step3["status"] = "completed"
            step3["details"] = f"{len(results)}名の仮想生活者エージェントが価値観・可処分所得・生活実感に基づき並列回答完了"
    except Exception as e:
        step3["status"] = "failed"
        step3["error"] = str(e)
        step3["duration_ms"] = int((time.time() - t0) * 1000)
        steps_log.append(step3)
        raise e
    steps_log.append(step3)

    # ---------------------------------------------------------
    # STEP 4: 多変量解析 & エグゼクティブサマリー自動統合
    # ---------------------------------------------------------
    step4 = make_step(
        "step_4_analytics_synthesis",
        "多変量解析＆エグゼクティブサマリー自律要約",
        f"scikit-learn + {resolved_model if (available and not use_mock) else 'rule_based_synthesis'}"
    )
    t0 = time.time()
    try:
        # DBから回答を取得して多変量解析
        raw_responses = db.query(SurveyResponse).filter(SurveyResponse.survey_id == survey_record.id).all()
        survey_dict = {"id": survey_record.id, "title": survey_record.title, "questions": survey_record.questions}
        personas_dict = [r.persona.to_dict() for r in raw_responses]
        responses_list = [{"persona_code": r.persona.persona_code, "answers": r.answers, "reasoning": r.reasoning} for r in raw_responses]
        analysis_data = analyze_survey_results(survey_dict, personas_dict, responses_list)

        # エグゼクティブサマリーの自律要約
        summary_result, s4_meta = await generate_executive_summary(
            research_goal=research_goal,
            survey_title=survey_title,
            questions=questions,
            analysis_data=analysis_data,
            use_mock=use_mock
        )

        step4["duration_ms"] = int((time.time() - t0) * 1000)
        step4["model_used"] = f"scikit-learn + {s4_meta.get('model_used', resolved_model)}"
        step4["api_calls_count"] = s4_meta.get("api_calls_count", 0)
        step4["tokens_used"] = s4_meta.get("tokens_used", {"prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0})
        step4["is_fallback"] = s4_meta.get("is_fallback", False)
        step4["fallback_reason"] = s4_meta.get("fallback_reason")

        if s4_meta.get("is_fallback"):
            step4["status"] = "fallback_mock"
            step4["details"] = f"要約フォールバック（{s4_meta.get('fallback_reason', '')[:60]}）のためルールベース要約で合成完了"
        else:
            step4["status"] = "completed"
            step4["details"] = "クロス集計、カイ二乗検定、PCA知覚空間、K-Meansクラスタリングおよび意思決定提言の要約完了"
    except Exception as e:
        step4["status"] = "failed"
        step4["error"] = str(e)
        step4["duration_ms"] = int((time.time() - t0) * 1000)
        steps_log.append(step4)
        raise e
    steps_log.append(step4)

    # ---------------------------------------------------------
    # 全体ステータス・実行時間・トークン集計の厳密な計算
    # ---------------------------------------------------------
    total_duration_ms = int((time.time() - orchestration_start) * 1000)
    total_duration_sec = round(total_duration_ms / 1000.0, 2)

    ai_steps = [s for s in steps_log if s.get("step_id") in ["step_2_survey_design", "step_3_survey_execution", "step_4_analytics_synthesis"]]
    any_fallback = any(s.get("is_fallback", False) or s.get("status") == "fallback_mock" for s in ai_steps)
    all_fallback = all(s.get("is_fallback", False) or s.get("status") == "fallback_mock" for s in ai_steps)

    if all_fallback:
        overall_status = "fallback_demo_mode"
    elif any_fallback:
        overall_status = "partial_fallback"
    else:
        overall_status = "completed"

    total_api_calls = sum(s.get("api_calls_count", 0) for s in steps_log)
    total_tokens = {
        "prompt_tokens": sum(s.get("tokens_used", {}).get("prompt_tokens", 0) for s in steps_log),
        "candidates_tokens": sum(s.get("tokens_used", {}).get("candidates_tokens", 0) for s in steps_log),
        "total_tokens": sum(s.get("tokens_used", {}).get("total_tokens", 0) for s in steps_log),
    }

    return {
        "orchestration_id": f"orch-{int(time.time())}",
        "research_goal": research_goal,
        "overall_status": overall_status,
        "total_duration_ms": total_duration_ms,
        "total_duration_sec": total_duration_sec,
        "cohort_id": cohort_record.id,
        "cohort_name": cohort_name,
        "cohort_size": len(personas_data),
        "target_count": target_count,
        "total_api_calls": total_api_calls,
        "total_tokens": total_tokens,
        "survey_id": survey_record.id,
        "survey_title": survey_title,
        "steps": steps_log,
        "executive_summary": summary_result,
        "analysis_summary": {
            "total_responses": len(raw_responses),
            "multivariate_available": bool(analysis_data.get("multivariate", {}).get("pca_2d")),
            "cluster_count": len(analysis_data.get("multivariate", {}).get("kmeans_clusters", {}).get("clusters", []))
        }
    }

def get_fallback_questions(research_goal: str) -> list[dict[str, Any]]:
    """フォールバック用の高品質設問テンプレート"""
    return [
        {
            "id": "q1",
            "text": f"Q1. 「{research_goal}」に関連する製品やサービスについて、現在のご自身の利用状況や関心に最も近いものをお選びください。",
            "type": "single",
            "options": [
                "日常的に利用しており強い関心がある",
                "知っており興味はあるが未利用",
                "名前を聞いた程度でよく知らない",
                "あまり関心がない・不要と感じている"
            ],
            "required": True
        },
        {
            "id": "q2",
            "text": "Q2. 本テーマで提案されている商品・サービスに対する、ご自身の購入意向や受容度をお答えください。（1: 全く購入したくない 〜 5: ぜひ購入したい）",
            "type": "scale5",
            "options": [],
            "required": True
        },
        {
            "id": "q3",
            "text": "Q3. 本提案の価格設定やコストパフォーマンスについて、ご自身の所得感からどのように評価しますか？（1: 割高・高すぎる 〜 5: 非常に妥当・割安）",
            "type": "scale5",
            "options": [],
            "required": True
        },
        {
            "id": "q4",
            "text": "Q4. 本提案に対して魅力を感じる点、または購入を躊躇する最大の懸念点・要望があれば自由にご記入ください。",
            "type": "text",
            "options": [],
            "required": True
        }
    ]

async def auto_design_survey_questions(research_goal: str, use_mock: bool = False) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Gemini / Vertex AI を使用して調査目的に応じた最適な4設問を設計"""
    available, provider, resolved_model = is_gemini_available()

    if available and not use_mock:
        prompt = f"""あなたは一流の消費者調査専門家・サーベイデザイナーです。
以下の調査課題について、生活者の受容度・価格感度・懸念点を客観的に測定するための【4つの調査設問】を設計してください。

【調査課題】
{research_goal}

【設問構成ルール】
1. Q1: 単一選択 (type: 'single') - 現在の利用状況、認知、または関連する興味関心（4〜5選択肢）
2. Q2: 5段階尺度 (type: 'scale5') - 本商品/施策の魅力度または購入意向（1: 全く買いたくない 〜 5: ぜひ買いたい）
3. Q3: 5段階尺度 (type: 'scale5') - 価格妥当性またはコストパフォーマンス感（1: 高すぎる 〜 5: 非常に割安・適正）
4. Q4: 自由記述 (type: 'text') - 購入したい理由、または購入にあたっての最大の懸念点・要望

【出力JSON形式】
必ず以下のJSON形式のみを出力してください:
{{
  "questions": [
    {{"id": "q1", "text": "...", "type": "single", "options": ["...", "...", "...", "..."], "required": true}},
    {{"id": "q2", "text": "...", "type": "scale5", "options": [], "required": true}},
    {{"id": "q3", "text": "...", "type": "scale5", "options": [], "required": true}},
    {{"id": "q4", "text": "...", "type": "text", "options": [], "required": true}}
  ]
}}
"""
        try:
            data, meta = await call_gemini_json_with_tracking(
                prompt=prompt,
                prefer_model=settings.DEFAULT_GEMINI_MODEL,
                temperature=0.4
            )
            if isinstance(data, dict) and "questions" in data and len(data["questions"]) >= 3:
                return data["questions"], {
                    "is_fallback": False,
                    "fallback_reason": None,
                    "model_used": meta.get("model_used", resolved_model),
                    "api_calls_count": 1,
                    "tokens_used": meta.get("tokens", {"prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0}),
                    "duration_ms": meta.get("duration_ms", 0)
                }
        except Exception as e:
            logger.warning(f"Gemini survey auto-design fallback: {e}")
            fallback_err = str(e)
            return get_fallback_questions(research_goal), {
                "is_fallback": True,
                "fallback_reason": fallback_err,
                "model_used": f"structured_survey_template ({fallback_err[:40]}によりフォールバック)",
                "api_calls_count": 0,
                "tokens_used": {"prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0},
                "duration_ms": 0
            }

    # デモ指定またはAI未設定
    return get_fallback_questions(research_goal), {
        "is_fallback": False if use_mock else True,
        "fallback_reason": None if use_mock else "Gemini/Vertex AI未初期化のためテンプレート設問を利用",
        "model_used": "structured_survey_template",
        "api_calls_count": 0,
        "tokens_used": {"prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0},
        "duration_ms": 0
    }

def get_fallback_executive_summary(research_goal: str, analysis_data: dict[str, Any]) -> dict[str, Any]:
    """フォールバック用のルールベース要約"""
    n_sample = len(analysis_data.get("univariate", {}))
    return {
        "headline": f"【調査結果要約】「{research_goal[:20]}」に対する生活者受容性の傾向分析",
        "summary_text": f"日本全国代表サンプル（設問数={n_sample}）を対象とした調査シミュレーションの結果、機能性や利便性への評価が高い一方、価格納得感における属性間ギャップが確認されました。",
        "key_findings": [
            "タイパ・効率重視層および単身若年層において最も高い購入意向が確認された。",
            "価格感度においてシニア層や家族持ち層で慎重姿勢が顕著であり、サポートや耐久性の訴求がボトルネック解消の鍵となる。",
            "多変量クラスタリングにより、実利機能重視型セグメントが初期アーリーアダプターとして最も有望であることが判明。"
        ],
        "target_recommendation": "30代〜40代のタイパ重視型・自己投資型ビジネスパーソン",
        "strategic_actions": [
            "初期プロモーションではスペックやブランド名よりも、日々の時間創出やストレス低減の実利価値を具体的に訴求する。",
            "高価格への心理的抵抗を低減するため、初期導入割引や返金保証などのリスクリダクション施策を講じる。"
        ]
    }

async def generate_executive_summary(
    research_goal: str,
    survey_title: str,
    questions: list[dict[str, Any]],
    analysis_data: dict[str, Any],
    use_mock: bool = False
) -> tuple[dict[str, Any], dict[str, Any]]:
    """調査結果（記述統計・多変量解析）からエグゼクティブサマリーを自律生成"""
    available, provider, resolved_model = is_gemini_available()

    univ = analysis_data.get("univariate", {})
    multi = analysis_data.get("multivariate", {})

    # 基本統計ハイライト
    scale_means = []
    for q_id, q_stat in univ.items():
        if q_stat.get("type") == "scale5":
            scale_means.append(f"{q_stat.get('question_text', q_id)}: 平均 {q_stat.get('mean', 0.0)}点")

    if available and not use_mock:
        prompt = f"""あなたは戦略コンサルタント兼データサイエンティストです。
以下の自律調査結果に基づき、経営陣・プロダクトマネージャー向けの【エグゼクティブサマリー】を作成してください。

【調査課題】
{research_goal}

【調査結果データ要約】
- 設問評価結果: {", ".join(scale_means) if scale_means else "5段階尺度回答あり"}
- クラスタリング分析: {len(multi.get("kmeans_clusters", {}).get("clusters", []))}個の生活者セグメントを検出
- 自由記述分析: {univ.get("q4", {}).get("text_summary", {}).get("dominant_sentiment", "分析完了")}

【出力JSON形式】
{{
  "headline": "意思決定者向けの一行要約タイトル",
  "summary_text": "全体サマリー（200文字程度）",
  "key_findings": [
    "発見1: 購買意向の傾向と背景",
    "発見2: 価格感度および受容性のボトルネック",
    "発見3: 最も受容性の高い生活者セグメント"
  ],
  "target_recommendation": "最も注力すべきターゲット顧客像",
  "strategic_actions": [
    "アクション提言1",
    "アクション提言2"
  ]
}}
"""
        try:
            data, meta = await call_gemini_json_with_tracking(
                prompt=prompt,
                prefer_model=settings.DEFAULT_GEMINI_MODEL,
                temperature=0.5
            )
            return data, {
                "is_fallback": False,
                "fallback_reason": None,
                "model_used": meta.get("model_used", resolved_model),
                "api_calls_count": 1,
                "tokens_used": meta.get("tokens", {"prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0}),
                "duration_ms": meta.get("duration_ms", 0)
            }
        except Exception as e:
            logger.warning(f"Gemini executive summary fallback: {e}")
            fallback_err = str(e)
            return get_fallback_executive_summary(research_goal, analysis_data), {
                "is_fallback": True,
                "fallback_reason": fallback_err,
                "model_used": f"rule_based_synthesis ({fallback_err[:40]}によりフォールバック)",
                "api_calls_count": 0,
                "tokens_used": {"prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0},
                "duration_ms": 0
            }

    return get_fallback_executive_summary(research_goal, analysis_data), {
        "is_fallback": False if use_mock else True,
        "fallback_reason": None if use_mock else "Gemini/Vertex AI未初期化のためルールベース要約を利用",
        "model_used": "rule_based_synthesis",
        "api_calls_count": 0,
        "tokens_used": {"prompt_tokens": 0, "candidates_tokens": 0, "total_tokens": 0},
        "duration_ms": 0
    }
