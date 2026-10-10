import os
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Any

from .config import settings, has_gemini_api_key
from .database import engine, Base, get_db
from .models import (
    PersonaCohort, Persona, Survey, SurveyResponse, InterviewSession, ConceptEvaluation,
    InterviewDataset, VirtualABExperiment, HumanAIValidation, migrate_database
)
from .schemas import (
    CohortCreateRequest, CohortOut, PersonaOut,
    SurveyCreateRequest, SurveyOut, SurveyExecutionRequest,
    InterviewMessageRequest, ConceptEvaluationRequest,
    InterviewIngestRequest, VirtualABExperimentRequest, HumanAIValidationRequest,
    AutonomousResearchRequest
)
from .orchestrator import run_autonomous_orchestration
from .persona_generator import (
    generate_cohort_personas,
    get_cohort_distribution_summary,
    STATISTICAL_BENCHMARKS
)
from .survey_runner import execute_survey_simulation
from .analysis_engine import analyze_survey_results, generate_csv_export
from .interview_engine import chat_with_persona
from .concept_evaluator import run_concept_comparison
from .interview_grounding import (
    DEMO_INTERVIEW_SAMPLES,
    extract_interview_grounding,
    parse_interview_csv
)
from .ab_experiment import run_virtual_ab_experiment, export_ab_experiment_csv
from .validation_engine import (
    generate_demo_human_survey_data,
    parse_human_csv_data,
    evaluate_human_ai_validation
)

# データベースマイグレーション
migrate_database()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Consumer Research Simulator API - 日本の公的統計・AI4PB研究準拠の仮想消費者調査プラットフォーム",
    version="2.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- API ルート ----------------

@app.get("/api/status")
def get_system_status():
    return {
        "status": "online",
        "has_gemini_key": has_gemini_api_key(),
        "default_model": settings.DEFAULT_GEMINI_MODEL,
        "mode": "Live Gemini API" if has_gemini_api_key() else "Offline Statistical Heuristic Simulation",
        "google_cloud": {
            "is_cloud_run": settings.IS_CLOUD_RUN,
            "project_id": settings.GOOGLE_CLOUD_PROJECT,
            "service": settings.CLOUD_RUN_SERVICE,
            "revision": settings.CLOUD_RUN_REVISION,
            "ai_product": "Google Gemini 3.8 Flash / Vertex AI Model Garden",
            "execution_product": "Cloud Run (Fully Managed Serverless Container)"
        },
        "features": {
            "modes": ["mode_a_demographic", "mode_b_synthetic_rich", "mode_c_interview_grounded"],
            "ab_experiment": True,
            "human_ai_validation": True,
            "stanford_ai4pb_reference": True
        }
    }

@app.get("/api/benchmarks")
def get_benchmarks():
    return STATISTICAL_BENCHMARKS

# --- インタビューデータ管理 (AI4PB Mode C Grounding) ---

@app.get("/api/interview-datasets/demo")
def get_demo_interviews():
    """AI4PB検証用のデモ用定性インタビューサンプルを取得"""
    return DEMO_INTERVIEW_SAMPLES

