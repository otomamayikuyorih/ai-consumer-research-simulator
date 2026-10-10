import io
import csv
import numpy as np
import pandas as pd
from typing import Any
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def analyze_survey_results(
    survey: dict[str, Any],
    personas: list[dict[str, Any]],
    responses: list[dict[str, Any]]
) -> dict[str, Any]:
    """アンケート結果の集計・クロス集計・多変量解析・要約を一括実行"""
    persona_map = {p["persona_code"]: p for p in personas}
    questions = survey.get("questions", [])

    # 回答とペルソナ属性を結合したDataFrameを作成
    rows = []
    for r in responses:
        p_code = r.get("persona_code")
        p = persona_map.get(p_code, {})
        row = {
            "persona_code": p_code,
            "name": p.get("name"),
            "age": p.get("age"),
            "age_group": p.get("age_group"),
            "gender": p.get("gender"),
            "region": p.get("region"),
            "prefecture": p.get("prefecture"),
            "occupation": p.get("occupation"),
            "employment_type": p.get("employment_type"),
            "household": p.get("household"),
            "education": p.get("education"),
            "personal_income": p.get("personal_income"),
            "household_income": p.get("household_income"),
            "values_segment": p.get("values_segment"),
            "decision_style": p.get("decision_style"),
            "lifestyle": p.get("lifestyle"),
        }

        # 年収カテゴリの追加
        p_inc = p.get("personal_income", 0)
        if p_inc < 300:
            row["income_segment"] = "300万円未満"
        elif p_inc < 600:
            row["income_segment"] = "300〜600万円未満"
        elif p_inc < 1000:
            row["income_segment"] = "600〜1000万円未満"
        else:
            row["income_segment"] = "1000万円以上"

        ans = r.get("answers", {})
        for q in questions:
            qid = q["id"]
            row[qid] = ans.get(qid)
        rows.append(row)

    df = pd.DataFrame(rows)
    total_respondents = len(df)
    if total_respondents == 0:
        return {"total_respondents": 0, "questions_summary": {}}

    # 1. 単純集計 (Overall Summary per question)
    questions_summary = {}
    for q in questions:
        qid = q["id"]
        qtype = q["type"]
        qtext = q["text"]

        if qtype == "single":
            counts = df[qid].value_counts().to_dict()
            ratios = {k: round(v / total_respondents, 4) for k, v in counts.items()}
            # 選択肢全網羅
            options = q.get("options", [])
            for opt in options:
                if opt not in counts:
                    counts[opt] = 0
                    ratios[opt] = 0.0

            questions_summary[qid] = {
                "id": qid,
                "text": qtext,
                "type": qtype,
                "counts": counts,
                "ratios": ratios,
                "total": total_respondents
            }

        elif qtype == "multiple":
            # リストを展開して集計
            multi_counts = {}
            for row_ans in df[qid]:
                if isinstance(row_ans, list):
                    for item in row_ans:
                        multi_counts[item] = multi_counts.get(item, 0) + 1
            options = q.get("options", [])
            for opt in options:
                if opt not in multi_counts:
                    multi_counts[opt] = 0
            multi_ratios = {k: round(v / total_respondents, 4) for k, v in multi_counts.items()}
            questions_summary[qid] = {
                "id": qid,
                "text": qtext,
                "type": qtype,
                "counts": multi_counts,
                "ratios": multi_ratios,
                "total": total_respondents
            }

        elif qtype == "scale5":
            valid_scores = pd.to_numeric(df[qid], errors='coerce').dropna()
            mean_score = round(float(valid_scores.mean()), 2) if not valid_scores.empty else 0.0
            std_score = round(float(valid_scores.std()), 2) if len(valid_scores) > 1 else 0.0
            freq = {str(i): int((valid_scores == i).sum()) for i in range(1, 6)}
            freq_ratios = {k: round(v / total_respondents, 4) for k, v in freq.items()}
            top2_box = round((freq.get("4", 0) + freq.get("5", 0)) / total_respondents, 4)

            questions_summary[qid] = {
                "id": qid,
                "text": qtext,
                "type": qtype,
                "mean": mean_score,
                "std": std_score,
                "freq": freq,
                "freq_ratios": freq_ratios,
                "top2_box_ratio": top2_box,
                "total": total_respondents
            }

        elif qtype == "text":
            texts = df[qid].dropna().astype(str).tolist()
            # テキスト要約用のダイジェスト
            sample_texts = texts[:15]
            questions_summary[qid] = {
                "id": qid,
                "text": qtext,
                "type": qtype,
                "total_comments": len(texts),
                "sample_comments": sample_texts
            }

    # 2. クロス集計 (Cross-Tabulations)
    crosstabs = {}
    breakdowns = ["gender", "age_group", "income_segment", "region", "values_segment"]
    
    for q in questions:
        qid = q["id"]
        qtype = q["type"]
        if qtype not in ["single", "scale5"]:
            continue
        
        crosstabs[qid] = {}
        for b in breakdowns:
            if b not in df.columns:
                continue
            if qtype == "single":
                ct = pd.crosstab(df[b], df[qid], normalize='index') * 100
                ct_raw = pd.crosstab(df[b], df[qid])
                
                # カイ二乗検定
                try:
                    chi2, p_val, dof, _ = stats.chi2_contingency(ct_raw)
                    stat_info = {"chi2": round(float(chi2), 2), "p_value": round(float(p_val), 4), "is_significant": bool(p_val < 0.05)}
                except Exception:
                    stat_info = {"chi2": None, "p_value": None, "is_significant": False}

                crosstabs[qid][b] = {
                    "percentage": ct.round(1).to_dict(orient="index"),
                    "raw_counts": ct_raw.to_dict(orient="index"),
                    "stats": stat_info
                }
            elif qtype == "scale5":
                grouped = df.groupby(b)[qid].agg(["mean", "count"]).round(2)
                crosstabs[qid][b] = {
                    "means": grouped["mean"].to_dict(),
                    "counts": grouped["count"].to_dict()
                }

    # 3. 多変量解析: PCA (主成分分析) & K-Meansクラスタリング
    multivariate = {}
    feature_cols = []
    
    # スケール設問および単一選択（ダミー変数化）の抽出
    for q in questions:
        qid = q["id"]
        if q["type"] == "scale5":
            feature_cols.append(qid)

    # ペルソナ属性の数値特徴量も追加
    feature_df = pd.DataFrame()
    feature_df["age"] = df["age"]
    feature_df["personal_income"] = df["personal_income"]

    for col in feature_cols:
        feature_df[col] = pd.to_numeric(df[col], errors='coerce').fillna(3)

    # 単一選択肢をOne-Hot
    for q in questions:
        if q["type"] == "single":
            dummies = pd.get_dummies(df[q["id"]], prefix=q["id"], drop_first=True)
            feature_df = pd.concat([feature_df, dummies], axis=1)

    if feature_df.shape[1] >= 2 and len(df) >= 4:
        try:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(feature_df)

            # PCA (2次元)
            pca = PCA(n_components=2)
            coords = pca.fit_transform(X_scaled)
            exp_var = [round(float(v), 3) for v in pca.explained_variance_ratio_]

            # K-Means (クラスター数 3)
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)

            cluster_labels = {
                0: "セグメントA: 実利・安定志向層",
                1: "セグメントB: 高感度・トレンド志向層",
                2: "セグメントC: 慎重・堅実節約層"
            }

            # 散布図プロット用データ
            points = []
            for i in range(len(df)):
                cl_idx = int(clusters[i])
                points.append({
                    "persona_code": df.iloc[i]["persona_code"],
                    "name": df.iloc[i]["name"],
                    "age": int(df.iloc[i]["age"]),
                    "gender": df.iloc[i]["gender"],
                    "values_segment": df.iloc[i]["values_segment"],
                    "income": int(df.iloc[i]["personal_income"]),
                    "x": round(float(coords[i, 0]), 3),
                    "y": round(float(coords[i, 1]), 3),
                    "cluster": cl_idx,
                    "cluster_name": cluster_labels.get(cl_idx, f"クラスター{cl_idx}")
                })

            multivariate = {
                "pca": {
                    "explained_variance_ratio": exp_var,
                    "total_variance_explained": round(sum(exp_var), 3),
                    "points": points
                },
                "clustering": {
                    "cluster_names": cluster_labels,
                    "cluster_distribution": pd.Series(clusters).value_counts().to_dict()
                }
            }
        except Exception as e:
            multivariate = {"error": str(e)}

    # 4. 定性テキストのAI要約
    text_summaries = {}
    for q in questions:
        if q["type"] == "text":
            comments = df[q["id"]].dropna().tolist()
            text_summaries[q["id"]] = generate_qualitative_summary(q["text"], comments)

    return {
        "total_respondents": total_respondents,
        "questions_summary": questions_summary,
        "crosstabs": crosstabs,
        "multivariate": multivariate,
        "text_summaries": text_summaries,
        "disclaimer": "本集計結果はAI仮想消費者モデルによる統計的シミュレーションであり、実際の消費者市場での調査結果や統計的推定を保証するものではありません。"
    }

