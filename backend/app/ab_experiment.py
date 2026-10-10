import io
import csv
import json
import logging
import math
import random
from typing import Any
import numpy as np
from scipy import stats
from .config import settings, has_gemini_api_key

logger = logging.getLogger(__name__)

async def run_virtual_ab_experiment(
    cohort_personas: list[dict[str, Any]],
    experiment_title: str,
    research_question: str,
    control_condition: dict[str, Any],
    treatment_condition: dict[str, Any],
    order_design: str = "counterbalanced", # "counterbalanced" or "randomized"
    use_mock: bool = False,
    sample_size: int = 50
) -> dict[str, Any]:
    """仮想A/B実験（Control vs Treatment）の実行と統計的効果量（Cohen's d, Δμ）の算出
    
    Gemini 3.8 Flashによる自律エージェント評価モードと、
    明示的なルールベース・デモモード（heuristic_demo）をサポート。
    """
    n_total = len(cohort_personas)
    if n_total == 0:
        raise ValueError("Cohort has no personas")

    # 実験対象のサンプリング（指定サイズまたはコホート全体）
    selected_personas = cohort_personas[:sample_size] if sample_size and sample_size < n_total else cohort_personas
    n_exp = len(selected_personas)

    # 各被験者への提示順序割り当て
    personas_with_order = []
    for idx, p in enumerate(selected_personas):
        if order_design == "counterbalanced":
            order = ["control", "treatment"] if idx % 2 == 0 else ["treatment", "control"]
        else:
            order = ["control", "treatment"] if random.random() < 0.5 else ["treatment", "control"]
        personas_with_order.append((p, order))

    engine_type = "gemini_agent"
    model_name = settings.DEFAULT_GEMINI_MODEL
    is_demo_mode = False
    fallback_warning = None

    individual_results = []
    control_scores = {"purchase_intent": [], "perceived_value": [], "price_fairness": [], "recommendation_likelihood": []}
    treatment_scores = {"purchase_intent": [], "perceived_value": [], "price_fairness": [], "recommendation_likelihood": []}

    from .gemini_service import is_gemini_available
    available, provider, resolved_model = is_gemini_available()
    can_use_gemini = available and not use_mock

    if can_use_gemini:

        try:
            # Gemini 3.8 Flash によるバッチ評価
            gemini_evals = await evaluate_cohort_with_gemini(
                personas_with_order,
                control_condition,
                treatment_condition,
                model_name=model_name
            )
            for (p, order), ev in zip(personas_with_order, gemini_evals):
                p_ctrl = ev["control"]
                p_treat = ev["treatment"]
                for metric in control_scores:
                    control_scores[metric].append(p_ctrl[metric])
                    treatment_scores[metric].append(p_treat[metric])

                individual_results.append({
                    "persona_code": p["persona_code"],
                    "name": p["name"],
                    "age": p["age"],
                    "age_group": p["age_group"],
                    "gender": p["gender"],
                    "income": p["personal_income"],
                    "values_segment": p["values_segment"],
                    "presentation_order": " -> ".join(order),
                    "control": p_ctrl,
                    "treatment": p_treat,
                    "control_reason": p_ctrl.get("reason", ""),
                    "treatment_reason": p_treat.get("reason", ""),
                    "delta_purchase_intent": p_treat["purchase_intent"] - p_ctrl["purchase_intent"]
                })

            engine_type = "gemini_agent"
            is_demo_mode = False

        except Exception as e:
            logger.error(f"Gemini A/B evaluation failed: {e}. Falling back to heuristic mock.")
            engine_type = "mock_fallback"
            is_demo_mode = True
            fallback_warning = f"Gemini API実行エラー（{str(e)[:120]}）のため、ヒューリスティック・モック生成に切り替えました。実AI推論データとして集計・保存しないでください。"

            # フォールバック処理
            individual_results.clear()
            for metric in control_scores:
                control_scores[metric].clear()
                treatment_scores[metric].clear()

            for p, order in personas_with_order:
                p_ctrl, p_treat = simulate_individual_ab_scores(p, control_condition, treatment_condition)
                for metric in control_scores:
                    control_scores[metric].append(p_ctrl[metric])
                    treatment_scores[metric].append(p_treat[metric])

                individual_results.append({
                    "persona_code": p["persona_code"],
                    "name": p["name"],
                    "age": p["age"],
                    "age_group": p["age_group"],
                    "gender": p["gender"],
                    "income": p["personal_income"],
                    "values_segment": p["values_segment"],
                    "presentation_order": " -> ".join(order),
                    "control": p_ctrl,
                    "treatment": p_treat,
                    "control_reason": "（ルールベース・デモ採点）",
                    "treatment_reason": "（ルールベース・デモ採点）",
                    "delta_purchase_intent": p_treat["purchase_intent"] - p_ctrl["purchase_intent"]
                })
    else:
        # 明示的なルールベース方式（デモモード）
        engine_type = "heuristic_demo"
        model_name = "heuristic_rule_engine"
        is_demo_mode = True
        if use_mock:
            fallback_warning = "【明示的デモモード】ルールベース（ヒューリスティック相関モデル）によるシミュレーション結果です（Gemini API不使用）。"
        else:
            fallback_warning = "【Gemini API未設定】APIキーが未検出のため、ルールベース・デモモードでシミュレーションを実行しました。"

        for p, order in personas_with_order:
            p_ctrl, p_treat = simulate_individual_ab_scores(p, control_condition, treatment_condition)
            for metric in control_scores:
                control_scores[metric].append(p_ctrl[metric])
                treatment_scores[metric].append(p_treat[metric])

            individual_results.append({
                "persona_code": p["persona_code"],
                "name": p["name"],
                "age": p["age"],
                "age_group": p["age_group"],
                "gender": p["gender"],
                "income": p["personal_income"],
                "values_segment": p["values_segment"],
                "presentation_order": " -> ".join(order),
                "control": p_ctrl,
                "treatment": p_treat,
                "control_reason": "（ルールベース・デモ採点）",
                "treatment_reason": "（ルールベース・デモ採点）",
                "delta_purchase_intent": p_treat["purchase_intent"] - p_ctrl["purchase_intent"]
            })

    # 各指標の統計分析（平均、標準偏差、差分、Cohen's d、t検定）
    metric_analysis = {}
    for metric in control_scores:
        c_arr = np.array(control_scores[metric])
        t_arr = np.array(treatment_scores[metric])

        c_mean = float(np.mean(c_arr))
        t_mean = float(np.mean(t_arr))
        c_std = float(np.std(c_arr, ddof=1)) if len(c_arr) > 1 else 0.0
        t_std = float(np.std(t_arr, ddof=1)) if len(t_arr) > 1 else 0.0

        diff_arr = t_arr - c_arr
        mean_diff = float(np.mean(diff_arr))
        pct_diff = float((mean_diff / c_mean) * 100.0) if c_mean > 0 else 0.0

        # Pooled Standard Deviation & Cohen's d
        s_pooled = math.sqrt(((c_std ** 2) + (t_std ** 2)) / 2.0) if (c_std > 0 or t_std > 0) else 1e-6
        cohens_d = float(mean_diff / s_pooled)

        # 対応のあるt検定 (Paired t-test)
        if len(t_arr) > 1 and np.any(diff_arr != 0):
            t_stat, p_val = stats.ttest_rel(t_arr, c_arr)
        else:
            t_stat, p_val = 0.0, 1.0

        metric_analysis[metric] = {
            "control_mean": round(c_mean, 2),
            "control_std": round(c_std, 2),
            "treatment_mean": round(t_mean, 2),
            "treatment_std": round(t_std, 2),
            "delta_mean": round(mean_diff, 2),
            "percentage_change": round(pct_diff, 1),
            "cohens_d": round(cohens_d, 3),
            "effect_size_label": get_effect_size_label(cohens_d),
            "t_statistic": round(float(t_stat), 3) if not math.isnan(t_stat) else 0.0,
            "p_value": round(float(p_val), 4) if not math.isnan(p_val) else 1.0,
            "is_statistically_significant": bool(p_val < 0.05) if not math.isnan(p_val) else False
        }

    subgroups = compute_subgroup_effects(individual_results)

    return {
        "title": experiment_title,
        "research_question": research_question,
        "sample_size": n_exp,
        "total_cohort_size": n_total,
        "order_design": order_design,
        "engine_type": engine_type,
        "model_name": model_name,
        "is_demo_mode": is_demo_mode,
        "fallback_warning": fallback_warning,
        "control_condition": control_condition,
        "treatment_condition": treatment_condition,
        "metric_analysis": metric_analysis,
        "subgroups": subgroups,
        "individual_results": individual_results,
        "academic_reference": {
            "paper": "Large Language Models Can Predict the Results of Social Science Experiments (Nature 2026)",
            "methodology": "Within-subject randomized/counterbalanced evaluation across persona cohorts",
            "notes": "本実験機能はNature 2026の研究成果に着想を得て設計された仮想A/B検証環境です。"
        },
        "simulation_disclaimer": "【重要】本効果量（Cohen's d）および統計的有意差はAIペルソナ集団の回答シミュレーションに基づく仮想的効果量であり、実在の母集団に対する因果効果（Average Treatment Effect: ATE）を保証するものではありません。"
    }

