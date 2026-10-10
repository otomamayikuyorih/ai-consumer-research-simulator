import { 
  Cohort, Persona, Survey, QuestionDef, SurveyAnalysis, ChatMessage, 
  ConceptItem, ConceptComparison, InterviewDataset, VirtualABExperiment, HumanAIValidation 
} from '../types';

const API_BASE = '/api';

export async function fetchSystemStatus() {
  const res = await fetch(`${API_BASE}/status`);
  if (!res.ok) throw new Error('Failed to fetch status');
  return res.json();
}

export async function fetchBenchmarks() {
  const res = await fetch(`${API_BASE}/benchmarks`);
  if (!res.ok) throw new Error('Failed to fetch benchmarks');
  return res.json();
}

export async function fetchCohorts(): Promise<Cohort[]> {
  const res = await fetch(`${API_BASE}/cohorts`);
  if (!res.ok) throw new Error('Failed to fetch cohorts');
  return res.json();
}

export async function createCohort(params: {
  name: string;
  target_count: number;
  seed: number;
  preset: string;
  generation_mode?: 'mode_a' | 'mode_b' | 'mode_c';
  interview_dataset_id?: string;
}): Promise<Cohort> {
  const res = await fetch(`${API_BASE}/cohorts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to create cohort');
  return res.json();
}

export async function deleteCohort(cohortId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/cohorts/${cohortId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete cohort');
  return res.json();
}

export async function fetchCohortDetail(cohortId: string): Promise<Cohort> {
  const res = await fetch(`${API_BASE}/cohorts/${cohortId}`);
  if (!res.ok) throw new Error('Failed to fetch cohort detail');
  return res.json();
}

export async function fetchCohortPersonas(
  cohortId: string,
  params?: {
    gender?: string;
    age_group?: string;
    values_segment?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }
): Promise<{ total: number; personas: Persona[]; items?: Persona[] }> {
  const query = new URLSearchParams();
  if (params?.gender) query.append('gender', params.gender);
  if (params?.age_group) query.append('age_group', params.age_group);
  if (params?.values_segment) query.append('values_segment', params.values_segment);
  if (params?.search) query.append('search', params.search);
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.offset) query.append('skip', params.offset.toString());

  const res = await fetch(`${API_BASE}/cohorts/${cohortId}/personas?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch personas');
  return res.json();
}

export async function fetchSurveys(cohortId?: string): Promise<Survey[]> {
  const url = cohortId ? `${API_BASE}/surveys?cohort_id=${cohortId}` : `${API_BASE}/surveys`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch surveys');
  return res.json();
}

export async function createSurvey(data: {
  cohort_id: string;
  title: string;
  description?: string;
  questions: QuestionDef[];
}): Promise<Survey> {
  const res = await fetch(`${API_BASE}/surveys`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create survey');
  return res.json();
}

export async function fetchSurveyDetail(surveyId: string): Promise<Survey> {
  const res = await fetch(`${API_BASE}/surveys/${surveyId}`);
  if (!res.ok) throw new Error('Failed to fetch survey');
  return res.json();
}

export async function runSurveySimulation(
  surveyId: string,
  options?: { model_name?: string; use_mock?: boolean; batch_size?: number }
) {
  const res = await fetch(`${API_BASE}/surveys/${surveyId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      survey_id: surveyId,
      model_name: options?.model_name,
      use_mock: options?.use_mock || false,
      batch_size: options?.batch_size || 10,
    }),
  });
  if (!res.ok) throw new Error('Failed to run simulation');
  return res.json();
}

export async function fetchSurveyAnalysis(surveyId: string): Promise<SurveyAnalysis> {
  const res = await fetch(`${API_BASE}/surveys/${surveyId}/analysis`);
  if (!res.ok) throw new Error('Failed to fetch analysis');
  return res.json();
}

export function getSurveyExportCsvUrl(surveyId: string): string {
  return `${API_BASE}/surveys/${surveyId}/export.csv`;
}

export async function sendInterviewMessage(
  personaId: string,
  content: string
): Promise<{ reply: string; history: ChatMessage[] }> {
  const res = await fetch(`${API_BASE}/interview/${personaId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error('Failed to send interview message');
  return res.json();
}

export async function fetchInterviewHistory(personaId: string): Promise<{ messages: ChatMessage[] }> {
  const res = await fetch(`${API_BASE}/interview/${personaId}/chat`);
  if (!res.ok) throw new Error('Failed to fetch chat history');
  return res.json();
}

export async function evaluateConcepts(params: {
  cohort_id: string;
  title: string;
  concepts: ConceptItem[];
  sample_size?: number;
  use_mock?: boolean;
}): Promise<{ id: string; results: ConceptComparison }> {
  const res = await fetch(`${API_BASE}/concept-evaluations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to evaluate concepts');
  return res.json();
}

export async function fetchConceptEvaluations(cohortId?: string) {
  const url = cohortId ? `${API_BASE}/concept-evaluations?cohort_id=${cohortId}` : `${API_BASE}/concept-evaluations`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to list concept evaluations');
  return res.json();
}

// =================== AI4PB Extension APIs ===================

export async function fetchInterviewDatasets(): Promise<InterviewDataset[]> {
  const res = await fetch(`${API_BASE}/interview-datasets`);
  if (!res.ok) throw new Error('Failed to fetch interview datasets');
  return res.json();
}

export async function fetchDemoInterviews(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/interview-datasets/demo`);
  if (!res.ok) throw new Error('Failed to fetch demo interview data');
  return res.json();
}

export async function ingestInterviewDataset(params: {
  name: string;
  source_type: 'text' | 'csv' | 'manual';
  raw_content: string;
  consent_confirmed: boolean;
  is_demo?: boolean;
}): Promise<InterviewDataset> {
  const res = await fetch(`${API_BASE}/interview-datasets/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to ingest interview dataset');
  return res.json();
}

export async function deleteInterviewDataset(id: string): Promise<any> {
  const res = await fetch(`${API_BASE}/interview-datasets/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete interview dataset');
  return res.json();
}

// 仮想A/B実験 (Nature 2026 Reference)
export async function runVirtualABExperiment(params: {
  cohort_id: string;
  title: string;
  research_question?: string;
  control_condition: {
    label: string;
    description: string;
    price: number;
    ad_copy?: string;
  };
  treatment_condition: {
    label: string;
    description: string;
    price: number;
    ad_copy?: string;
  };
  order_design?: 'counterbalanced' | 'randomized';
  use_mock?: boolean;
}): Promise<VirtualABExperiment> {
  const res = await fetch(`${API_BASE}/ab-experiments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to run virtual A/B experiment');
  return res.json();
}

export async function fetchABExperimentDetail(id: string): Promise<VirtualABExperiment> {
  const res = await fetch(`${API_BASE}/ab-experiments/${id}`);
  if (!res.ok) throw new Error('Failed to fetch A/B experiment detail');
  return res.json();
}

export async function fetchABExperiments(cohortId?: string): Promise<any[]> {
  const url = cohortId ? `${API_BASE}/ab-experiments?cohort_id=${cohortId}` : `${API_BASE}/ab-experiments`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch A/B experiments list');
  return res.json();
}

export function getABExportCsvUrl(id: string): string {
  return `${API_BASE}/ab-experiments/${id}/export-csv`;
}

// Human-AI 比較検証 (AI4PB Empirical Benchmarking)
export async function runHumanAIValidation(params: {
  survey_id: string;
  dataset_name: string;
  is_demo?: boolean;
  human_data_csv?: string;
  split_ratio?: '50_50_split' | '70_30_split';
}): Promise<HumanAIValidation> {
  const res = await fetch(`${API_BASE}/validations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Failed to run Human-AI validation');
  return res.json();
}

export async function fetchValidationDetail(id: string): Promise<HumanAIValidation> {
  const res = await fetch(`${API_BASE}/validations/${id}`);
  if (!res.ok) throw new Error('Failed to fetch validation detail');
  return res.json();
}

export async function fetchValidations(surveyId?: string): Promise<any[]> {
  const url = surveyId ? `${API_BASE}/validations?survey_id=${surveyId}` : `${API_BASE}/validations`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to list validations');
  return res.json();
}

// 自律調査オーケストレーター (Agentic Orchestrator)
export async function fetchOrchestratorPresets(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/orchestrator/presets`);
  if (!res.ok) throw new Error('Failed to fetch orchestrator presets');
  return res.json();
}

export async function runAutonomousOrchestration(params: {
  research_goal: string;
  target_count?: number;
  generation_mode?: 'mode_a' | 'mode_b' | 'mode_c';
  use_mock?: boolean;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/orchestrator/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || '自律調査パイプラインの実行に失敗しました');
  }
  return res.json();
}
