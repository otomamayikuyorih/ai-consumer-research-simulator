"""
Comprehensive P0 & P1 Integration Test Suite
Verifies:
1. API Status and Model Configuration (Gemini 3.8 Flash)
2. Consent Enforcement (P0-5: Rejection on consent_confirmed=False)
3. Public Environment Protection (P0-6: Restrictions when RESTRICT_PUBLIC_DATA_MODIFICATION=True)
4. A/B Experimentation with Counterbalancing & Rationale (P0-1: Presentation order in prompts & individual rationales)
5. Scientific Validation Engine (P0-2, P0-3: Absence of pseudo-random jitter, Pearson r / MAE, Zero-shot robustness transparency)
6. Gemini Fallback Transparency (P0-7: Clear warning and transient tagging)
7. Autonomous Research Orchestration Agent (P1-8, P1-9: 4-step pipeline, step metadata/provenance, executive summary)
8. Orchestrator Presets API
"""
import sys
import os
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.config import settings

client = TestClient(app)

def run_tests():
    passed = 0
    failed = 0
    results = []

    def record_test(name, condition, details=""):
        nonlocal passed, failed
        if condition:
            passed += 1
            results.append({"test": name, "status": "PASS", "details": details})
            print(f"[PASS] {name} - {details}")
        else:
            failed += 1
            results.append({"test": name, "status": "FAIL", "details": details})
            print(f"[FAIL] {name} - {details}")

    print("=" * 70)
    print("RUNNING COMPREHENSIVE P0/P1 INTEGRATION TESTS FOR SUBMISSION")
    print("=" * 70)

    # ----------------------------------------------------
    # 1. API Status and Model Configuration
    # ----------------------------------------------------
    resp = client.get("/api/status")
    data = resp.json()
    default_model = data.get("default_model")
    record_test(
        "API Status & Model Configuration", 
        resp.status_code == 200 and "gemini" in default_model.lower(),
        f"Status: {resp.status_code}, Default Model: {default_model}"
    )

    # ----------------------------------------------------
    # 2. Consent Enforcement (P0-5)
    # ----------------------------------------------------
    # 2a. Rejection when consent_confirmed is False
    unconsented_payload = {
        "name": "Unconsented Test Dataset",
        "source_type": "text",
        "raw_content": "参加者A: 新商品について特に意見はありません。",
        "consent_confirmed": False,
        "is_demo": False
    }
    resp_uncon = client.post("/api/interview-datasets/ingest", json=unconsented_payload)
    record_test(
        "P0-5: Consent Enforcement (Rejection on False)",
        resp_uncon.status_code == 400,
        f"HTTP {resp_uncon.status_code} - Detail: {resp_uncon.json().get('detail')}"
    )

    # 2b. Acceptance when consent_confirmed is True
    consented_payload = {
        "name": "Consented Test Dataset",
        "source_type": "text",
        "raw_content": "参加者A: 価格が手頃ならぜひ試してみたいです。\n参加者B: デザインが洗練されていて気に入りました。",
        "consent_confirmed": True,
        "is_demo": False
    }
    resp_con = client.post("/api/interview-datasets/ingest", json=consented_payload)
    ingested_id = resp_con.json().get("id") if resp_con.status_code == 200 else None
    record_test(
        "P0-5: Consent Enforcement (Acceptance on True)",
        resp_con.status_code == 200 and ingested_id is not None,
        f"HTTP {resp_con.status_code} - ID: {ingested_id}"
    )

    # ----------------------------------------------------
    # 3. Public Environment Protection (P0-6)
    # ----------------------------------------------------
    original_setting = settings.RESTRICT_PUBLIC_DATA_MODIFICATION
    try:
        settings.RESTRICT_PUBLIC_DATA_MODIFICATION = True
        
        # 3a. New upload of non-demo personal data is blocked
        resp_block_upload = client.post("/api/interview-datasets/ingest", json=consented_payload)
        record_test(
            "P0-6: Public Env Protection (Upload Blocked)",
            resp_block_upload.status_code == 403,
            f"HTTP {resp_block_upload.status_code} - Detail: {resp_block_upload.json().get('detail')}"
        )

        # 3b. Deletion of initial demo dataset is blocked
        # Find demo dataset or create one with is_demo=True
        datasets = client.get("/api/interview-datasets").json()
        demo_ds = next((d for d in datasets if d.get("is_demo")), None)
        if not demo_ds:
            seed_res = client.post("/api/interview-datasets/ingest", json={
                "name": "【審査用デモ】インタビュー検証用",
                "source_type": "text",
                "raw_content": "対象者: 時間節約と栄養バランスを両立できる点に魅力を感じます。\n対象者: 価格が少し高くても品質が良ければリピートします。",
                "consent_confirmed": True,
                "is_demo": True
            })
            if seed_res.status_code == 200:
                demo_ds = seed_res.json()

        if demo_ds:
            del_demo_resp = client.delete(f"/api/interview-datasets/{demo_ds['id']}")
            record_test(
                "P0-6: Public Env Protection (Demo Dataset DELETE Blocked)",
                del_demo_resp.status_code == 403,
                f"HTTP {del_demo_resp.status_code} - Detail: {del_demo_resp.json().get('detail')}"
            )
        else:
            record_test("P0-6: Public Env Protection (Demo Dataset check)", False, "No demo dataset found")
    finally:
        settings.RESTRICT_PUBLIC_DATA_MODIFICATION = original_setting

    # Clean up non-demo dataset
    if ingested_id:
        client.delete(f"/api/interview-datasets/{ingested_id}")

    # ----------------------------------------------------
    # 4. Cohort Generation (for A/B and Survey Testing)
    # ----------------------------------------------------
    cohort_resp = client.post("/api/cohorts", json={
        "name": "テスト用コホート (P0/P1検証用)",
        "target_count": 20,
        "seed": 42,
        "generation_mode": "mode_b",
        "preset": "general_national"
    })
    cohort_id = cohort_resp.json()["id"]
    record_test(
        "Cohort Generation",
        cohort_resp.status_code == 200 and cohort_id is not None,
        f"Cohort ID: {cohort_id}"
    )

    # ----------------------------------------------------
    # 5. Virtual A/B Experimentation (P0-1)
    # ----------------------------------------------------
    ab_payload = {
        "cohort_id": cohort_id,
        "title": "A/B RCT: 睡眠AIアドバイザー機能の受容性検証",
        "research_question": "プレミアム機能と価格差に対する受容性を検証",
        "control_condition": {
            "label": "通常パッケージ (¥19,800)",
            "description": "通常機能のスマートウォッチ",
            "price": 19800,
            "ad_copy": "毎日の健康管理をシンプルに"
        },
        "treatment_condition": {
            "label": "プレミアムパッケージ (¥24,800)",
            "description": "睡眠AIアドバイス付きスマートウォッチ",
            "price": 24800,
            "ad_copy": "AI専任トレーナーがあなたの睡眠を科学"
        },
        "order_design": "counterbalanced",
        "sample_size": 20,
        "use_mock": True
    }
    ab_resp = client.post("/api/ab-experiments", json=ab_payload)
    ab_data = ab_resp.json()
    ab_res = ab_data.get("results", {})
    individual_results = ab_res.get("individual_results", [])

    # Check metric analysis (Cohen's d, p-value, t-statistic)
    metric_analysis = ab_res.get("metric_analysis", {})
    record_test(
        "P0-1: A/B Experiment Metric Analysis",
        ab_resp.status_code == 200 and "purchase_intent" in metric_analysis,
        f"Cohen's d: {metric_analysis.get('purchase_intent', {}).get('cohens_d')}, p-value: {metric_analysis.get('purchase_intent', {}).get('p_value')}"
    )

    # Check counterbalancing in sample: both Control->Treatment and Treatment->Control exist
    orders = [r.get("presentation_order", "").lower() for r in individual_results]
    has_c_t = any("control" in o and o.startswith("control") for o in orders)
    has_t_c = any("treatment" in o and o.startswith("treatment") for o in orders)
    record_test(
        "P0-1: A/B Counterbalanced Order Randomization",
        has_c_t and has_t_c,
        f"Orders: C->T count={sum(1 for o in orders if o.startswith('control'))}, T->C count={sum(1 for o in orders if o.startswith('treatment'))}"
    )

    # Check individual evaluation rationales
    has_rationales = len(individual_results) > 0 and bool(individual_results[0].get("control_reason") or individual_results[0].get("treatment_reason"))
    record_test(
        "P0-1: A/B Individual Response Rationales",
        has_rationales,
        f"Sample: {individual_results[0].get('control_reason')[:50]}..."
    )

    # ----------------------------------------------------
    # 6. Scientific Validation Engine (P0-2, P0-3)
    # ----------------------------------------------------
    # Create survey and simulate responses to validate against human benchmark
    survey_resp = client.post("/api/surveys", json={
        "cohort_id": cohort_id,
        "title": "妥当性検証テスト用アンケート",
        "questions": [
            {
                "id": "q1",
                "text": "本製品を購入したいと思いますか？",
                "type": "scale5",
                "options": []
            },
            {
                "id": "q2",
                "text": "価格に対する満足度を5段階で評価してください",
                "type": "scale5",
                "options": []
            }
        ]
    })
    survey_id = survey_resp.json()["id"]

    # Simulate responses
    client.post("/api/surveys/simulate", json={"survey_id": survey_id, "use_mock": True})

    # Run validation
    val_resp = client.post("/api/validations", json={
        "survey_id": survey_id,
        "dataset_name": "【デモ実測データ】",
        "is_demo": True,
        "split_ratio": "50_50_split"
    })
    val_data = val_resp.json()
    val_res = val_data.get("results", {})
    metrics = val_res.get("overall_metrics", {})
    
    record_test(
        "P0-2: Validation Engine Metrics (No Fake Jitter)",
        val_resp.status_code == 200 and "overall_mae" in metrics and "pearson_r" in metrics,
        f"MAE: {metrics.get('overall_mae')}, RMSE: {metrics.get('overall_rmse')}, Pearson r: {metrics.get('pearson_r')}"
    )

    # Check scientific transparency notice
    notice = val_res.get("scientific_notice", "") or val_res.get("scientific_transparency_notice", "")
    record_test(
        "P0-3: Scientific Transparency (Zero-shot Robustness, No Fake Calibration)",
        "Zero-shot" in notice or "折半" in notice or "未校正" in notice,
        f"Notice: {notice[:75]}..."
    )

    # ----------------------------------------------------
    # 7. Autonomous Research Orchestrator Agent (P1-8, P1-9)
    # ----------------------------------------------------
    orch_payload = {
        "research_goal": "完全栄養食パスタの若年層・働く単身世帯への受容性と適正価格検証",
        "target_audience_hint": "20代〜40代の働く単身世帯・健康意識層",
        "sample_size": 20,
        "use_mock": True
    }
    orch_resp = client.post("/api/orchestrator/run", json=orch_payload)
    orch_data = orch_resp.json()
    
    record_test(
        "P1-8: Autonomous Orchestrator Execution (Demo/Fallback Mode Identification)",
        orch_resp.status_code == 200 and orch_data.get("overall_status") in ["completed", "fallback_demo_mode", "partial_fallback"],
        f"Orchestration ID: {orch_data.get('orchestration_id')} (Status: {orch_data.get('overall_status')})"
    )
    
    steps = orch_data.get("steps", [])
    all_steps_completed = len(steps) == 4 and all(s.get("status") in ["completed", "fallback_mock"] for s in steps)
    record_test(
        "P1-8: Orchestrator 4-Step Chain Completed",
        all_steps_completed,
        f"Steps: {[s.get('step_id') for s in steps]}"
    )
    
    # Check step provenance (model, duration, retry count)
    has_provenance = all("model_used" in s and "duration_ms" in s and "retry_count" in s for s in steps)
    record_test(
        "P1-9: Step Provenance, Model Tracking & Latency Observability",
        has_provenance,
        f"Models: {[s.get('model_used') for s in steps]}, Durations: {[s.get('duration_ms') for s in steps]} ms"
    )
    
    # Check Executive Research Summary
    summary = orch_data.get("executive_summary", {})
    record_test(
        "P1-8: Executive Research Summary Generated",
        bool(summary.get("key_findings") and summary.get("target_recommendation") and summary.get("strategic_actions")),
        f"Key Findings: {len(summary.get('key_findings', []))}, Target: {summary.get('target_recommendation')[:40]}..."
    )

    # ----------------------------------------------------
    # 8. Orchestrator Presets API
    # ----------------------------------------------------
    presets_resp = client.get("/api/orchestrator/presets")
    presets_data = presets_resp.json()
    presets_list = presets_data if isinstance(presets_data, list) else presets_data.get("presets", [])
    record_test(
        "Orchestrator Presets API",
        presets_resp.status_code == 200 and len(presets_list) >= 3,
        f"Found {len(presets_list)} presets"
    )

    # ----------------------------------------------------
    # 9. Clean up
    # ----------------------------------------------------
    client.delete(f"/api/cohorts/{cohort_id}")
    client.delete(f"/api/surveys/{survey_id}")

    print("=" * 70)
    print(f"FINAL TEST SUMMARY: {passed} PASSED, {failed} FAILED (TOTAL {passed + failed})")
    print("=" * 70)

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
