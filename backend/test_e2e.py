import sys
import os
import requests
import json
from fastapi.testclient import TestClient

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app.main import app

client = TestClient(app)

def test_full_pipeline():
    print("=== [1] Checking API Status ===")
    res = client.get("/api/status")
    assert res.status_code == 200, res.text
    print("Status:", res.json())

    print("\n=== [2] Checking Public Statistics Benchmarks ===")
    res = client.get("/api/benchmarks")
    assert res.status_code == 200, res.text
    benchmarks = res.json()
    print("Age groups in benchmark:", list(benchmarks["age_groups_national"].keys()))
    print("Regions in benchmark:", list(benchmarks["regions"].keys()))

    print("\n=== [3] Creating 100 Personas Cohort ===")
    res = client.post("/api/cohorts", json={
        "name": "全国代表サンプル (N=100)",
        "target_count": 100,
        "seed": 42,
        "preset": "general_national"
    })
    assert res.status_code == 200, res.text
    cohort = res.json()
    cohort_id = cohort["id"]
    print(f"Cohort created! ID: {cohort_id}, Count: {cohort['persona_count']}")
    assert cohort["persona_count"] == 100

    print("\n=== [4] Fetching Cohort Personas and Filtering ===")
    res = client.get(f"/api/cohorts/{cohort_id}/personas?limit=5")
    assert res.status_code == 200
    personas_data = res.json()
    print(f"Total personas: {personas_data['total']}, Retrieved: {len(personas_data['items'])}")
    first_persona = personas_data['items'][0]
    print("Sample persona:", {
        "name": first_persona["name"],
        "age": first_persona["age"],
        "gender": first_persona["gender"],
        "region": first_persona["region"],
        "occupation": first_persona["occupation"],
        "income": first_persona["personal_income"],
        "values": first_persona["values_segment"],
    })

    print("\n=== [5] Creating Marketing Survey ===")
    survey_payload = {
        "cohort_id": cohort_id,
        "title": "新スマートウォッチ受容性調査",
        "description": "健康管理とAIコーチング機能を搭載した新スマートウォッチの受容性評価",
        "questions": [
            {
                "id": "q1",
                "text": "このスマートウォッチを購入したいと思いますか？",
                "type": "single",
                "options": ["ぜひ購入したい", "機会があれば購入したい", "あまり購入したくない", "絶対に購入したくない"],
                "required": True
            },
            {
                "id": "q2",
                "text": "魅力を感じる機能をすべて選んでください。",
                "type": "multiple",
                "options": ["AIによる睡眠・健康コーチング", "高精度な心拍・血圧測定", "長時間バッテリー（10日間）", "洗練された北欧風デザイン", "スマホ不要の通話機能"],
                "required": True
            },
            {
                "id": "q3",
                "text": "本製品のデザインとコンセプトに対する満足度を教えてください。",
                "type": "scale5",
                "options": ["1: 全く満足できない", "2: あまり満足できない", "3: どちらともいえない", "4: やや満足", "5: 大いに満足"],
                "required": True
            },
            {
                "id": "q4",
                "text": "購入にあたって最も気になる懸念点や、製品への要望があれば教えてください。",
                "type": "text",
                "options": [],
                "required": False
            }
        ]
    }
    res = client.post("/api/surveys", json=survey_payload)
    assert res.status_code == 200, res.text
    survey = res.json()
    survey_id = survey["id"]
    print(f"Survey created! ID: {survey_id}, Title: {survey['title']}")

    print("\n=== [6] Running Simulation for 100 Personas ===")
    res = client.post(f"/api/surveys/{survey_id}/run", json={
        "survey_id": survey_id,
        "use_mock": True,
        "batch_size": 20
    })
    assert res.status_code == 200, res.text
    run_res = res.json()
    print(f"Simulation completed! Responses collected: {run_res['total_responses']}")
    assert run_res["total_responses"] == 100

    print("\n=== [7] Fetching Analytics & Multivariate Results ===")
    res = client.get(f"/api/surveys/{survey_id}/analysis")
    assert res.status_code == 200, res.text
    analysis = res.json()
    print("Total respondents in analysis:", analysis["total_respondents"])
    print("Q1 Summary counts:", analysis["questions_summary"]["q1"]["counts"])
    print("Q3 Scale Mean:", analysis["questions_summary"]["q3"]["mean"], "Top-2 Box:", analysis["questions_summary"]["q3"]["top2_box_ratio"])
    
    # Check Cross-tabulation
    crosstab_q1 = analysis["crosstabs"]["q1"]
    print("Q1 Crosstab by Age Groups:", list(crosstab_q1["age_group"]["percentage"].keys()))
    print("Q1 Crosstab Chi-Square Test:", crosstab_q1["age_group"]["stats"])

    # Check PCA & Clustering
    multivariate = analysis["multivariate"]
    print("PCA Points Count:", len(multivariate["pca"]["points"]))
    print("PCA Explained Variance:", multivariate["pca"]["explained_variance_ratio"])
    print("Clusters Distribution:", multivariate["clustering"]["cluster_distribution"])

    # Check Qualitative AI Text Summary
    q4_text_summary = analysis["text_summaries"]["q4"]
    print("Q4 AI Summary Paragraph:", q4_text_summary["summary"][:60], "...")
    print("Q4 Sentiment Ratio:", q4_text_summary["sentiment_ratio"])

    print("\n=== [8] Exporting CSV ===")
    res = client.get(f"/api/surveys/{survey_id}/export.csv")
    assert res.status_code == 200
    csv_bytes = res.content
    assert csv_bytes.startswith(b'\xef\xbb\xbf')  # UTF-8 BOM
    csv_text = csv_bytes.decode('utf-8-sig')
    csv_lines = csv_text.strip().splitlines()
    print(f"CSV Header: {csv_lines[0][:80]}...")
    print(f"Total CSV records: {len(csv_lines)} (1 header + 100 respondents)")
    assert len(csv_lines) == 101

    print("\n=== [9] Testing 1-on-1 AI Interview Chat ===")
    test_persona_id = first_persona["id"]
    interview_res = client.post(f"/api/interview/{test_persona_id}/chat", json={
        "content": "スマートウォッチを購入したいと思った一番の決め手は何でしたか？"
    })
    assert interview_res.status_code == 200, interview_res.text
    chat_data = interview_res.json()
    print(f"Persona ({first_persona['name']}) Reply: {chat_data['reply']}")
    print(f"Chat History length: {len(chat_data['history'])}")

    print("\n=== [10] Testing Product Concept Evaluation (A/B Test) ===")
    concept_payload = {
        "cohort_id": cohort_id,
        "title": "スマートウォッチ vs スマートリング A/Bテスト",
        "sample_size": 30,
        "concepts": [
            {
                "name": "スマートウォッチ Pro",
                "description": "大画面有機EL・通話・心拍モニタリング搭載",
                "price": 34800,
                "target_category": "ウェアラブルデバイス"
            },
            {
                "name": "スマートリング Light",
                "description": "指に装着するだけで睡眠・体温・歩数を自動記録する超軽量チタンリング",
                "price": 24800,
                "target_category": "スマートジュエリー"
            }
        ]
    }
    res = client.post("/api/concept-evaluations", json=concept_payload)
    assert res.status_code == 200, res.text
    concept_res = res.json()["results"]
    print("Best Purchase Intent Concept:", concept_res["best_purchase_intent"])
    print("Best Interest Concept:", concept_res["best_interest"])
    print("Strategic Recommendation:", concept_res["strategic_recommendation"][:80], "...")

    print("\n=== [11] Testing Frontend Static Mount ===")
    res = client.get("/")
    assert res.status_code == 200
    assert "<!doctype html>" in res.text
    print("Static HTML page served successfully! Length:", len(res.text))

    print("\nALL 11 END-TO-END PIPELINE TESTS PASSED!")

if __name__ == "__main__":
    test_full_pipeline()
