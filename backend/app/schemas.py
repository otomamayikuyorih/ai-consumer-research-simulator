from typing import Any, Optional
from pydantic import BaseModel, Field

class PersonaBase(BaseModel):
    persona_code: str
    generation_mode: str = "mode_b" # "mode_a", "mode_b", "mode_c"
    name: str
    age: int
    age_group: str
    gender: str
    region: str
    prefecture: str
    occupation: str
    employment_type: str
    household: str
    education: str
    personal_income: int
    household_income: int
    hobbies: list[str]
    values_segment: str
    lifestyle: str
    info_channels: list[str]
    decision_style: str
    consumption_profile: str
    life_history: Optional[str] = ""
    purchase_experiences: Optional[list[str]] = Field(default_factory=list)
    grounded_interview: Optional[dict[str, Any]] = Field(default_factory=dict)
    is_consented_human_subject: Optional[bool] = False
    data_consent_status: Optional[str] = "synthetic_public_stats"

class PersonaOut(PersonaBase):
    id: str
    cohort_id: str

    class Config:
        from_attributes = True

class CohortCreateRequest(BaseModel):
    name: str = "日本全国・代表サンプル"
    target_count: int = 100
    seed: int = 42
    generation_mode: str = "mode_b" # "mode_a" (Demographic), "mode_b" (Synthetic Rich), "mode_c" (Interview Grounded)
    preset: str = "general_national" # "general_national", "young_digital", "senior_silver", "working_parents"
    interview_dataset_id: Optional[str] = None
    custom_distribution: Optional[dict[str, Any]] = None

class CohortOut(BaseModel):
    id: str
    name: str
    target_count: int
    seed: int
    generation_mode: str = "mode_b"
    interview_dataset_id: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    provenance_info: Optional[dict[str, Any]] = None
    created_at: Any
    persona_count: int = 0

    class Config:
        from_attributes = True

class QuestionDef(BaseModel):
    id: str
    text: str
    type: str # "single", "multiple", "scale5", "text"
    options: list[str] = Field(default_factory=list)
    required: bool = True

class SurveyCreateRequest(BaseModel):
    cohort_id: str
    title: str
    description: Optional[str] = ""
    questions: list[QuestionDef]

class SurveyOut(BaseModel):
    id: str
    cohort_id: str
    title: str
    description: Optional[str] = ""
    questions: list[QuestionDef]
    model_name: Optional[str] = None
    created_at: Any
    response_count: int = 0

    class Config:
        from_attributes = True

class SurveyExecutionRequest(BaseModel):
    survey_id: str
    model_name: Optional[str] = None
    use_mock: bool = False
    batch_size: int = 10

class InterviewMessageRequest(BaseModel):
    content: str

class ConceptItem(BaseModel):
    name: str
    description: str
    price: int # JPY
    target_category: str

class ConceptEvaluationRequest(BaseModel):
    cohort_id: str
    title: str
    concepts: list[ConceptItem]
    sample_size: int = 50
    use_mock: bool = False

# --- AI4PB 拡張スキーマ ---

class InterviewIngestRequest(BaseModel):
    name: str
    source_type: str = "text" # "text", "csv", "manual"
    raw_content: str
    consent_confirmed: bool = True
    is_demo: bool = False

class VirtualABExperimentRequest(BaseModel):
    cohort_id: str
    title: str
    research_question: Optional[str] = ""
    control_condition: dict[str, Any] # {label, description, price, ad_copy}
    treatment_condition: dict[str, Any] # {label, description, price, ad_copy}
    order_design: str = "counterbalanced" # "counterbalanced", "randomized"
    use_mock: bool = False

class HumanAIValidationRequest(BaseModel):
    survey_id: str
    dataset_name: str
    is_demo: bool = False
    human_data_csv: Optional[str] = None # CSV string
    split_ratio: str = "50_50_split"