@app.post("/api/interview-datasets/ingest")
async def ingest_interview_dataset(req: InterviewIngestRequest, db: Session = Depends(get_db)):
    """インタビューテキストまたはCSVを取り込み、Geminiで生活実感・発言（Verbatim Quotes）を抽出"""
    # P0安全性チェック1: 同意なしの取り込み拒否
    if not req.consent_confirmed and not req.is_demo:
        raise HTTPException(
            status_code=400,
            detail="【同意未確認】調査参加者本人の事前同意（データ提供・AIシミュレーション利用への同意）が確認されていないため、取り込みを拒否しました。"
        )

    # P0安全性チェック2: 審査用公開環境における実在個人データのアップロード制限
    if settings.RESTRICT_PUBLIC_DATA_MODIFICATION and not req.is_demo:
        raise HTTPException(
            status_code=403,
            detail="【審査用公開環境保護】個人情報保護およびセキュリティのため、公開審査環境における実在個人データの新規アップロードは制限されています。デモ用データセットをご利用ください。"
        )

    extracted_profiles = []

    if req.source_type == "csv":
        csv_records = parse_interview_csv(req.raw_content)
        for r in csv_records:
            t = r.get("transcript") or r.get("answer") or str(r)
            ex = await extract_interview_grounding(t, metadata=r)
            extracted_profiles.append({
                "participant_id": r.get("participant_id", "SUBJ-CSV"),
                "raw_transcript": t,
                "extracted_data": ex,
                "is_demo": req.is_demo
            })
    else:
        # 単一またはまとまったインタビューテキスト
        ex = await extract_interview_grounding(req.raw_content)
        extracted_profiles.append({
            "participant_id": "SUBJ-INGEST-001",
            "raw_transcript": req.raw_content,
            "extracted_data": ex,
            "is_demo": req.is_demo
        })

    ds = InterviewDataset(
        name=req.name,
        source_type=req.source_type,
        raw_content=req.raw_content[:5000],
        extracted_data=extracted_profiles,
        consent_confirmed=1 if req.consent_confirmed else 0,
        is_demo=1 if req.is_demo else 0,
        participant_count=len(extracted_profiles)
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds.to_dict()

@app.get("/api/interview-datasets")
def list_interview_datasets(db: Session = Depends(get_db)):
    records = db.query(InterviewDataset).order_by(InterviewDataset.created_at.desc()).all()
    # デモデータが一件も存在しない場合は初期投入
    if not records:
        demo_ds = InterviewDataset(
            name="【デモ】3名の詳細定性インタビュー記録 (共働き子育て・単身エンジニア・シニア)",
            source_type="manual",
            raw_content="Stanford AI4PB準拠の初期サンプル定性インタビュー記録",
            extracted_data=DEMO_INTERVIEW_SAMPLES,
            consent_confirmed=1,
            is_demo=1,
            participant_count=len(DEMO_INTERVIEW_SAMPLES)
        )
        db.add(demo_ds)
        db.commit()
        db.refresh(demo_ds)
        records = [demo_ds]

    return [r.to_dict() for r in records]

@app.delete("/api/interview-datasets/{dataset_id}")
def delete_interview_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """個人情報・機微情報の保護と同意撤回に対応するためのインタビューデータ物理削除エンドポイント"""
    ds = db.query(InterviewDataset).filter(InterviewDataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Interview dataset not found")

    # P0安全性チェック3: 審査用公開環境における初期ベースデモデータセットの削除制限
    if settings.RESTRICT_PUBLIC_DATA_MODIFICATION and ds.is_demo:
        raise HTTPException(
            status_code=403,
            detail="【審査用公開環境保護】公開審査環境における初期ベースデモデータセットの削除は制限されています。"
        )

    db.delete(ds)
    db.commit()
    return {"status": "deleted", "dataset_id": dataset_id}

# --- コホート・ペルソナ ---

@app.post("/api/cohorts", response_model=CohortOut)
def create_cohort(req: CohortCreateRequest, db: Session = Depends(get_db)):
    generation_mode = req.generation_mode or "mode_b"
    interview_samples = None

    if generation_mode == "mode_c":
        # Mode Cの場合は指定または最新のインタビューデータセットを参照
        if req.interview_dataset_id:
            ds = db.query(InterviewDataset).filter(InterviewDataset.id == req.interview_dataset_id).first()
            if ds and ds.extracted_data:
                interview_samples = ds.extracted_data
        if not interview_samples:
            interview_samples = DEMO_INTERVIEW_SAMPLES

    provenance = {
        "model_version": settings.DEFAULT_GEMINI_MODEL,
        "seed": req.seed,
        "generation_mode": generation_mode,
        "academic_attribution": "Stanford AI4PB (Park et al., 2024) / Nature (2026)",
        "synthetic_notice": (
            "Mode A/Bは統計相関アルゴリズムによる合成データです。Mode Cはインタビュー記録に接地された生活者です。"
        )
    }

    config_data = {
        "preset": req.preset,
        "seed": req.seed,
        "generation_mode": generation_mode,
        "interview_dataset_id": req.interview_dataset_id,
        "data_source": STATISTICAL_BENCHMARKS["source"]
    }
    cohort = PersonaCohort(
        name=req.name,
        target_count=req.target_count,
        seed=req.seed,
        generation_mode=generation_mode,
        interview_dataset_id=req.interview_dataset_id,
        config=config_data,
        provenance_info=provenance
    )
    db.add(cohort)
    db.commit()
    db.refresh(cohort)

    # ペルソナ一括生成（Mode A / Mode B / Mode C）
    personas_data = generate_cohort_personas(
        count=req.target_count,
        preset=req.preset,
        seed=req.seed,
        mode=generation_mode,
        interview_samples=interview_samples
    )
    for p in personas_data:
        persona = Persona(
            cohort_id=cohort.id,
            persona_code=p["persona_code"],
            generation_mode=p.get("generation_mode", generation_mode),
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
            hobbies=p["hobbies"],
            values_segment=p["values_segment"],
            lifestyle=p["lifestyle"],
            info_channels=p["info_channels"],
            decision_style=p["decision_style"],
            consumption_profile=p["consumption_profile"],
            life_history=p.get("life_history", ""),
            purchase_experiences=p.get("purchase_experiences", []),
            grounded_interview=p.get("grounded_interview", {}),
            is_consented_human_subject=p.get("is_consented_human_subject", 0),
            data_consent_status=p.get("data_consent_status", "synthetic_public_stats")
        )
        db.add(persona)
    db.commit()

    return CohortOut(
        id=cohort.id,
        name=cohort.name,
        target_count=cohort.target_count,
        seed=cohort.seed,
        generation_mode=cohort.generation_mode,
        interview_dataset_id=cohort.interview_dataset_id,
        config=cohort.config,
        provenance_info=cohort.provenance_info,
        created_at=cohort.created_at.isoformat(),
        persona_count=len(personas_data)
    )

@app.get("/api/cohorts")
def list_cohorts(db: Session = Depends(get_db)):
    cohorts = db.query(PersonaCohort).order_by(PersonaCohort.created_at.desc()).all()
    results = []
    for c in cohorts:
        results.append({
            "id": c.id,
            "name": c.name,
            "target_count": c.target_count,
            "seed": c.seed,
            "generation_mode": c.generation_mode or "mode_b",
            "interview_dataset_id": c.interview_dataset_id,
            "config": c.config,
            "provenance_info": c.provenance_info,
            "created_at": c.created_at.isoformat(),
            "persona_count": len(c.personas)
        })
    return results

@app.get("/api/cohorts/{cohort_id}")
def get_cohort_detail(cohort_id: str, db: Session = Depends(get_db)):
    cohort = db.query(PersonaCohort).filter(PersonaCohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")

    personas_dicts = [p.to_dict() for p in cohort.personas]
    distribution = get_cohort_distribution_summary(personas_dicts)

    return {
        "id": cohort.id,
        "name": cohort.name,
        "target_count": cohort.target_count,
        "seed": cohort.seed,
        "generation_mode": cohort.generation_mode or "mode_b",
        "interview_dataset_id": cohort.interview_dataset_id,
        "config": cohort.config,
        "provenance_info": cohort.provenance_info,
        "created_at": cohort.created_at.isoformat(),
        "persona_count": len(cohort.personas),
        "distribution": distribution
    }

@app.delete("/api/cohorts/{cohort_id}")
def delete_cohort(cohort_id: str, db: Session = Depends(get_db)):
    cohort = db.query(PersonaCohort).filter(PersonaCohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")
    db.delete(cohort)
    db.commit()
    return {"status": "deleted", "id": cohort_id}

@app.get("/api/cohorts/{cohort_id}/personas")
def get_cohort_personas_list(
    cohort_id: str,
    skip: int = 0,
    limit: int = 50,
    gender: str = None,
    age_group: str = None,
    values_segment: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Persona).filter(Persona.cohort_id == cohort_id)
    if gender:
        query = query.filter(Persona.gender == gender)
    if age_group:
        query = query.filter(Persona.age_group == age_group)
    if values_segment:
        query = query.filter(Persona.values_segment == values_segment)

    total = query.count()
    records = query.order_by(Persona.persona_code).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "personas": [p.to_dict() for p in records],
        "items": [p.to_dict() for p in records]
    }

@app.get("/api/personas/{persona_id}")
def get_persona_detail(persona_id: str, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona.to_dict()

# --- アンケート ---

@app.post("/api/surveys", response_model=SurveyOut)
def create_survey(req: SurveyCreateRequest, db: Session = Depends(get_db)):
    cohort = db.query(PersonaCohort).filter(PersonaCohort.id == req.cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404, detail="Target cohort not found")

    questions_json = [q.dict() for q in req.questions]
    survey = Survey(
        cohort_id=req.cohort_id,
        title=req.title,
        description=req.description,
        questions=questions_json
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)

    return SurveyOut(
        id=survey.id,
        cohort_id=survey.cohort_id,
        title=survey.title,
        description=survey.description,
        questions=survey.questions,
        created_at=survey.created_at.isoformat(),
        response_count=0
    )

@app.get("/api/surveys")
def list_surveys(cohort_id: str = None, db: Session = Depends(get_db)):
    query = db.query(Survey)
    if cohort_id:
        query = query.filter(Survey.cohort_id == cohort_id)
    records = query.order_by(Survey.created_at.desc()).all()
    return [{
        "id": s.id,
        "cohort_id": s.cohort_id,
        "title": s.title,
        "description": s.description,
        "questions_count": len(s.questions),
        "response_count": len(s.responses),
        "created_at": s.created_at.isoformat()
    } for s in records]

@app.get("/api/surveys/{survey_id}")
def get_survey_detail(survey_id: str, db: Session = Depends(get_db)):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
    return {
        "id": survey.id,
        "cohort_id": survey.cohort_id,
        "title": survey.title,
        "description": survey.description,
        "questions": survey.questions,
        "model_name": survey.model_name,
        "created_at": survey.created_at.isoformat(),
        "response_count": len(survey.responses)
    }

@app.post("/api/surveys/simulate")
@app.post("/api/surveys/{survey_id}/run")
async def run_survey_simulation(req: SurveyExecutionRequest, db: Session = Depends(get_db)):
    survey = db.query(Survey).filter(Survey.id == req.survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    personas = db.query(Persona).filter(Persona.cohort_id == survey.cohort_id).all()
    if not personas:
        raise HTTPException(status_code=400, detail="No personas in target cohort")

    personas_dicts = [p.to_dict() for p in personas]

    # 回答シミュレーション実行
    results, execution_meta = await execute_survey_simulation(
        personas=personas_dicts,
        questions=survey.questions,
        use_mock=req.use_mock,
        model_name=req.model_name,
        batch_size=req.batch_size
    )

    # P0安全性要件7: Gemini API失敗時はモックへの切替をユーザーに明示し、実AI推論として集計・保存しない
    if execution_meta.get("is_fallback"):
        survey.model_name = "mock_fallback_on_gemini_error"
        db.commit()
        return {
            "survey_id": survey.id,
            "total_simulated": len(results),
            "total_responses": 0,
            "status": "mock_fallback_rejected",
            "is_fallback": True,
            "is_mock": True,
            "engine_type": "mock_fallback",
            "model_used": "mock_fallback_statistical",
            "warning": execution_meta.get("warning"),
            "error_detail": execution_meta.get("error_detail"),
            "sample_responses": results[:3]
        }

    # 既存回答のクリア
    db.query(SurveyResponse).filter(SurveyResponse.survey_id == survey.id).delete()

    # DB保存（明示的モック指定または正常なGemini推論時のみ）
    persona_map = {p.persona_code: p.id for p in personas}
    for r in results:
        p_code = r["persona_code"]
        p_id = persona_map.get(p_code)
        if p_id:
            db_resp = SurveyResponse(
                survey_id=survey.id,
                persona_id=p_id,
                answers=r["answers"],
                reasoning=r.get("reasoning", "")
            )
            db.add(db_resp)

    survey.model_name = execution_meta["model_name"]
    db.commit()

    return {
        "survey_id": survey.id,
        "total_simulated": len(results),
        "total_responses": len(results),
        "status": "completed",
        "engine_type": execution_meta.get("engine_type", "gemini_agent"),
        "is_mock": execution_meta.get("is_mock", False),
        "is_fallback": False,
        "model_used": survey.model_name,
        "warning": execution_meta.get("warning")
    }

# --- 解析 & CSV ---

@app.get("/api/surveys/{survey_id}/analysis")
def get_survey_analysis(survey_id: str, db: Session = Depends(get_db)):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    responses = db.query(SurveyResponse).filter(SurveyResponse.survey_id == survey_id).all()
    if not responses:
        raise HTTPException(status_code=400, detail="No survey responses recorded yet")

    survey_dict = {"id": survey.id, "title": survey.title, "questions": survey.questions}
    personas_dict = [r.persona.to_dict() for r in responses]
    responses_list = [{"persona_code": r.persona.persona_code, "answers": r.answers, "reasoning": r.reasoning} for r in responses]

    analysis = analyze_survey_results(survey_dict, personas_dict, responses_list)
    analysis["survey_id"] = survey.id
    analysis["survey_title"] = survey.title
    return analysis

@app.get("/api/surveys/{survey_id}/export-csv")
@app.get("/api/surveys/{survey_id}/export.csv")
def export_survey_csv(survey_id: str, db: Session = Depends(get_db)):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    responses = db.query(SurveyResponse).filter(SurveyResponse.survey_id == survey_id).all()
    if not responses:
        raise HTTPException(status_code=400, detail="No responses to export")

    survey_dict = {"id": survey.id, "title": survey.title, "questions": survey.questions}
    personas_dict = [r.persona.to_dict() for r in responses]
    responses_list = [{"persona_code": r.persona.persona_code, "answers": r.answers} for r in responses]

    csv_content = generate_csv_export(survey_dict, personas_dict, responses_list)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=survey_results_{survey_id[:8]}.csv"
        }
    )

# --- 1on1 AI インタビュー ---

@app.post("/api/personas/{persona_id}/chat")
@app.post("/api/interview/{persona_id}/chat")
async def interview_chat(persona_id: str, req: InterviewMessageRequest, db: Session = Depends(get_db)):
    persona = db.query(Persona).filter(Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    session = db.query(InterviewSession).filter(InterviewSession.persona_id == persona_id).first()
    if not session:
        session = InterviewSession(persona_id=persona_id, messages=[])
        db.add(session)
        db.commit()
        db.refresh(session)

    # 過去アンケート回答の取得
    latest_resp = db.query(SurveyResponse).filter(SurveyResponse.persona_id == persona_id).order_by(SurveyResponse.created_at.desc()).first()
    survey_answers = latest_resp.answers if latest_resp else None

    # AI回答生成
    reply = await chat_with_persona(
        persona=persona.to_dict(),
        history=session.messages,
        user_message=req.content,
        survey_answers=survey_answers
    )

    new_messages = list(session.messages)
    new_messages.append({"role": "user", "content": req.content})
    new_messages.append({"role": "assistant", "content": reply})
    session.messages = new_messages
    db.commit()

    return {
        "reply": reply,
        "history": new_messages
    }

@app.get("/api/personas/{persona_id}/chat")
@app.get("/api/interview/{persona_id}/chat")
def get_interview_history(persona_id: str, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.persona_id == persona_id).first()
    if not session:
        return {"messages": []}
    return {"messages": session.messages}

# --- 商品コンセプト評価 ---

@app.post("/api/concept-evaluations")
async def evaluate_concepts(req: ConceptEvaluationRequest, db: Session = Depends(get_db)):
    cohort = db.query(PersonaCohort).filter(PersonaCohort.id == req.cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")

    personas = db.query(Persona).filter(Persona.cohort_id == req.cohort_id).limit(req.sample_size).all()
    personas_dicts = [p.to_dict() for p in personas]
    concepts_dicts = [c.dict() for c in req.concepts]

    results = await run_concept_comparison(concepts_dicts, personas_dicts, use_mock=req.use_mock)

    eval_record = ConceptEvaluation(
        cohort_id=req.cohort_id,
        title=req.title,
        concepts=concepts_dicts,
        results=results
    )
    db.add(eval_record)
    db.commit()
    db.refresh(eval_record)

    return {
        "id": eval_record.id,
        "title": eval_record.title,
        "cohort_id": eval_record.cohort_id,
        "results": eval_record.results,
        "created_at": eval_record.created_at.isoformat()
    }

@app.get("/api/concept-evaluations/{eval_id}")
def get_concept_evaluation_detail(eval_id: str, db: Session = Depends(get_db)):
    ev = db.query(ConceptEvaluation).filter(ConceptEvaluation.id == eval_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Concept evaluation not found")
    return {
        "id": ev.id,
        "title": ev.title,
        "cohort_id": ev.cohort_id,
        "concepts": ev.concepts,
        "results": ev.results,
        "created_at": ev.created_at.isoformat()
    }

@app.get("/api/concept-evaluations")
def list_concept_evaluations(cohort_id: str = None, db: Session = Depends(get_db)):
    query = db.query(ConceptEvaluation)
    if cohort_id:
        query = query.filter(ConceptEvaluation.cohort_id == cohort_id)
    records = query.order_by(ConceptEvaluation.created_at.desc()).all()
    return [{
        "id": r.id,
        "title": r.title,
        "cohort_id": r.cohort_id,
        "concepts_count": len(r.concepts),
        "created_at": r.created_at.isoformat()
    } for r in records]

# --- 仮想A/B実験 (AI4PB・Nature 2026準拠) ---

@app.post("/api/ab-experiments")
async def create_and_run_ab_experiment(req: VirtualABExperimentRequest, db: Session = Depends(get_db)):
    cohort = db.query(PersonaCohort).filter(PersonaCohort.id == req.cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")

    personas = db.query(Persona).filter(Persona.cohort_id == req.cohort_id).all()
    if not personas:
        raise HTTPException(status_code=400, detail="No personas in target cohort")

    personas_dicts = [p.to_dict() for p in personas]

    res = await run_virtual_ab_experiment(
        cohort_personas=personas_dicts,
        experiment_title=req.title,
        research_question=req.research_question or "",
        control_condition=req.control_condition,
        treatment_condition=req.treatment_condition,
        order_design=req.order_design,
        use_mock=req.use_mock,
        sample_size=req.sample_size or 50
    )

    # P0安全性要件7: Gemini API失敗時はモックへの切替をユーザーに明示し、実AI推論として集計・保存しない
    if res.get("engine_type") == "mock_fallback":
        return {
            "id": "mock_fallback_transient",
            "title": req.title,
            "cohort_id": req.cohort_id,
            "status": "mock_fallback_warning",
            "is_fallback": True,
            "engine_type": "mock_fallback",
            "warning": res.get("fallback_warning"),
            "results": res,
            "created_at": datetime.now().isoformat()
        }

    provenance = {
        "model_version": res.get("model_name", settings.DEFAULT_GEMINI_MODEL),
        "engine_type": res.get("engine_type", "gemini_agent"),
        "is_demo_mode": res.get("is_demo_mode", False),
        "academic_reference": "Nature (2026) LLMs Can Predict the Results of Social Science Experiments",
        "sample_size": res.get("sample_size", len(personas_dicts)),
        "order_design": req.order_design
    }

    ab_record = VirtualABExperiment(
        cohort_id=req.cohort_id,
        title=req.title,
        research_question=req.research_question,
        control_condition=req.control_condition,
        treatment_condition=req.treatment_condition,
        order_design=req.order_design,
        metrics=res,
        provenance_info=provenance
    )
    db.add(ab_record)
    db.commit()
    db.refresh(ab_record)

    return {
        "id": ab_record.id,
        "title": ab_record.title,
        "cohort_id": ab_record.cohort_id,
        "results": res,
        "created_at": ab_record.created_at.isoformat()
    }

@app.get("/api/ab-experiments/{exp_id}")
def get_ab_experiment_detail(exp_id: str, db: Session = Depends(get_db)):
    exp = db.query(VirtualABExperiment).filter(VirtualABExperiment.id == exp_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="A/B experiment not found")
    return {
        "id": exp.id,
        "cohort_id": exp.cohort_id,
        "title": exp.title,
        "research_question": exp.research_question,
        "control_condition": exp.control_condition,
        "treatment_condition": exp.treatment_condition,
        "order_design": exp.order_design,
        "results": exp.metrics,
        "provenance_info": exp.provenance_info,
        "created_at": exp.created_at.isoformat()
    }

@app.get("/api/ab-experiments/{exp_id}/export-csv")
def export_ab_csv(exp_id: str, db: Session = Depends(get_db)):
    exp = db.query(VirtualABExperiment).filter(VirtualABExperiment.id == exp_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="A/B experiment not found")

    csv_content = export_ab_experiment_csv(exp.metrics)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=ab_experiment_{exp_id[:8]}.csv"
        }
    )

@app.get("/api/ab-experiments")
def list_ab_experiments(cohort_id: str = None, db: Session = Depends(get_db)):
    query = db.query(VirtualABExperiment)
    if cohort_id:
        query = query.filter(VirtualABExperiment.cohort_id == cohort_id)
    records = query.order_by(VirtualABExperiment.created_at.desc()).all()
    return [{
        "id": r.id,
        "title": r.title,
        "cohort_id": r.cohort_id,
        "order_design": r.order_design,
        "created_at": r.created_at.isoformat()
    } for r in records]

# --- Human-AI 比較検証 (AI4PB 予測性能ベンチマーク) ---

@app.post("/api/validations")
def run_human_ai_validation(req: HumanAIValidationRequest, db: Session = Depends(get_db)):
    survey = db.query(Survey).filter(Survey.id == req.survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    ai_responses = db.query(SurveyResponse).filter(SurveyResponse.survey_id == req.survey_id).all()
    if not ai_responses:
        raise HTTPException(status_code=400, detail="No AI responses found for this survey. Run simulation first.")

    ai_list = [{
        "persona": r.persona.to_dict(),
        "answers": r.answers
    } for r in ai_responses]

    if req.is_demo or not req.human_data_csv:
        human_records = generate_demo_human_survey_data(survey.questions, count=len(ai_list))
    else:
        human_records = parse_human_csv_data(req.human_data_csv, survey.questions)

    validation_result = evaluate_human_ai_validation(
        ai_responses=ai_list,
        human_records=human_records,
        questions=survey.questions,
        split_ratio=req.split_ratio
    )

    val_record = HumanAIValidation(
        survey_id=req.survey_id,
        dataset_name=req.dataset_name,
        is_demo=1 if req.is_demo else 0,
        human_data=human_records[:50], # サンプル保存
        split_ratio=req.split_ratio,
        validation_results=validation_result
    )
    db.add(val_record)
    db.commit()
    db.refresh(val_record)

    return {
        "id": val_record.id,
        "survey_id": val_record.survey_id,
        "dataset_name": val_record.dataset_name,
        "is_demo": bool(val_record.is_demo),
        "results": validation_result,
        "created_at": val_record.created_at.isoformat()
    }

@app.get("/api/validations/{val_id}")
def get_validation_detail(val_id: str, db: Session = Depends(get_db)):
    val = db.query(HumanAIValidation).filter(HumanAIValidation.id == val_id).first()
    if not val:
        raise HTTPException(status_code=404, detail="Validation record not found")
    return {
        "id": val.id,
        "survey_id": val.survey_id,
        "dataset_name": val.dataset_name,
        "is_demo": bool(val.is_demo),
        "results": val.validation_results,
        "created_at": val.created_at.isoformat()
    }

@app.get("/api/validations")
def list_validations(survey_id: str = None, db: Session = Depends(get_db)):
    query = db.query(HumanAIValidation)
    if survey_id:
        query = query.filter(HumanAIValidation.survey_id == survey_id)
    records = query.order_by(HumanAIValidation.created_at.desc()).all()
    return [{
        "id": r.id,
        "survey_id": r.survey_id,
        "dataset_name": r.dataset_name,
        "is_demo": bool(r.is_demo),
        "created_at": r.created_at.isoformat()
    } for r in records]

# --- 自律調査オーケストレーター (P1: エージェントらしさ) ---

@app.get("/api/orchestrator/presets")
def get_orchestrator_presets():
    """調査オーケストレーター用の標準プリセット課題一覧"""
    return [
        {
            "id": "smartwatch_health",
            "title": "次世代スマートウォッチ健康モニタリング受容性",
            "goal": "心電図・血圧・睡眠時無呼吸測定を搭載した次世代スマートウォッチ（月額サブスク980円）に対する20〜60代男女の受容性・価格妥当性・懸念点の調査",
            "recommended_count": 50
        },
        {
            "id": "ethical_food",
            "title": "フードロス削減エシカル定期便の購買意向",
            "goal": "賞味期限間近や規格外の国産高品質食材を定価の40%引で届ける定期便サービスに対する、共働き子育て世帯・単身層の受容性と価格感度調査",
            "recommended_count": 50
        },
        {
            "id": "senior_digital_support",
            "title": "シニア向け対話型AI生活サポート端末",
            "goal": "画面付き音声対話端末による服薬リマインド・孤独感解消・遠隔見守りサービスに対する、60代以上シニア層およびその家族の安心感と支払い意向",
            "recommended_count": 50
        }
    ]

@app.post("/api/orchestrator/run")
async def run_orchestrator_pipeline(req: AutonomousResearchRequest, db: Session = Depends(get_db)):
    """ペルソナ生成 -> 設問設計 -> 回答推論 -> 多変量解析&サマリー要約を一気通貫で自律実行"""
    if not req.research_goal or not req.research_goal.strip():
        raise HTTPException(status_code=400, detail="調査課題（research_goal）を入力してください。")

    result = await run_autonomous_orchestration(
        research_goal=req.research_goal.strip(),
        target_count=req.target_count,
        generation_mode=req.generation_mode,
        use_mock=req.use_mock,
        db=db
    )
    return result

# --- 静的フロントエンド配信（本番・Cloud Run・ローカル統合用） ---
possible_dist_paths = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")),
    os.path.abspath(os.path.join(os.getcwd(), "frontend", "dist")),
]
for p in possible_dist_paths:
    if os.path.exists(p) and os.path.isdir(p):
        app.mount("/", StaticFiles(directory=p, html=True), name="static")
        break
