import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base, engine

def generate_uuid() -> str:
    return str(uuid.uuid4())

class InterviewDataset(Base):
    __tablename__ = "interview_datasets"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False, default="text") # "text", "csv", "manual"
    raw_content = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=False, default=list) # [{persona_code, verbatim_quotes, values, etc.}]
    consent_confirmed = Column(Integer, default=1) # 1: 同意確認済み, 0: 未確認
    is_demo = Column(Integer, default=0) # 1: デモサンプル, 0: ユーザー実測
    participant_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    cohorts = relationship("PersonaCohort", back_populates="interview_dataset")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type,
            "consent_confirmed": bool(self.consent_confirmed),
            "is_demo": bool(self.is_demo),
            "participant_count": self.participant_count,
            "extracted_count": len(self.extracted_data) if self.extracted_data else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class PersonaCohort(Base):
    __tablename__ = "persona_cohorts"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    target_count = Column(Integer, nullable=False, default=100)
    seed = Column(Integer, nullable=False, default=42)
    generation_mode = Column(String, nullable=False, default="mode_b") # "mode_a", "mode_b", "mode_c"
    interview_dataset_id = Column(String, ForeignKey("interview_datasets.id"), nullable=True)
    config = Column(JSON, nullable=True) # Generation parameters, presets, stats sources
    provenance_info = Column(JSON, nullable=True) # Reproducibility audit trail
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    interview_dataset = relationship("InterviewDataset", back_populates="cohorts")
    personas = relationship("Persona", back_populates="cohort", cascade="all, delete-orphan")
    surveys = relationship("Survey", back_populates="cohort", cascade="all, delete-orphan")
    concept_tests = relationship("ConceptEvaluation", back_populates="cohort", cascade="all, delete-orphan")
    ab_experiments = relationship("VirtualABExperiment", back_populates="cohort", cascade="all, delete-orphan")

