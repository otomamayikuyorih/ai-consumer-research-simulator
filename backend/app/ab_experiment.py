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
    use_mock: bool = False
) -> dict[str, Any]:
    """仮想A/B実験（Control vs Treatment）の実行と統計的効果量（Cohen's d, Δμ）の算出"""
    n_total = len(cohort_personas)
    if n_total == 0:
        raise ValueError("Cohort has no personas")

    # 条件提示順序のカウンターバランスまたはランダム化
    individual_results = []
    
    # 評価指標（1〜5のLikert尺度）
    # 1: purchase_intent (購入意向)
    # 2: perceived_value (価値実感・魅力度)
    # 3: price_fairness (価格の納得感・妥当性)
    # 4: recommendation_likelihood (推奨意向)

    control_scores = {"purchase_intent": [], "perceived_value": [], "price_fairness": [], "recommendation_likelihood": []}
    treatment_scores = {"purchase_intent": [], "perceived_value": [], "price_fairness": [], "recommendation_likelihood": []}

    for idx, p in enumerate(cohort_personas):
        # 順序の割り当て
        if order_design == "counterbalanced":
            # 前半は Control -> Treatment、後半は Treatment -> Control
            order = ["control", "treatment"] if idx % 2 == 0 else ["treatment", "control"]
        else:
            order = ["control", "treatment"] if random.random() < 0.5 else ["treatment", "control"]

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
        t_stat, p_val = stats.ttest_rel(t_arr, c_arr)

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

    # 属性別サブグループ効果分析（購入意向に関する属性別の効果量と平均差）
    subgroups = compute_subgroup_effects(individual_results)

    return {
        "title": experiment_title,
        "research_question": research_question,
        "sample_size": n_total,
        "order_design": order_design,
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

def simulate_individual_ab_scores(persona: dict[str, Any], ctrl: dict[str, Any], treat: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """個々のペルソナ属性に基づくControlとTreatmentのシミュレーション採点"""
    values = persona.get("values_segment", "")
    age = persona.get("age", 40)
    income = persona.get("personal_income", 450)
    gender = persona.get("gender", "男性")
    mode = persona.get("generation_mode", "mode_b")

    # Baseline scores (1-5)
    c_base = 2.8
    t_base = 2.8

    # 価格差
    c_price = ctrl.get("price", 1000)
    t_price = treat.get("price", 1000)
    price_diff_ratio = (t_price - c_price) / max(1, c_price)

    # 価値観による受容性の変動
    t_copy = str(treat.get("ad_copy", "") + " " + treat.get("description", "")).lower()
    c_copy = str(ctrl.get("ad_copy", "") + " " + ctrl.get("description", "")).lower()

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

    # Mode C (インタビュー接地) の場合は、インタビューで抽出された価格感度やキーワードを反映
    if mode == "mode_c":
        grounded = persona.get("grounded_interview", {})
        price_sens = str(grounded.get("price_sensitivity", ""))
        if "惜しみなく" in price_sens or "許容" in price_sens:
            t_base += 0.3
        elif "シビア" in price_sens or "削減" in price_sens:
            t_base -= 0.3

    # ノイズの付加
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
        "recommendation_likelihood": int(c_nps)
    }

    treat_res = {
        "purchase_intent": int(t_pi),
        "perceived_value": int(t_val),
        "price_fairness": int(t_pf),
        "recommendation_likelihood": int(t_nps)
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
    # Excel文字化け防止 BOM
    output.write('\ufeff')
    writer = csv.writer(output)

    writer.writerow([
        "ペルソナID", "氏名", "年代", "性別", "年収(万円)", "消費価値観", "提示順序",
        "Control_購入意向(1-5)", "Treatment_購入意向(1-5)", "購入意向差分(Treatment-Control)",
        "Control_価値実感(1-5)", "Treatment_価値実感(1-5)",
        "Control_価格妥当性(1-5)", "Treatment_価格妥当性(1-5)"
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
            r["treatment"]["price_fairness"]
        ])

    return output.getvalue()
