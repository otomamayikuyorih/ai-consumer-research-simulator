import React, { useState } from 'react';
import { 
  PlayCircle, 
  CheckCircle2, 
  Loader2, 
  Cpu, 
  BarChart3, 
  Layers, 
  Sparkles,
  AlertCircle
} from 'lucide-react';
import { Survey, Cohort } from '../types';
import { runSurveySimulation } from '../services/api';

interface SurveyRunnerViewProps {
  surveys: Survey[];
  cohorts: Cohort[];
  activeSurvey: Survey | null;
  onSelectSurvey: (survey: Survey) => void;
  onNavigateToAnalysis: (survey: Survey) => void;
  systemStatus: { has_gemini_key: boolean; mode: string } | null;
}

export const SurveyRunnerView: React.FC<SurveyRunnerViewProps> = ({
  surveys,
  cohorts,
  activeSurvey,
  onSelectSurvey,
  onNavigateToAnalysis,
  systemStatus,
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [useMock, setUseMock] = useState(!systemStatus?.has_gemini_key);
  const [batchSize, setBatchSize] = useState(10);
  const [runResult, setRunResult] = useState<any>(null);

  const targetCohort = cohorts.find((c) => c.id === activeSurvey?.cohort_id);

  const handleStartSimulation = async () => {
    if (!activeSurvey) return;

    setIsRunning(true);
    setProgress(15);
    setStatusMessage('ペルソナコホートのプロファイル（年齢・年収・消費価値観）を抽出中...');

    // Progress animation ticker
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev < 85) return prev + Math.floor(Math.random() * 15) + 5;
        return prev;
      });
    }, 600);

    try {
      setStatusMessage(
        useMock
          ? '統計相関シミュレーションエンジンで100名の回答をバッチ生成中...'
          : 'Google Gemini APIによる生活者回答プロンプトを一括実行中...'
      );

      const res = await runSurveySimulation(activeSurvey.id, {
        use_mock: useMock,
        batch_size: batchSize,
      });

      clearInterval(timer);
      setProgress(100);
      setStatusMessage('全設問の回答収集が完了しました。クロス集計と多変量解析を生成しています。');
      setRunResult(res);
    } catch (err: any) {
      clearInterval(timer);
      alert('シミュレーション実行中にエラーが発生しました: ' + err.message);
      setIsRunning(false);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-8 pb-12 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <PlayCircle className="w-6 h-6 text-brand-600" />
          調査シミュレーションの実行
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          仮想消費者コホートの全ペルソナに対して一括でアンケートを配信・回答シミュレーションを実行します
        </p>
      </div>

      {/* Survey & Cohort Selection */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">実行対象のアンケート</label>
          <select
            value={activeSurvey?.id || ''}
            onChange={(e) => {
              const found = surveys.find((s) => s.id === e.target.value);
              if (found) onSelectSurvey(found);
            }}
            className="w-full text-xs font-semibold px-3 py-2.5 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-brand-500"
          >
            {surveys.length === 0 && <option value="">アンケートが存在しません</option>}
            {surveys.map((s) => (
              <option key={s.id} value={s.id}>
                {s.title} ({s.questions?.length || 0}問 / 現在回答: {s.response_count}件)
              </option>
            ))}
          </select>
        </div>

        {activeSurvey && (
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 space-y-3 text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <span className="text-slate-500">対象コホート</span>
              <span className="font-bold text-slate-800">{targetCohort?.name || '未設定'} (N={targetCohort?.persona_count || 100})</span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <span className="text-slate-500">設問数</span>
              <span className="font-bold text-slate-800">{activeSurvey.questions?.length} 問</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-500">過去のシミュレーション回答数</span>
              <span className="font-bold text-emerald-600">{activeSurvey.response_count} 件完了</span>
            </div>
          </div>
        )}

        {/* Engine Settings */}
        <div className="border-t border-slate-100 pt-5 space-y-4">
          <h4 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
            <Cpu className="w-4 h-4 text-brand-600" />
            AI回答シミュレーション設定
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Mode selection */}
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <span className="block text-xs font-semibold text-slate-700 mb-1">実行エンジン</span>
              <div className="space-y-2 mt-2">
                <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="radio"
                    name="mode"
                    checked={!useMock}
                    disabled={!systemStatus?.has_gemini_key}
                    onChange={() => setUseMock(false)}
                    className="text-brand-600"
                  />
                  <span>
                    Google Gemini API 連携
                    {!systemStatus?.has_gemini_key && <span className="text-[10px] text-amber-600 ml-1">(キー未設定)</span>}
                  </span>
                </label>
                <label className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="radio"
                    name="mode"
                    checked={useMock}
                    onChange={() => setUseMock(true)}
                    className="text-brand-600"
                  />
                  <span>統計推計ヒューリスティックモード (高速・無料)</span>
                </label>
              </div>
            </div>

            {/* Batch size */}
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <span className="block text-xs font-semibold text-slate-700 mb-1">一括処理バッチ規模</span>
              <select
                value={batchSize}
                onChange={(e) => setBatchSize(Number(e.target.value))}
                className="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white mt-1"
              >
                <option value={10}>10名ずつ並列処理 (推奨・安定)</option>
                <option value={20}>20名ずつ (高スループット)</option>
                <option value={5}>5名ずつ (低遅延)</option>
              </select>
              <p className="text-[10px] text-slate-400 mt-2">
                複数ペルソナを一括処理することでAPI呼び出し回数とコストを最小化します
              </p>
            </div>
          </div>
        </div>

        {/* Progress & Launch Button */}
        <div className="border-t border-slate-100 pt-5 space-y-4">
          {isRunning && (
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-600">
                <span className="flex items-center gap-1.5 font-medium">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-600" />
                  {statusMessage}
                </span>
                <span className="font-bold text-brand-600">{progress}%</span>
              </div>
              <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-brand-600 to-indigo-600 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}

          {runResult && !isRunning && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <span className="text-xs font-bold text-emerald-900">
                  {runResult.total_responses} 名のシミュレーション回答収集が完了しました！
                </span>
              </div>
              <button
                onClick={() => activeSurvey && onNavigateToAnalysis(activeSurvey)}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-xs flex items-center gap-1.5"
              >
                <BarChart3 className="w-4 h-4" />
                結果解析ダッシュボードを見る &rarr;
              </button>
            </div>
          )}

          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-brand-600" />
              個々のペルソナの全設問に対する一貫性が保持されます
            </span>
            <button
              onClick={handleStartSimulation}
              disabled={isRunning || !activeSurvey}
              className="px-6 py-3 bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs rounded-xl shadow-md shadow-brand-600/20 flex items-center gap-2 transition-all disabled:opacity-50"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  回答シミュレーション中...
                </>
              ) : (
                <>
                  <PlayCircle className="w-4 h-4" />
                  シミュレーションを開始する
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
