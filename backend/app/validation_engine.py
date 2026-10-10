import csv
import io
import json
import logging
import math
from typing import Any, Optional
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

def generate_demo_human_survey_data(questions: list[dict[str, Any]], count: int = 100) -> list[dict[str, Any]]:
    """検証用の架空の実測人間アンケート調査データ（デモ用であることを明示）"""
    records = []
    np.random.seed(123)

    for i in range(count):
        p_id = f"DEMO-HUMAN-{i+1:04d}"
        age = int(np.random.randint(20, 75))
        age_group = f"{age // 10 * 10}代" if age < 70 else "70代以上"
        gender = "男性" if np.random.random() < 0.49 else "女性"

        answers = {}
        for q in questions:
            q_id = q["id"]
            q_type = q["type"]
            options = q.get("options", [])

            if q_type == "single":
                if options:
                    probs = np.ones(len(options))
                    probs[0] += 0.5
                    probs = probs / np.sum(probs)
                    answers[q_id] = str(np.random.choice(options, p=probs))
            elif q_type == "multiple":
                selected = []
                for opt in options:
                    if np.random.random() < 0.35:
                        selected.append(opt)
                if not selected and options:
                    selected.append(options[0])
                answers[q_id] = selected
            elif q_type == "scale5":
                score = int(np.clip(round(np.random.normal(3.1, 0.9)), 1, 5))
                answers[q_id] = score
            elif q_type == "text":
                answers[q_id] = "（実測デモ回答サンプル）価格とサポート体制に納得できれば購入を前向きに考えたいと思います。"

        records.append({
            "participant_id": p_id,
            "age": age,
            "age_group": age_group,
            "gender": gender,
            "answers": answers,
            "is_demo": True
        })
    return records

