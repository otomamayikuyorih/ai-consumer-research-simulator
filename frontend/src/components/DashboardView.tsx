import React, { useState } from 'react';
import { 
  Users, 
  FileQuestion, 
  BarChart3, 
  Sparkles, 
  ArrowRight, 
  CheckCircle2, 
  TrendingUp, 
  Layers,
  Database,
  Cpu,
  Bot,
  Play,
  RotateCcw,
  AlertTriangle,
  ChevronRight,
  Sliders,
  Check,
  Target
} from 'lucide-react';
import { Cohort, Survey } from '../types';
import { runAutonomousOrchestration } from '../services/api';

interface DashboardViewProps {
  cohorts: Cohort[];
  surveys: Survey[];
  onNavigate: (tab: string) => void;
  onSelectCohort: (cohort: Cohort) => void;
  onSelectSurvey: (survey: Survey) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  cohorts,
  surveys,
  onNavigate,
  onSelectCohort,
  onSelectSurvey,
}) => {
  const totalPersonas = cohorts.reduce((acc, c) => acc + (c.persona_count || 0), 0);
  const totalResponses = surveys.reduce((acc, s) => acc + (s.response_count || 0), 0);

  // 自律型調査オーケストレーター (P1: エージェントらしさ)
  const [researchGoal, setResearchGoal] = useState('心電図・血圧測定を搭載した次世代スマートウォッチ（月額サブスク980円）に対する20〜60代男女の受容性・価格妥当性・懸念点の調査');
  const [targetCount, setTargetCount] = useState(30);
  const [useMock, setUseMock] = useState(false);
  const [isOrchestrating, setIsOrchestrating] = useState(false);
  const [orchestratorResult, setOrchestratorResult] = useState<any | null>(null);
  const [orchestratorError, setOrchestratorError] = useState<string | null>(null);

  const presets = [
    {
      title: 'スマートウォッチ健康受容性',
      goal: '心電図・血圧測定を搭載した次世代スマートウォッチ（月額サブスク980円）に対する20〜60代男女の受容性・価格妥当性・懸念点の調査',
      count: 30
    },
    {
      title: 'フードロス削減エシカル定期便',
      goal: '規格外・賞味期限間近の国産高品質食材を40%引で届ける定期便に対する、共働き子育て世帯・単身層の受容性と価格感度調査',
      count: 30
    },
    {
      title: 'シニア向け対話型AI生活サポート',
      goal: '画面付き音声端末による服薬リマインド・孤独感解消・遠隔見守りサービスに対する、60代以上シニア層および家族の支払い意向調査',
      count: 30
    }
  ];

  const handleRunOrchestrator = async () => {
    if (!researchGoal.trim()) {
      alert('調査課題を入力してください');
      return;
    }
    setIsOrchestrating(true);
    setOrchestratorError(null);
    try {
      const res = await runAutonomousOrchestration({
        research_goal: researchGoal,
        target_count: targetCount,
        generation_mode: 'mode_b',
        use_mock: useMock,
      });
      setOrchestratorResult(res);
    } catch (err: any) {
      setOrchestratorError(err.message || '自律調査パイプラインの実行に失敗しました');
    } finally {
      setIsOrchestrating(false);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Hero Welcome */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-radial from-brand-500/20 to-transparent pointer-events-none"></div>
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-sm border border-white/10 text-xs font-medium text-brand-200 mb-4">
            <Sparkles className="w-3.5 h-3.5 text-brand-300" />
            AI-Driven Virtual Consumer Research Platform
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-3">
            統計的ペルソナ群による<br className="hidden sm:inline" />リアルタイム消費者調査シミュレーター
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed mb-6">
            総務省「国勢調査」「家計調査」等の公的統計に基づき、年齢・年収・地域・価値観がリアルに相関した100〜1,000名の仮想消費者を生成。Google Gemini AIによりアンケート回答、クロス集計、多変量解析、1対1深掘りインタビュー、商品受容性評価を即座に実施できます。
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => onNavigate('personas')}
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-medium text-sm flex items-center gap-2 shadow-lg shadow-brand-600/30 transition-all"
            >
              <Users className="w-4 h-4" />
              ペルソナコホートを生成
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('builder')}
              className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-medium text-sm border border-white/20 backdrop-blur-sm transition-all"
            >
              アンケートを作成する
            </button>
          </div>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500">登録コホート数</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{cohorts.length} <span className="text-xs font-normal text-slate-500">群</span></p>
          </div>
          <div className="w-11 h-11 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <Layers className="w-5 h-5" />
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500">生成ペルソナ総数</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{totalPersonas} <span className="text-xs font-normal text-slate-500">名</span></p>
          </div>
          <div className="w-11 h-11 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Users className="w-5 h-5" />
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500">作成アンケート数</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{surveys.length} <span className="text-xs font-normal text-slate-500">件</span></p>
          </div>
          <div className="w-11 h-11 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
            <FileQuestion className="w-5 h-5" />
          </div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500">シミュレーション回答総数</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{totalResponses} <span className="text-xs font-normal text-slate-500">件</span></p>
          </div>
          <div className="w-11 h-11 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <BarChart3 className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Autonomous Research Orchestrator Card (P1: エージェントらしさ) */}
      <div className="bg-white rounded-2xl border-2 border-indigo-200/80 p-6 sm:p-7 shadow-sm space-y-6 relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center">
                <Bot className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                自律型調査オーケストレーター
                <span className="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 border border-indigo-200">
                  Agentic Orchestration
                </span>
              </h2>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed max-w-3xl">
              調査課題（リサーチゴール）を入力するだけで、<strong>①公的統計ペルソナ生成</strong> ➔ <strong>②設問票の自動設計</strong> ➔ <strong>③Gemini 3.5 Flashによる並行シミュレーション</strong> ➔ <strong>④多変量解析と戦略サマリー要約</strong> までエージェントが自律的に完遂します。
            </p>
          </div>

          <div className="flex items-center gap-2 self-start lg:self-center">
            <span className="text-xs font-semibold text-slate-600">課題プリセット:</span>
            <div className="flex flex-wrap gap-1.5">
              {presets.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setResearchGoal(p.goal);
                    setTargetCount(p.count);
                  }}
                  className="px-2.5 py-1 text-xs font-medium rounded-lg bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 border border-slate-200 transition-colors text-slate-700"
                >
                  {p.title}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Form Inputs */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-800 mb-1.5">
              調査課題・リサーチゴール（自然言語で入力）
            </label>
            <textarea
              rows={3}
              value={researchGoal}
              onChange={(e) => setResearchGoal(e.target.value)}
              placeholder="例: 心電図・血圧測定を搭載した次世代スマートウォッチ（月額サブスク980円）に対する20〜60代男女の受容性・価格妥当性・懸念点の調査"
              className="w-full text-xs p-3.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 font-sans leading-relaxed"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-1">
            {/* Mode selection */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">推論エンジン</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setUseMock(false)}
                  className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 border transition-all ${
                    !useMock 
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs' 
                      : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Gemini 3.5 Flash
                </button>
                <button
                  type="button"
                  onClick={() => setUseMock(true)}
                  className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 border transition-all ${
                    useMock 
                      ? 'bg-amber-600 text-white border-amber-600 shadow-xs' 
                      : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <Sliders className="w-3.5 h-3.5" />
                  高速デモモード
                </button>
              </div>
            </div>

            {/* Target Count */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">仮想調査サンプルサイズ</label>
              <select
                value={targetCount}
                onChange={(e) => setTargetCount(Number(e.target.value))}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg bg-white font-semibold text-slate-800"
              >
                <option value={20}>20名（クイック検証・低レイテンシ）</option>
                <option value={30}>30名（推奨バランス）</option>
                <option value={50}>50名（標準代表調査）</option>
              </select>
            </div>

            {/* Run Button */}
            <div className="flex items-end">
              <button
                type="button"
                onClick={handleRunOrchestrator}
                disabled={isOrchestrating}
                className="w-full flex items-center justify-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold text-xs rounded-xl shadow-md transition-all disabled:opacity-50"
              >
                {isOrchestrating ? (
                  <>
                    <RotateCcw className="w-4 h-4 animate-spin" />
                    自律パイプラインを実行中...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    自律調査パイプラインを実行する
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Error Banner */}
        {orchestratorError && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <span>{orchestratorError}</span>
          </div>
        )}

        {/* Pipeline Execution Details & Results */}
        {orchestratorResult && (
          <div className="space-y-6 pt-4 border-t border-slate-200">
            {/* Step Progress & Observability Cards (P1-9) */}
            <div>
              <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-indigo-600" />
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    自律エージェント実行ステップ履歴 & 稼働モデル (Execution Provenance)
                  </h4>
                  <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                    orchestratorResult.overall_status === 'completed'
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : orchestratorResult.overall_status === 'partial_fallback'
                      ? 'bg-amber-100 text-amber-800 border border-amber-300'
                      : orchestratorResult.overall_status === 'fallback_demo_mode'
                      ? 'bg-sky-100 text-sky-800 border border-sky-300'
                      : 'bg-rose-100 text-rose-800 border border-rose-300'
                  }`}>
                    {orchestratorResult.overall_status === 'completed' && '✓ 実AI推論完了 (Vertex AI / Gemini)'}
                    {orchestratorResult.overall_status === 'partial_fallback' && '⚠️ 一部モック切替 (API失敗検知)'}
                    {orchestratorResult.overall_status === 'fallback_demo_mode' && '⚠️ デモモード (統計相関モック実行)'}
                    {orchestratorResult.overall_status === 'failed' && '❌ 失敗'}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[11px] font-mono text-slate-500">
                  <span>
                    所要時間: <strong className="text-slate-700">{orchestratorResult.total_duration_sec ?? (orchestratorResult.total_duration_ms / 1000).toFixed(2)}秒</strong> ({orchestratorResult.total_duration_ms}ms)
                  </span>
                  <span>•</span>
                  <span>
                    API呼出: <strong className="text-slate-700">{orchestratorResult.total_api_calls ?? 0}回</strong>
                  </span>
                  <span>•</span>
                  <span>
                    トークン: <strong className="text-indigo-600">{orchestratorResult.total_tokens?.total_tokens?.toLocaleString() ?? 0} tokens</strong>
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {orchestratorResult.steps?.map((step: any, idx: number) => {
                  const stepName = step.step_name || step.name;
                  const isFallback = step.is_fallback || step.status === 'fallback_mock';
                  const isDone = step.status === 'completed';
                  return (
                    <div key={idx} className={`p-3.5 rounded-xl border space-y-2 ${
                      isFallback
                        ? 'border-amber-300 bg-amber-50/50'
                        : isDone
                        ? 'border-slate-200 bg-slate-50/70'
                        : 'border-rose-200 bg-rose-50/50'
                    }`}>
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-slate-500">Step {idx + 1}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          isDone
                            ? 'bg-emerald-100 text-emerald-800'
                            : isFallback
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}>
                          {isDone ? '✓ 実推論完了' : isFallback ? '⚠️ モック切替' : '❌ エラー'}
                        </span>
                      </div>

                      <div className="text-xs font-bold text-slate-800 leading-snug">
                        {stepName}
                      </div>

                      <div className="pt-2 border-t border-slate-200/60 text-[11px] space-y-1 text-slate-600 font-mono">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Model:</span>
                          <span className="font-semibold text-slate-700 truncate max-w-[130px]" title={step.model_used}>
                            {step.model_used}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Duration:</span>
                          <span>{step.duration_ms}ms</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">API Calls / Tok:</span>
                          <span>{step.api_calls_count ?? 0}回 / {step.tokens_used?.total_tokens ? `${step.tokens_used.total_tokens}t` : '-'}</span>
                        </div>
                        {step.fallback_reason && (
                          <div className="pt-1 text-[10px] text-amber-700 leading-tight">
                            理由: {step.fallback_reason}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Executive Summary Card */}
            {orchestratorResult.executive_summary && (
              <div className="p-5 rounded-2xl bg-gradient-to-br from-indigo-50/60 to-purple-50/60 border border-indigo-200 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Target className="w-5 h-5 text-indigo-600" />
                    <h3 className="text-sm font-bold text-indigo-950">
                      {orchestratorResult.executive_summary.headline || 'リサーチ・エグゼクティブサマリー & 戦略提言'}
                    </h3>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-200/60 text-indigo-800">
                    Google Gemini / Vertex AI 自動要約
                  </span>
                </div>

                <p className="text-xs text-indigo-950 leading-relaxed font-medium">
                  {orchestratorResult.executive_summary.summary_text || orchestratorResult.executive_summary.summary}
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  {/* Key Findings */}
                  <div className="p-3.5 bg-white/90 rounded-xl border border-indigo-100 space-y-2">
                    <h4 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      主要な調査発見 (Key Findings)
                    </h4>
                    <ul className="text-xs text-slate-600 space-y-1 list-disc list-inside">
                      {orchestratorResult.executive_summary.key_findings?.map((k: string, i: number) => (
                        <li key={i}>{k}</li>
                      ))}
                    </ul>
                  </div>

                  {/* Strategic Actions */}
                  <div className="p-3.5 bg-white/90 rounded-xl border border-indigo-100 space-y-2">
                    <h4 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-purple-600" />
                      推奨アクション & ターゲット
                    </h4>
                    <div className="text-xs text-slate-700">
                      <span className="font-bold text-indigo-900">推奨ターゲット:</span>{' '}
                      {orchestratorResult.executive_summary.target_recommendation || orchestratorResult.executive_summary.recommended_target}
                    </div>
                    <ul className="text-xs text-slate-600 space-y-1 list-disc list-inside pt-1">
                      {orchestratorResult.executive_summary.strategic_actions?.map((a: string, i: number) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Direct Action Links */}
                <div className="flex flex-wrap gap-3 pt-3 border-t border-indigo-200/50">
                  {orchestratorResult.survey_id && (
                    <button
                      type="button"
                      onClick={() => {
                        const s = surveys.find(item => item.id === orchestratorResult.survey_id);
                        if (s) onSelectSurvey(s);
                        onNavigate('analytics');
                      }}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition-colors"
                    >
                      <BarChart3 className="w-3.5 h-3.5" />
                      多変量解析ダッシュボード（PCA・クロス集計）で詳細を見る &rarr;
                    </button>
                  )}
                  {orchestratorResult.cohort_id && (
                    <button
                      type="button"
                      onClick={() => {
                        const c = cohorts.find(item => item.id === orchestratorResult.cohort_id);
                        if (c) onSelectCohort(c);
                        onNavigate('personas');
                      }}
                      className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 font-semibold text-xs rounded-xl shadow-xs flex items-center gap-1.5 transition-colors"
                    >
                      <Users className="w-3.5 h-3.5" />
                      生成されたペルソナ群（{orchestratorResult.cohort_size}名）を確認する
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Feature Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div 
          onClick={() => onNavigate('personas')}
          className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs hover:shadow-md hover:border-brand-300 transition-all cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
            <Users className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-base text-slate-900 mb-2 group-hover:text-brand-600 transition-colors flex items-center justify-between">
            1. ペルソナ生成・統計検証
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-brand-600" />
          </h3>
          <p className="text-xs text-slate-600 leading-relaxed mb-4">
            全国代表サンプル、Z世代・ミレニアル、シニア層など、日本の人口・就業・給与統計を反映した属性相関群を即時生成し、分布整合性を確認できます。
          </p>
          <div className="text-xs font-medium text-brand-600 flex items-center gap-1">
            コホート作成へ進む &rarr;
          </div>
        </div>

        <div 
          onClick={() => onNavigate('runner')}
          className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs hover:shadow-md hover:border-brand-300 transition-all cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
            <TrendingUp className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-base text-slate-900 mb-2 group-hover:text-brand-600 transition-colors flex items-center justify-between">
            2. アンケート実行＆解析
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-brand-600" />
          </h3>
          <p className="text-xs text-slate-600 leading-relaxed mb-4">
            単一・複数・5段階尺度・自由記述の調査をペルソナ群に一括回答シミュレーション。クロス集計や主成分分析(PCA)、クラスタリングを可視化します。
          </p>
          <div className="text-xs font-medium text-indigo-600 flex items-center gap-1">
            調査シミュレーションへ &rarr;
          </div>
        </div>

        <div 
          onClick={() => onNavigate('interview')}
          className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs hover:shadow-md hover:border-brand-300 transition-all cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-lg bg-purple-100 text-purple-700 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform">
            <Sparkles className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-base text-slate-900 mb-2 group-hover:text-brand-600 transition-colors flex items-center justify-between">
            3. AIインタビュー＆評価
            <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-brand-600" />
          </h3>
          <p className="text-xs text-slate-600 leading-relaxed mb-4">
            アンケート回答者から気になるペルソナを選択し、回答理由や日常の本音を1対1で深掘り対話。新商品・新サービスのA/B受容性評価も行えます。
          </p>
          <div className="text-xs font-medium text-purple-600 flex items-center gap-1">
            AI対話・商品評価へ &rarr;
          </div>
        </div>
      </div>

      {/* Tables Row: Recent Cohorts & Recent Surveys */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cohorts List */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-sm text-slate-800 flex items-center gap-2">
              <Users className="w-4 h-4 text-brand-600" />
              仮想消費者コホート
            </h3>
            <button
              onClick={() => onNavigate('personas')}
              className="text-xs text-brand-600 hover:text-brand-700 font-medium"
            >
              すべて見る
            </button>
          </div>
          {cohorts.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-xs">
              コホートがまだありません。「ペルソナ生成」から作成してください。
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {cohorts.slice(0, 5).map((c) => (
                <div 
                  key={c.id} 
                  onClick={() => { onSelectCohort(c); onNavigate('personas'); }}
                  className="py-3 flex items-center justify-between hover:bg-slate-50 px-2 rounded-lg cursor-pointer transition-colors"
                >
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">{c.name}</h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      サンプル数: <span className="font-medium text-slate-700">{c.persona_count}人</span> | シード値: {c.seed}
                    </p>
                  </div>
                  <div className="text-xs text-slate-400">
                    {new Date(c.created_at).toLocaleDateString('ja-JP')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Surveys List */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-sm text-slate-800 flex items-center gap-2">
              <FileQuestion className="w-4 h-4 text-purple-600" />
              最近のアンケート調査
            </h3>
            <button
              onClick={() => onNavigate('runner')}
              className="text-xs text-brand-600 hover:text-brand-700 font-medium"
            >
              すべて見る
            </button>
          </div>
          {surveys.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-xs">
              アンケートがまだありません。「アンケート作成」から新規作成してください。
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {surveys.slice(0, 5).map((s) => (
                <div 
                  key={s.id} 
                  onClick={() => { onSelectSurvey(s); onNavigate('analytics'); }}
                  className="py-3 flex items-center justify-between hover:bg-slate-50 px-2 rounded-lg cursor-pointer transition-colors"
                >
                  <div>
                    <h4 className="text-sm font-semibold text-slate-900">{s.title}</h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      設問数: <span className="font-medium text-slate-700">{s.questions?.length || 0}問</span> | 回答数: <span className="font-medium text-slate-700">{s.response_count}件</span>
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {s.response_count > 0 ? (
                      <span className="px-2 py-0.5 rounded-full text-[11px] bg-emerald-50 text-emerald-700 border border-emerald-200">
                        解析可能
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[11px] bg-slate-100 text-slate-500">
                        未実施
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
