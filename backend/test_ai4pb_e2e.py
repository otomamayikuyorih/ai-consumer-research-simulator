import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ai4pb_pipeline():
    print("=== [1] Testing System Status & AI4PB Metadata ===")
    res = client.get("/api/status")
    assert res.status_code == 200
    data = res.json()
    assert "features" in data
    assert "mode_c_interview_grounded" in data["features"]["modes"]
    print("Status response:", data)

    print("\n=== [2] Testing Interview Datasets (Mode C Grounding) ===")
    res = client.get("/api/interview-datasets/demo")
    assert res.status_code == 200
    demos = res.json()
    assert len(demos) >= 3
    print(f"Retrieved {len(demos)} demo interview transcripts.")
    sample_subj = demos[0]
    print(f"Sample Subject ID: {sample_subj['participant_id']}, Verbatim quotes: {sample_subj['extracted_data']['verbatim_quotes'][0][:40]}...")

    res = client.get("/api/interview-datasets")
    assert res.status_code == 200
    datasets = res.json()
    assert len(datasets) >= 1
    dataset_id = datasets[0]["id"]
    print(f"Default dataset active: {datasets[0]['name']}")

    print("\n=== [3] Creating 3 Cohorts for Comparison: Mode A, Mode B, Mode C ===")
    # Mode A: Demographic Persona
    res_a = client.post("/api/cohorts", json={
        "name": "コホート Mode A (Demographic Only)",
        "target_count": 20,
        "seed": 101,
        "generation_mode": "mode_a",
        "preset": "general_national"
    })
    assert res_a.status_code == 200
    cohort_a = res_a.json()
    assert cohort_a["generation_mode"] == "mode_a"
    print(f"Created Cohort Mode A (ID: {cohort_a['id']})")

    # Mode B: Synthetic Rich Persona
    res_b = client.post("/api/cohorts", json={
        "name": "コホート Mode B (Synthetic Rich Narrative)",
        "target_count": 20,
        "seed": 102,
        "generation_mode": "mode_b",
        "preset": "general_national"
    })
    assert res_b.status_code == 200
    cohort_b = res_b.json()
    assert cohort_b["generation_mode"] == "mode_b"
    print(f"Created Cohort Mode B (ID: {cohort_b['id']})")

    # Mode C: Interview-Grounded Persona
    res_c = client.post("/api/cohorts", json={
        "name": "コホート Mode C (Interview-Grounded)",
        "target_count": 20,
        "seed": 103,
        "generation_mode": "mode_c",
        "preset": "general_national",
        "interview_dataset_id": dataset_id
    })
    assert res_c.status_code == 200
    cohort_c = res_c.json()
    assert cohort_c["generation_mode"] == "mode_c"
    print(f"Created Cohort Mode C (ID: {cohort_c['id']})")

    # Verify Persona Details across modes
    p_a_list = client.get(f"/api/cohorts/{cohort_a['id']}/personas").json()["personas"]
    p_b_list = client.get(f"/api/cohorts/{cohort_b['id']}/personas").json()["personas"]
    p_c_list = client.get(f"/api/cohorts/{cohort_c['id']}/personas").json()["personas"]

    assert p_a_list[0]["generation_mode"] == "mode_a"
    assert p_b_list[0]["generation_mode"] == "mode_b"
    assert p_c_list[0]["generation_mode"] == "mode_c"
    assert len(p_b_list[0]["life_history"]) > 10
    assert "verbatim_quotes" in p_c_list[0]["grounded_interview"]
    print("Mode C Verbatim Quote attached:", p_c_list[0]["grounded_interview"]["verbatim_quotes"][0][:50])

    print("\n=== [4] Testing Virtual A/B Experiment (Nature 2026 Reference) ===")
    ab_req = {
        "cohort_id": cohort_b["id"],
        "title": "エコ・サステナブル訴求 vs 通常訴求の購入意向・価格受容性RCT",
        "research_question": "環境配慮と森林保全寄付を訴求したプレミアム版は、通常版（1,200円）に対し+280円の価格増でも受容されるか？",
        "control_condition": {
            "label": "通常版パッケージ（価格: 1,200円）",
            "description": "高機能プレミアムシャンプー。髪にうるおいと輝きを。",
            "price": 1200,
            "ad_copy": "サロン品質の仕上がりをご自宅で。"
        },
        "treatment_condition": {
            "label": "エコ・サステナブル版（価格: 1,480円）",
            "description": "100%再生プラスチック容器＆植林寄付つき高機能プレミアムシャンプー。",
            "price": 1480,
            "ad_copy": "美しい髪と、美しい地球のために。"
        },
        "order_design": "counterbalanced",
        "use_mock": True
    }
    res_ab = client.post("/api/ab-experiments", json=ab_req)
    assert res_ab.status_code == 200
    ab_data = res_ab.json()
    exp_id = ab_data["id"]
    metrics = ab_data["results"]["metric_analysis"]
    print("Purchase Intent Cohen's d:", metrics["purchase_intent"]["cohens_d"])
    print("Purchase Intent Delta Mean:", metrics["purchase_intent"]["delta_mean"])
    print("Subgroups by Gender:", ab_data["results"]["subgroups"]["by_gender"])

    # Test A/B CSV export
    res_csv = client.get(f"/api/ab-experiments/{exp_id}/export-csv")
    assert res_csv.status_code == 200
    assert "Control_購入意向" in res_csv.text
    print(f"Exported A/B CSV length: {len(res_csv.text)} bytes")

    print("\n=== [5] Testing Survey Simulation and Human-AI Validation Dashboard ===")
    survey_req = {
        "cohort_id": cohort_b["id"],
        "title": "AI4PB 妥当性検証テスト調査",
        "description": "実測人間調査データとの予測誤差（MAE/RMSE）測定用",
        "questions": [
            {
                "id": "q1",
                "text": "本製品を購入したいと思いますか？",
                "type": "single",
                "options": ["ぜひ購入したい", "機会があれば購入したい", "あまり購入したくない", "全く購入したくない"]
            },
            {
                "id": "q2",
                "text": "価格に対する満足度を5段階で評価してください",
                "type": "scale5",
                "options": []
            }
        ]
    }
    res_survey = client.post("/api/surveys", json=survey_req)
    assert res_survey.status_code == 200
    survey_id = res_survey.json()["id"]

    # Run simulation
    client.post("/api/surveys/simulate", json={"survey_id": survey_id, "use_mock": True})

    # Run validation with Demo dataset
    val_req = {
        "survey_id": survey_id,
        "dataset_name": "【デモ実測データ（架空の人手調査 N=100）】",
        "is_demo": True,
        "split_ratio": "50_50_split"
    }
    res_val = client.post("/api/validations", json=val_req)
    assert res_val.status_code == 200
    val_data = res_val.json()
    val_results = val_data["results"]
    assert val_results["is_demo_dataset"] is True
    print("Overall MAE:", val_results["overall_metrics"]["overall_mae"])
    print("Overall RMSE:", val_results["overall_metrics"]["overall_rmse"])
    print("Pearson r:", val_results["overall_metrics"]["pearson_r"])
    print("Out-of-sample Test MAE:", val_results["out_of_sample_validation"]["test_evaluation_split"]["overall_mae"])
    print("Subgroup errors:", val_results["subgroup_errors"])

    print("\n=== [6] Testing Privacy Consent Deletion Endpoint ===")
    # Create temp dataset and delete it
    temp_ingest = client.post("/api/interview-datasets/ingest", json={
        "name": "一時的インタビューデータ",
        "source_type": "text",
        "raw_content": "テストインタビューテキスト",
        "consent_confirmed": True,
        "is_demo": False
    }).json()
    del_res = client.delete(f"/api/interview-datasets/{temp_ingest['id']}")
    assert del_res.status_code == 200
    print("Successfully deleted sensitive dataset on consent withdrawal!")

    print("\nALL AI4PB EXTENSION E2E TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_ai4pb_pipeline()
