export interface Persona {
  id: string;
  cohort_id: string;
  persona_code: string;
  generation_mode?: 'mode_a' | 'mode_b' | 'mode_c';
  name: string;
  age: number;
  age_group: string;
  gender: string;
  region: string;
  prefecture: string;
  occupation: string;
  employment_type: string;
  household: string;
  education: string;
  personal_income: number;
  household_income: number;
  hobbies: string[];
  values_segment: string;
  lifestyle: string;
  info_channels: string[];
  decision_style: string;
  consumption_profile: string;
  life_history?: string;
  purchase_experiences?: string[];
  grounded_interview?: {
    values?: string[];
    consumption_habits?: string[];
    purchase_triggers?: string[];
    price_sensitivity?: string;
    decision_style?: string;
    daily_habits?: string[];
    interests?: string[];
    verbatim_quotes?: string[];
  };
  is_consented_human_subject?: number;
  data_consent_status?: string;
}

export interface Cohort {
  id: string;
  name: string;
  target_count: number;
  seed: number;
  generation_mode?: 'mode_a' | 'mode_b' | 'mode_c';
  interview_dataset_id?: string;
  config?: any;
  provenance_info?: any;
  created_at: string;
  persona_count: number;
  distribution?: CohortDistribution;
}

export interface CohortDistribution {
  total_count: number;
  age_distribution: {
    actual_counts: Record<string, number>;
    actual_ratio: Record<string, number>;
    benchmark_ratio: Record<string, number>;
  };
  gender_distribution: {
    actual_counts: Record<string, number>;
    actual_ratio: Record<string, number>;
    benchmark_ratio: Record<string, number>;
  };
  region_distribution: {
    actual_counts: Record<string, number>;
    actual_ratio: Record<string, number>;
    benchmark_ratio: Record<string, number>;
  };
  values_distribution: {
    actual_counts: Record<string, number>;
    actual_ratio: Record<string, number>;
  };
  income_stats: {
    personal_mean: number;
    personal_median: number;
    household_mean: number;
    household_median: number;
  };
  data_source: string;
  notes: string;
}

export interface QuestionDef {
  id: string;
  text: string;
  type: 'single' | 'multiple' | 'scale5' | 'text';
  options: string[];
  required?: boolean;
}

export interface Survey {
  id: string;
  cohort_id: string;
  title: string;
  description?: string;
  questions: QuestionDef[];
  model_name?: string;
  created_at: string;
  response_count: number;
}

export interface SurveyAnalysis {
  total_respondents: number;
  questions_summary: Record<string, any>;
  crosstabs: Record<string, Record<string, any>>;
  multivariate: {
    pca?: {
      explained_variance_ratio: number[];
      total_variance_explained: number;
      points: Array<{
        persona_code: string;
        name: string;
        age: number;
        gender: string;
        values_segment: string;
        income: number;
        x: number;
        y: number;
        cluster: number;
        cluster_name: string;
      }>;
    };
    clustering?: {
      cluster_names: Record<number, string>;
      cluster_distribution: Record<string, number>;
    };
    error?: string;
  };
  text_summaries: Record<string, {
    summary: string;
    sentiment_ratio: { positive: number; neutral: number; negative: number };
    key_themes: Array<{ theme: string; count: number }>;
    total_analyzed: number;
  }>;
  disclaimer: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ConceptItem {
  name: string;
  description: string;
  price: number;
  target_category: string;
}

export interface ConceptEvaluationResult {
  concept_name: string;
  mean_purchase_intent: number;
  mean_interest: number;
  price_perception: Record<string, number>;
  top_appeal_segments: string[];
  assumed_usage_scenes: string[];
  hesitation_reasons: string[];
  improvement_suggestions: string[];
  overall_critique: string;
}

export interface ConceptComparison {
  evaluated_concepts: ConceptEvaluationResult[];
  best_purchase_intent: { name: string; score: number };
  best_interest: { name: string; score: number };
  strategic_recommendation: string;
}

// AI4PB Research Extensions
export interface InterviewDataset {
  id: string;
  name: string;
  source_type: string;
  raw_content?: string;
  extracted_data?: any[];
  consent_confirmed: boolean;
  is_demo: boolean;
  participant_count: number;
  created_at: string;
}

export interface VirtualABExperiment {
  id: string;
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
  order_design: string;
  results: {
    title: string;
    sample_size: number;
    order_design: string;
    metric_analysis: Record<string, {
      control_mean: number;
      treatment_mean: number;
      delta_mean: number;
      percentage_change: number;
      cohens_d: number;
      effect_size_label: string;
      t_statistic: number;
      p_value: number;
      is_statistically_significant: boolean;
    }>;
    subgroups: {
      by_gender: Record<string, any>;
      by_age: Record<string, any>;
      by_values: Record<string, any>;
    };
    individual_results: any[];
    simulation_disclaimer: string;
    academic_reference?: any;
  };
  provenance_info?: any;
  created_at: string;
}

export interface HumanAIValidation {
  id: string;
  survey_id: string;
  dataset_name: string;
  is_demo: boolean;
  results: {
    status: string;
    is_demo_dataset: boolean;
    dataset_notice: string;
    human_sample_size: number;
    ai_sample_size: number;
    split_info: {
      mode: string;
      calibration_sample_size: number;
      test_sample_size: number;
    };
    overall_metrics: {
      overall_mae: number;
      overall_rmse: number;
      pearson_r: number;
      question_level: Record<string, any>;
    };
    out_of_sample_validation: {
      calibration_split: any;
      test_evaluation_split: any;
      generalization_notes: string;
    };
    subgroup_errors: Record<string, any>;
    individual_concordance: {
      has_individual_mapping: boolean;
      exact_match_rate?: number;
      description: string;
    };
  };
  created_at: string;
}