async def evaluate_cohort_with_gemini(
    personas_with_order: list[tuple[dict[str, Any], list[str]]],
    control_condition: dict[str, Any],
    treatment_condition: dict[str, Any],
    model_name: str = None,
    batch_size: int = 5
) -> list[dict[str, Any]]:
    """Gemini / Vertex AI にペルソナごとの提示順序を反映させたプロンプトでA/B評価を実行"""
    from .gemini_service import call_gemini_json_with_tracking


    all_evaluations = []

    for i in range(0, len(personas_with_order), batch_size):
        batch = personas_with_order[i:i+batch_size]

        # プロンプトの組み立て（被験者ごとにCondition 1とCondition 2の提示順序を厳密に指示）
        prompt_parts = [
            "あなたは社会科学実験・消費者受容性検証（Nature 2026準拠）の自律的マルチエージェント評価エンジンです。",
            "以下の複数名の生活者ペルソナ本人として自律的に思考し、指定された提示順序（Condition 1 -> Condition 2）で2つの提案内容を直感的に評価してください。",
            "",
            "【実験条件の定義】",
            f"● [Control (統制群)]: {control_condition.get('label', '通常仕様')}",
            f"  - 説明: {control_condition.get('description', '')}",
            f"  - 価格: {control_condition.get('price', 0):,}円",
            f"  - 広告訴求: {control_condition.get('ad_copy', '')}",
            "",
            f"● [Treatment (実験群)]: {treatment_condition.get('label', '新提案')}",
            f"  - 説明: {treatment_condition.get('description', '')}",
            f"  - 価格: {treatment_condition.get('price', 0):,}円",
            f"  - 広告訴求: {treatment_condition.get('ad_copy', '')}",
            "",
            "【評価尺度（1〜5の整数）】",
            "1. purchase_intent: 購入意向 (1: 全く買いたくない 〜 5: ぜひ買いたい)",
            "2. perceived_value: 価値実感・魅力度 (1: 魅力を感じない 〜 5: 非常に魅力的)",
            "3. price_fairness: 価格の納得感・妥当性 (1: 不当に高い 〜 5: 非常に妥当・割安)",
            "4. recommendation_likelihood: 推奨意向 (1: 全く勧めない 〜 5: 強く勧めたい)",
            "5. reason: ペルソナ本人の口調での評価理由（簡潔に1文）",
            "",
            "【評価対象ペルソナと提示順序】"
        ]

        for p, order in batch:
            first_cond = order[0]
            second_cond = order[1]
            grounded_quote = ""
            if p.get("grounded_interview"):
                quotes = p["grounded_interview"].get("extracted_data", {}).get("verbatim_quotes", [])
                if quotes:
                    grounded_quote = f" 生の声: 「{quotes[0]}」"

            prompt_parts.append(
                f"- ID: {p['persona_code']} | 氏名: {p['name']} | 年代性別: {p['age']}歳{p['gender']} | 年収: {p['personal_income']}万円 | 価値観: {p['values_segment']}{grounded_quote}\n"
                f"  【重要：提示順序】まず第1提示 [{first_cond.upper()}] を評価した直後に、第2提示 [{second_cond.upper()}] を評価してください。"
            )

        prompt_parts.append("")
        prompt_parts.append("【出力形式】")
        prompt_parts.append("以下のJSON形式のみを出力してください:")
        prompt_parts.append("""{
  "evaluations": [
    {
      "persona_code": "P-XXXX",
      "control": {
        "purchase_intent": 3,
        "perceived_value": 3,
        "price_fairness": 3,
        "recommendation_likelihood": 2,
        "reason": "..."
      },
      "treatment": {
        "purchase_intent": 4,
        "perceived_value": 4,
        "price_fairness": 4,
        "recommendation_likelihood": 4,
        "reason": "..."
      }
    }
  ]
}""")

        prompt = "\n".join(prompt_parts)

        data, meta = await call_gemini_json_with_tracking(
            prompt=prompt,
            prefer_model=model_name or settings.DEFAULT_GEMINI_MODEL,
            temperature=0.6
        )
        eval_list = data.get("evaluations", []) if isinstance(data, dict) else []
        eval_map = {e["persona_code"]: e for e in eval_list if isinstance(e, dict) and "persona_code" in e}


        # バッチ内の各ペルソナの結果を整理
        for p, order in batch:
            p_code = p["persona_code"]
            if p_code in eval_map:
                ev = eval_map[p_code]
                c_data = ev.get("control", {})
                t_data = ev.get("treatment", {})
                all_evaluations.append({
                    "persona_code": p_code,
                    "control": {
                        "purchase_intent": int(np.clip(c_data.get("purchase_intent", 3), 1, 5)),
                        "perceived_value": int(np.clip(c_data.get("perceived_value", 3), 1, 5)),
                        "price_fairness": int(np.clip(c_data.get("price_fairness", 3), 1, 5)),
                        "recommendation_likelihood": int(np.clip(c_data.get("recommendation_likelihood", 3), 1, 5)),
                        "reason": str(c_data.get("reason", ""))
                    },
                    "treatment": {
                        "purchase_intent": int(np.clip(t_data.get("purchase_intent", 3), 1, 5)),
                        "perceived_value": int(np.clip(t_data.get("perceived_value", 3), 1, 5)),
                        "price_fairness": int(np.clip(t_data.get("price_fairness", 3), 1, 5)),
                        "recommendation_likelihood": int(np.clip(t_data.get("recommendation_likelihood", 3), 1, 5)),
                        "reason": str(t_data.get("reason", ""))
                    }
                })
            else:
                # バッチ内にキーが欠損していた場合はルールベースで補完
                c_mock, t_mock = simulate_individual_ab_scores(p, control_condition, treatment_condition)
                all_evaluations.append({
                    "persona_code": p_code,
                    "control": c_mock,
                    "treatment": t_mock
                })

    return all_evaluations