def parse_human_csv_data(csv_text: str, questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """ユーザーがアップロードした実測人間アンケートCSVのパース"""
    f = io.StringIO(csv_text.strip())
    reader = csv.DictReader(f)
    records = []

    for idx, row in enumerate(reader):
        p_id = row.get("participant_id") or row.get("ID") or f"HUMAN-{idx+1:04d}"
        age = int(row.get("age") or row.get("年齢") or 35)
        age_group = f"{age // 10 * 10}代" if age < 70 else "70代以上"
        gender = row.get("gender") or row.get("性別") or "不明"

        answers = {}
        for q in questions:
            q_id = q["id"]
            val = row.get(q_id) or row.get(q.get("text", "")) or row.get(f"q{idx+1}")
            if val is not None:
                if q["type"] == "scale5":
                    try:
                        answers[q_id] = int(val)
                    except:
                        answers[q_id] = 3
                elif q["type"] == "multiple":
                    answers[q_id] = [x.strip() for x in str(val).split(";") if x.strip()]
                else:
                    answers[q_id] = str(val).strip()
            else:
                answers[q_id] = q["options"][0] if q.get("options") else 3

        records.append({
            "participant_id": p_id,
            "age": age,
            "age_group": age_group,
            "gender": gender,
            "answers": answers,
            "is_demo": False
        })
    return records

def evaluate_human_ai_validation(
    ai_responses: list[dict[str, Any]],
    human_records: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    split_ratio: str = "50_50_split"
) -> dict[str, Any]:
    """Human vs AI 回答の比較検証エンジン
    
    【科学的信頼性の改善】
    - 疑似乱数による誤差捏造を完全排除（計算不能時はNone/NAを返却）
    - 実際のプロンプト校正がない場合は「校正済み・汎化検証済み」と謳わず、
      「Zero-shot折半サンプリング頑健性検証（Split-Half Robustness）」として透明に提示
    """
    if not human_records or not ai_responses:
        return {
            "status": "unvalidated",
            "message": "実測データまたはAI回答データが存在しません。検証は未完了（N/A）です。",
            "overall_metrics": {
                "overall_mae": None,
                "overall_rmse": None,
                "pearson_r": None,
                "question_level": {}
            },
            "split_half_evaluation": None,
            "subgroup_errors": {}
        }

    n_ai = len(ai_responses)
    n_human = len(human_records)
    is_demo = any(r.get("is_demo", False) for r in human_records)

    # 1. サンプリング折半分割 (Split-half sampling)
    np.random.seed(42)
    indices = np.random.permutation(n_human)
    split_point = n_human // 2 if split_ratio == "50_50_split" else int(n_human * 0.7)

    split1_human = [human_records[i] for i in indices[:split_point]]
    split2_human = [human_records[i] for i in indices[split_point:]]

    overall_metrics = compute_distribution_metrics(ai_responses, human_records, questions)
    split1_metrics = compute_distribution_metrics(ai_responses, split1_human, questions) if split1_human else None
    split2_metrics = compute_distribution_metrics(ai_responses, split2_human, questions) if split2_human else None

    # 属性別予測誤差（実計算のみ・乱数排除）
    subgroup_errors = compute_subgroup_errors(ai_responses, human_records, questions)

    # 個人単位の一致率
    individual_concordance = compute_individual_match(ai_responses, human_records, questions)

    # 折半誤差の差分（ロバストネス指標）
    mae_gap = None
    if split1_metrics and split2_metrics:
        m1 = split1_metrics.get("overall_mae")
        m2 = split2_metrics.get("overall_mae")
        if m1 is not None and m2 is not None:
            mae_gap = round(abs(m2 - m1), 3)

    return {
        "status": "completed",
        "is_demo_dataset": is_demo,
        "dataset_notice": "【注意】本検証はデモ用の架空実測データに基づいています。実在の人間の結果ではありません。" if is_demo else "実測アンケートデータに基づく実証比較結果です。",
        "human_sample_size": n_human,
        "ai_sample_size": n_ai,
        "calibration_performed": False,
        "evaluation_type": "zero_shot_split_half",
        "evaluation_type_label": "Zero-shot 折半サンプリング頑健性検証 (Split-Half Robustness)",
        "scientific_notice": (
            "【科学的透明性の注記】本システムは事後的なプロンプト過学習やパラメータ調整（キャリブレーション）を行わないZero-Shot推論エージェントです。"
            "したがって本50/50分割は『校正済みモデルの未知データ汎化性能』ではなく、人間回答データのサンプリングばらつきに対するZero-shot予測のロバストネス（安定性）を客観検証するものです。"
        ),
        "split_info": {
            "mode": split_ratio,
            "split_1_sample_size": len(split1_human),
            "split_2_sample_size": len(split2_human)
        },
        "overall_metrics": overall_metrics,
        "split_half_evaluation": {
            "split_1_metrics": split1_metrics,
            "split_2_metrics": split2_metrics,
            "mae_gap": mae_gap,
            "interpretation": "折半した2つの人間サンプル間での予測誤差（MAE）の差が極小であれば、サンプリング偏りに対してもAIの推論が一貫して安定していることを示します。"
        },
        "out_of_sample_validation": {
            "calibration_split": split1_metrics or {},
            "test_evaluation_split": split2_metrics or {},
            "note": "【後方互換性エイリアス】事後校正のないZero-shot折半サンプリング頑健性検証（split_half_evaluation）を参照してください。"
        },
        "subgroup_errors": subgroup_errors,
        "individual_concordance": individual_concordance
    }

def compute_distribution_metrics(ai_list: list[dict], human_list: list[dict], questions: list[dict]) -> dict[str, Any]:
    """選択肢ごとの出現割合を比較し、MAE, RMSE, Pearson r を計算（乱数やハードコードを一切排除）"""
    if not human_list or not ai_list:
        return {
            "overall_mae": None,
            "overall_rmse": None,
            "pearson_r": None,
            "question_level": {}
        }

    q_metrics = {}
    all_ai_probs = []
    all_human_probs = []

    for q in questions:
        q_id = q["id"]
        q_type = q["type"]
        options = q.get("options", [])

        if q_type in ["single", "multiple"]:
            if not options:
                continue
            human_counts = {opt: 0 for opt in options}
            ai_counts = {opt: 0 for opt in options}

            for r in human_list:
                ans = r["answers"].get(q_id)
                if q_type == "single" and ans in human_counts:
                    human_counts[ans] += 1
                elif q_type == "multiple" and isinstance(ans, list):
                    for a in ans:
                        if a in human_counts: human_counts[a] += 1

            for r in ai_list:
                ans = r["answers"].get(q_id)
                if q_type == "single" and ans in ai_counts:
                    ai_counts[ans] += 1
                elif q_type == "multiple" and isinstance(ans, list):
                    for a in ans:
                        if a in ai_counts: ai_counts[a] += 1

            total_h = len(human_list)
            total_ai = len(ai_list)

            h_dist = {opt: round(human_counts[opt] / total_h, 3) for opt in options}
            ai_dist = {opt: round(ai_counts[opt] / total_ai, 3) for opt in options}

            diffs = [abs(ai_dist[opt] - h_dist[opt]) for opt in options]
            mae = float(np.mean(diffs)) if diffs else 0.0
            rmse = float(np.sqrt(np.mean([d**2 for d in diffs]))) if diffs else 0.0

            for opt in options:
                all_human_probs.append(h_dist[opt])
                all_ai_probs.append(ai_dist[opt])

            q_metrics[q_id] = {
                "question_text": q["text"],
                "type": q_type,
                "human_proportions": h_dist,
                "ai_proportions": ai_dist,
                "mae": round(mae, 3),
                "rmse": round(rmse, 3)
            }

        elif q_type == "scale5":
            h_vals = [float(r["answers"][q_id]) for r in human_list if q_id in r.get("answers", {}) and r["answers"][q_id] is not None]
            ai_vals = [float(r["answers"][q_id]) for r in ai_list if q_id in r.get("answers", {}) and r["answers"][q_id] is not None]

            if not h_vals or not ai_vals:
                q_metrics[q_id] = {
                    "question_text": q["text"],
                    "type": "scale5",
                    "human_mean": None,
                    "ai_mean": None,
                    "mean_error": None,
                    "human_std": None,
                    "ai_std": None
                }
                continue

            h_mean = float(np.mean(h_vals))
            ai_mean = float(np.mean(ai_vals))
            h_std = float(np.std(h_vals))
            ai_std = float(np.std(ai_vals))

            # 5段階評価を1〜5の比率としても記録して相関係数に寄与
            for score in range(1, 6):
                all_human_probs.append(sum(1 for v in h_vals if round(v) == score) / len(h_vals))
                all_ai_probs.append(sum(1 for v in ai_vals if round(v) == score) / len(ai_vals))

            q_metrics[q_id] = {
                "question_text": q["text"],
                "type": "scale5",
                "human_mean": round(h_mean, 2),
                "ai_mean": round(ai_mean, 2),
                "mean_error": round(abs(ai_mean - h_mean), 2),
                "human_std": round(h_std, 2),
                "ai_std": round(ai_std, 2),
                "mae": round(abs(ai_mean - h_mean), 2),
                "rmse": round(abs(ai_mean - h_mean), 2)
            }

    # ピアソン相関係数（十分なデータと分散がある場合のみ実計算、それ以外はNone/NA）
    overall_r = None
    if len(all_human_probs) >= 3 and len(all_ai_probs) >= 3:
        std_h = float(np.std(all_human_probs))
        std_ai = float(np.std(all_ai_probs))
        if std_h > 1e-6 and std_ai > 1e-6:
            r_val, _ = stats.pearsonr(all_human_probs, all_ai_probs)
            if not math.isnan(r_val):
                overall_r = round(float(r_val), 3)

    valid_maes = [m["mae"] for m in q_metrics.values() if m.get("mae") is not None]
    valid_rmses = [m["rmse"] for m in q_metrics.values() if m.get("rmse") is not None]

    overall_mae = round(float(np.mean(valid_maes)), 3) if valid_maes else None
    overall_rmse = round(float(np.mean(valid_rmses)), 3) if valid_rmses else None

    return {
        "overall_mae": overall_mae,
        "overall_rmse": overall_rmse,
        "pearson_r": overall_r,
        "question_level": q_metrics
    }

def compute_subgroup_errors(ai_list: list[dict], human_list: list[dict], questions: list[dict]) -> dict[str, Any]:
    """年代別の予測誤差（MAE）を厳密に計算（乱数を完全排除し、未算出はNone/NA）"""
    target_q = next((q for q in questions if q["type"] in ["single", "scale5"]), None)
    if not target_q:
        return {}

    q_id = target_q["id"]
    age_groups = ["20代", "30代", "40代", "50代", "60代以上"]
    by_age = {}

    for ag in age_groups:
        h_sub = [r for r in human_list if ag in r.get("age_group", "")]
        ai_sub = [r for r in ai_list if ag in r.get("persona", {}).get("age_group", "")]

        if h_sub and ai_sub:
            if target_q["type"] == "scale5":
                h_vals = [float(r["answers"].get(q_id, 3)) for r in h_sub if q_id in r.get("answers", {})]
                ai_vals = [float(r["answers"].get(q_id, 3)) for r in ai_sub if q_id in r.get("answers", {})]
                if h_vals and ai_vals:
                    by_age[ag] = round(float(abs(np.mean(ai_vals) - np.mean(h_vals))), 2)
                else:
                    by_age[ag] = None
            else:
                # 選択肢ごとの出現比率差分平均を厳密計算
                options = target_q.get("options", [])
                if options:
                    diffs = []
                    for opt in options:
                        h_prop = sum(1 for r in h_sub if r["answers"].get(q_id) == opt) / len(h_sub)
                        ai_prop = sum(1 for r in ai_sub if r["answers"].get(q_id) == opt) / len(ai_sub)
                        diffs.append(abs(ai_prop - h_prop))
                    by_age[ag] = round(float(np.mean(diffs)), 3)
                else:
                    by_age[ag] = None
        else:
            by_age[ag] = None # サンプルデータが存在しない場合はN/A

    return {
        "target_question": target_q["text"],
        "mae_by_age_group": by_age
    }

def compute_individual_match(ai_list: list[dict], human_list: list[dict], questions: list[dict]) -> dict[str, Any]:
    """個人単位（1対1）の回答一致率判定"""
    matches = 0
    total_comparisons = 0

    human_map = {r["participant_id"]: r["answers"] for r in human_list if "participant_id" in r}

    for ai in ai_list:
        p_code = ai.get("persona", {}).get("persona_code")
        if p_code in human_map:
            h_ans = human_map[p_code]
            ai_ans = ai.get("answers", {})
            for q in questions:
                q_id = q["id"]
                if q_id in h_ans and q_id in ai_ans:
                    total_comparisons += 1
                    if str(h_ans[q_id]) == str(ai_ans[q_id]):
                        matches += 1

    if total_comparisons > 0:
        match_rate = round(matches / total_comparisons, 3)
        return {
            "has_individual_mapping": True,
            "total_comparisons": total_comparisons,
            "exact_match_rate": match_rate,
            "description": f"同一被験者（1対1対応）に対する回答一致率: {match_rate * 100:.1f}%"
        }
    else:
        return {
            "has_individual_mapping": False,
            "exact_match_rate": None,
            "description": "実測個票IDとAIペルソナIDの直接紐付けが存在しないため、集計割合レベル（Marginal Distribution）での統計的一致度（MAE/RMSE/Pearson r）を評価しています。"
        }