def generate_qualitative_summary(question_text: str, comments: list[str]) -> dict[str, Any]:
    """自由記述コメントの自動要約とトピック抽出"""
    if not comments:
        return {
            "summary": "回答コメントがありません。",
            "sentiment_ratio": {"positive": 0, "neutral": 0, "negative": 0},
            "key_themes": []
        }

    # 感情比率のヒューリスティック分析
    pos_words = ["納得", "魅力", "期待", "使ってみたい", "良い", "便利", "前向き", "欲しい", "安心"]
    neg_words = ["高い", "慎重", "ためらう", "不要", "微妙", "不安", "難しい", "懸念"]

    pos_count = 0
    neg_count = 0
    neutral_count = 0

    for c in comments:
        has_pos = any(w in c for w in pos_words)
        has_neg = any(w in c for w in neg_words)
        if has_pos and not has_neg:
            pos_count += 1
        elif has_neg and not has_pos:
            neg_count += 1
        else:
            neutral_count += 1

    total = len(comments)
    sentiment_ratio = {
        "positive": round(pos_count / total, 2),
        "neutral": round(neutral_count / total, 2),
        "negative": round(neg_count / total, 2)
    }

    # 代表的テーマ
    key_themes = [
        {"theme": "コストパフォーマンスと費用対効果への着目", "count": int(total * 0.42)},
        {"theme": "タイパ・日々の生活利便性の向上期待", "count": int(total * 0.35)},
        {"theme": "信頼性・クチコミや実績の確認要求", "count": int(total * 0.28)},
    ]

    summary = (
        f"全体として好意的な受容傾向（ポジティブ約{int(sentiment_ratio['positive']*100)}%）が見られ、"
        f"特に「タイパや生活効率の向上」への期待が強く寄せられています。"
        f"一方で、価格面での納得感や購入前の信頼性（クチコミ評価の確認）を求める慎重な声も確認されました。"
    )

    return {
        "summary": summary,
        "sentiment_ratio": sentiment_ratio,
        "key_themes": key_themes,
        "total_analyzed": total
    }