def simulate_individual_ab_scores(persona: dict[str, Any], ctrl: dict[str, Any], treat: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """個々のペルソナ属性に基づくControlとTreatmentのシミュレーション採点（明示的ルールベース方式）"""
    values = persona.get("values_segment", "")
    age = persona.get("age", 40)
    income = persona.get("personal_income", 450)

    # Baseline scores (1-5)
    c_base = 2.8
    t_base = 2.8

    # 価格差
    c_price = ctrl.get("price", 1000)
    t_price = treat.get("price", 1000)
    price_diff_ratio = (t_price - c_price) / max(1, c_price)

    # 価値観による受容性の変動
    t_copy = str(treat.get("ad_copy", "") + " " + treat.get("description", "")).lower()

    # エコ・サステナブル訴求の場合
    if any(k in t_copy for k in ["エコ", "サステナブル", "地球", "環境", "再生", "森林"]):
        if values == "サステナビリティ・エシカル":
            t_base += 0.9
        elif values == "健康・ウェルネス投資":
            t_base += 0.5
        elif age < 35:
            t_base += 0.4

    # コスパ訴求または値上げに対する抵抗
    if price_diff_ratio > 0.15:
        if values == "コスパ・実利重視" or income < 400:
            t_base -= 0.6
        else:
            t_base -= 0.2
    elif price_diff_ratio < -0.15:
        if values == "コスパ・実利重視":
            t_base += 0.7

    c_pi = np.clip(int(round(np.random.normal(c_base, 0.7))), 1, 5)
    t_pi = np.clip(int(round(np.random.normal(t_base, 0.7))), 1, 5)

    c_val = np.clip(int(round(np.random.normal(c_base + 0.2, 0.6))), 1, 5)
    t_val = np.clip(int(round(np.random.normal(t_base + 0.3, 0.6))), 1, 5)

    c_pf = np.clip(int(round(np.random.normal(3.2 - (c_price/2000), 0.6))), 1, 5)
    t_pf = np.clip(int(round(np.random.normal(3.2 - (t_price/2000), 0.6))), 1, 5)

    c_nps = np.clip(int(round(c_pi * 0.8 + c_val * 0.2)), 1, 5)
    t_nps = np.clip(int(round(t_pi * 0.8 + t_val * 0.2)), 1, 5)

    ctrl_res = {
        "purchase_intent": int(c_pi),
        "perceived_value": int(c_val),
        "price_fairness": int(c_pf),
        "recommendation_likelihood": int(c_nps),
        "reason": "現状の価格と仕様に一定の納得感があるため"
    }

    treat_res = {
        "purchase_intent": int(t_pi),
        "perceived_value": int(t_val),
        "price_fairness": int(t_pf),
        "recommendation_likelihood": int(t_nps),
        "reason": "新機能と価格設定のバランスを魅力的に感じるため"
    }

    return ctrl_res, treat_res

def get_effect_size_label(d: float) -> str:
    abs_d = abs(d)
    if abs_d < 0.2:
        return "微小 (Negligible |d| < 0.2)"
    elif abs_d < 0.5:
        return "小 (Small 0.2 ≤ |d| < 0.5)"
    elif abs_d < 0.8:
        return "中 (Medium 0.5 ≤ |d| < 0.8)"
    else:
        return "大 (Large |d| ≥ 0.8)"

def compute_subgroup_effects(individual_results: list[dict[str, Any]]) -> dict[str, Any]:
    """属性別の平均差と効果量の集計"""
    by_gender = {"男性": [], "女性": []}
    by_age = {"20代": [], "30代": [], "40代": [], "50代": [], "60代": [], "70代以上": []}
    by_values = {}

    for r in individual_results:
        diff = r["delta_purchase_intent"]
        g = r.get("gender", "その他")
        if g in by_gender:
            by_gender[g].append(diff)

        ag = r.get("age_group", "40代")
        if ag in by_age:
            by_age[ag].append(diff)

        v = r.get("values_segment", "その他")
        if v not in by_values:
            by_values[v] = []
        by_values[v].append(diff)

    def calc_group_stats(group_dict):
        out = {}
        for k, v_list in group_dict.items():
            if not v_list:
                continue
            mean_diff = float(np.mean(v_list))
            std_diff = float(np.std(v_list, ddof=1)) if len(v_list) > 1 else 1e-5
            d = mean_diff / (std_diff if std_diff > 0 else 1.0)
            out[k] = {
                "count": len(v_list),
                "delta_mean": round(mean_diff, 2),
                "cohens_d": round(float(d), 3)
            }
        return out

    return {
        "by_gender": calc_group_stats(by_gender),
        "by_age": calc_group_stats(by_age),
        "by_values": calc_group_stats(by_values)
    }

def export_ab_experiment_csv(experiment_data: dict[str, Any]) -> str:
    """A/B実験の個票データCSV出力（UTF-8 BOM付き）"""
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)

    writer.writerow([
        "ペルソナID", "氏名", "年代", "性別", "年収(万円)", "消費価値観", "提示順序",
        "Control_購入意向(1-5)", "Treatment_購入意向(1-5)", "購入意向差分(Treatment-Control)",
        "Control_価値実感(1-5)", "Treatment_価値実感(1-5)",
        "Control_価格妥当性(1-5)", "Treatment_価格妥当性(1-5)",
        "Control_評価理由", "Treatment_評価理由"
    ])

    for r in experiment_data.get("individual_results", []):
        writer.writerow([
            r["persona_code"],
            r["name"],
            r["age_group"],
            r["gender"],
            r["income"],
            r["values_segment"],
            r["presentation_order"],
            r["control"]["purchase_intent"],
            r["treatment"]["purchase_intent"],
            r["delta_purchase_intent"],
            r["control"]["perceived_value"],
            r["treatment"]["perceived_value"],
            r["control"]["price_fairness"],
            r["treatment"]["price_fairness"],
            r.get("control_reason", ""),
            r.get("treatment_reason", "")
        ])

    return output.getvalue()