class Persona(Base):
    __tablename__ = "personas"

    id = Column(String, primary_key=True, default=generate_uuid)
    cohort_id = Column(String, ForeignKey("persona_cohorts.id"), nullable=False)
    persona_code = Column(String, nullable=False) # e.g. "P-0001"
    generation_mode = Column(String, nullable=False, default="mode_b") # "mode_a", "mode_b", "mode_c"
    name = Column(String, nullable=False) # e.g. "佐藤 健一"
    age = Column(Integer, nullable=False)
    age_group = Column(String, nullable=False) # "20代", "30代", etc.
    gender = Column(String, nullable=False) # "男性", "女性"
    region = Column(String, nullable=False) # "関東", "近畿", etc.
    prefecture = Column(String, nullable=False) # "東京都", "大阪府", etc.
    occupation = Column(String, nullable=False) # "会社員（情報通信）", etc.
    employment_type = Column(String, nullable=False) # "正規雇用", "公務員", etc.
    household = Column(String, nullable=False) # "単身", "夫婦と子ども", etc.
    education = Column(String, nullable=False) # "大学卒", etc.
    personal_income = Column(Integer, nullable=False) # 万円 (e.g. 520)
    household_income = Column(Integer, nullable=False) # 万円 (e.g. 800)
    hobbies = Column(JSON, nullable=False) # list of str
    values_segment = Column(String, nullable=False) # "コスパ・実利志向", etc.
    lifestyle = Column(String, nullable=False) # "ワークライフバランス重視", etc.
    info_channels = Column(JSON, nullable=False) # list of str
    decision_style = Column(String, nullable=False) # "徹底比較型", etc.
    consumption_profile = Column(Text, nullable=False) # Detailed description
    
    # AI4PB拡張フィールド
    life_history = Column(Text, nullable=True) # 生活史（Mode B: 仮想生活史, Mode C: 実測生活背景）
    purchase_experiences = Column(JSON, nullable=True) # 過去の購買経験・エピソード
    grounded_interview = Column(JSON, nullable=True) # インタビュー記録・Verbatim Quotes
    is_consented_human_subject = Column(Integer, default=0) # 0: 架空/統計合成, 1: 同意済み実在参加者
    data_consent_status = Column(String, default="synthetic_public_stats") # 同意状況

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    cohort = relationship("PersonaCohort", back_populates="personas")
    responses = relationship("SurveyResponse", back_populates="persona", cascade="all, delete-orphan")
    interviews = relationship("InterviewSession", back_populates="persona", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "cohort_id": self.cohort_id,
            "persona_code": self.persona_code,
            "generation_mode": self.generation_mode or "mode_b",
            "name": self.name,
            "age": self.age,
            "age_group": self.age_group,
            "gender": self.gender,
            "region": self.region,
            "prefecture": self.prefecture,
            "occupation": self.occupation,
            "employment_type": self.employment_type,
            "household": self.household,
            "education": self.education,
            "personal_income": self.personal_income,
            "household_income": self.household_income,
            "hobbies": self.hobbies or [],
            "values_segment": self.values_segment,
            "lifestyle": self.lifestyle,
            "info_channels": self.info_channels or [],
            "decision_style": self.decision_style,
            "consumption_profile": self.consumption_profile,
            "life_history": self.life_history or "",
            "purchase_experiences": self.purchase_experiences or [],
            "grounded_interview": self.grounded_interview or {},
            "is_consented_human_subject": bool(self.is_consented_human_subject),
            "data_consent_status": self.data_consent_status or "synthetic_public_stats",
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Survey(Base):
    __tablename__ = "surveys"

    id = Column(String, primary_key=True, default=generate_uuid)
    cohort_id = Column(String, ForeignKey("persona_cohorts.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    questions = Column(JSON, nullable=False) # list of questions
    model_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    cohort = relationship("PersonaCohort", back_populates="surveys")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")
    validations = relationship("HumanAIValidation", back_populates="survey", cascade="all, delete-orphan")

class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(String, primary_key=True, default=generate_uuid)
    survey_id = Column(String, ForeignKey("surveys.id"), nullable=False)
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False)
    answers = Column(JSON, nullable=False) # {q_id: answer_val}
    reasoning = Column(Text, nullable=True) # reasoning behind the answers
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    survey = relationship("Survey", back_populates="responses")
    persona = relationship("Persona", back_populates="responses")

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    persona_id = Column(String, ForeignKey("personas.id"), nullable=False)
    title = Column(String, default="AIインタビューセッション")
    messages = Column(JSON, nullable=False, default=list) # [{role: "user"|"assistant", content: str, timestamp: str}]
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    persona = relationship("Persona", back_populates="interviews")

class ConceptEvaluation(Base):
    __tablename__ = "concept_evaluations"

    id = Column(String, primary_key=True, default=generate_uuid)
    cohort_id = Column(String, ForeignKey("persona_cohorts.id"), nullable=False)
    title = Column(String, nullable=False)
    concepts = Column(JSON, nullable=False) # list of concept dicts {name, description, price, target}
    results = Column(JSON, nullable=False) # evaluation metrics & comparison
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    cohort = relationship("PersonaCohort", back_populates="concept_tests")

class VirtualABExperiment(Base):
    __tablename__ = "virtual_ab_experiments"

    id = Column(String, primary_key=True, default=generate_uuid)
    cohort_id = Column(String, ForeignKey("persona_cohorts.id"), nullable=False)
    title = Column(String, nullable=False)
    research_question = Column(Text, nullable=True)
    control_condition = Column(JSON, nullable=False) # {label, description, price, copy, etc.}
    treatment_condition = Column(JSON, nullable=False) # {label, description, price, copy, etc.}
    order_design = Column(String, default="counterbalanced") # "counterbalanced", "randomized"
    metrics = Column(JSON, nullable=False) # Cohen's d, delta means, subgroup comparisons
    provenance_info = Column(JSON, nullable=True) # prompt, seed, model, academic attribution
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    cohort = relationship("PersonaCohort", back_populates="ab_experiments")

class HumanAIValidation(Base):
    __tablename__ = "human_ai_validations"

    id = Column(String, primary_key=True, default=generate_uuid)
    survey_id = Column(String, ForeignKey("surveys.id"), nullable=False)
    dataset_name = Column(String, nullable=False)
    is_demo = Column(Integer, default=1) # 1: デモサンプル, 0: ユーザー実測
    human_data = Column(JSON, nullable=False) # [{participant_id, age, gender, answers}]
    split_ratio = Column(String, default="50_50_split")
    validation_results = Column(JSON, nullable=False) # MAE, RMSE, Pearson r, calibration vs test metrics
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    survey = relationship("Survey", back_populates="validations")

def migrate_database():
    """既存のSQLiteテーブルに対して安全にカラムを追加するマイグレーション処理"""
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        from sqlalchemy import text
        # テーブルのカラム一覧を取得
        res = conn.execute(text("PRAGMA table_info(persona_cohorts)"))
        cohort_cols = [r[1] for r in res.fetchall()]
        if "generation_mode" not in cohort_cols:
            conn.execute(text("ALTER TABLE persona_cohorts ADD COLUMN generation_mode VARCHAR DEFAULT 'mode_b'"))
        if "interview_dataset_id" not in cohort_cols:
            conn.execute(text("ALTER TABLE persona_cohorts ADD COLUMN interview_dataset_id VARCHAR"))
        if "provenance_info" not in cohort_cols:
            conn.execute(text("ALTER TABLE persona_cohorts ADD COLUMN provenance_info JSON"))

        res = conn.execute(text("PRAGMA table_info(personas)"))
        persona_cols = [r[1] for r in res.fetchall()]
        if "generation_mode" not in persona_cols:
            conn.execute(text("ALTER TABLE personas ADD COLUMN generation_mode VARCHAR DEFAULT 'mode_b'"))
        if "life_history" not in persona_cols:
            conn.execute(text("ALTER TABLE personas ADD COLUMN life_history TEXT"))
        if "purchase_experiences" not in persona_cols:
            conn.execute(text("ALTER TABLE personas ADD COLUMN purchase_experiences JSON"))
        if "grounded_interview" not in persona_cols:
            conn.execute(text("ALTER TABLE personas ADD COLUMN grounded_interview JSON"))
        if "is_consented_human_subject" not in persona_cols:
            conn.execute(text("ALTER TABLE personas ADD COLUMN is_consented_human_subject INTEGER DEFAULT 0"))
        if "data_consent_status" not in persona_cols:
            conn.execute(text("ALTER TABLE personas ADD COLUMN data_consent_status VARCHAR DEFAULT 'synthetic_public_stats'"))

        conn.commit()