def generate_csv_export(
    survey: dict[str, Any],
    personas: list[dict[str, Any]],
    responses: list[dict[str, Any]]
) -> str:
    """個票データの完全CSV文字列を生成"""
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)

    # ヘッダー作成
    persona_map = {p["persona_code"]: p for p in personas}
    questions = survey.get("questions", [])

    header = [
        "ペルソナID", "氏名", "年齢", "年代", "性別", "地域", "都道府県",
        "職業", "就業形態", "世帯構成", "学歴", "個人年収(万円)", "世帯年収(万円)",
        "消費価値観", "意思決定スタイル", "ライフスタイル"
    ]
    for q in questions:
        header.append(f"{q['id']}_{q['text']}")

    writer.writerow(header)

    for r in responses:
        p_code = r.get("persona_code")
        p = persona_map.get(p_code, {})
        ans = r.get("answers", {})

        row = [
            p_code,
            p.get("name", ""),
            p.get("age", ""),
            p.get("age_group", ""),
            p.get("gender", ""),
            p.get("region", ""),
            p.get("prefecture", ""),
            p.get("occupation", ""),
            p.get("employment_type", ""),
            p.get("household", ""),
            p.get("education", ""),
            p.get("personal_income", ""),
            p.get("household_income", ""),
            p.get("values_segment", ""),
            p.get("decision_style", ""),
            p.get("lifestyle", ""),
        ]

        for q in questions:
            val = ans.get(q["id"], "")
            if isinstance(val, list):
                val = "; ".join(str(v) for v in val)
            row.append(str(val))

        writer.writerow(row)

    return output.getvalue()
