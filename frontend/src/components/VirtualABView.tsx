import React, { useState, useEffect } from 'react';
import { 
  FlaskConical, 
  ArrowRight, 
  CheckCircle2, 
  Download, 
  Sliders, 
  BarChart2, 
  Sparkles, 
  Info, 
  RotateCcw,
  Zap,
  TrendingUp,
  AlertCircle
} from 'lucide-react';
import { Cohort, VirtualABExperiment } from '../types';
import { runVirtualABExperiment, fetchABExperiments, getABExportCsvUrl } from '../services/api';

interface VirtualABViewProps {
  cohorts: Cohort[];
  activeCohort: Cohort | null;
  onSelectCohort?: (cohort: Cohort) => void;
}

export const VirtualABView: React.FC<VirtualABViewProps> = ({
  cohorts,
  activeCohort,
  onSelectCohort,
}) => {
  const [selectedCohortId, setSelectedCohortId] = useState<string>(activeCohort?.id || '');
  const [title, setTitle] = useState('環境配慮・サステナブル訴求 vs 通常版の受容性RCT実験');
  const [researchQuestion, setResearchQuestion] = useState('100%再生プラスチック容器＆植林寄付つきプレミアム版（1,480円）は、通常版（1,200円）に対し+280円の価格増でも消費者に受容されるか？');
  
  // Control
  const [controlLabel, setControlLabel] = useState('通常版（価格: 1,200円）');
  const [controlDesc, setControlDesc] = useState('高機能プレミアムヘアケアシャンプー。髪の深層まで浸透し、指通りの良いうるおいと輝きを与えます。');
  const [controlPrice, setControlPrice] = useState<number>(1200);
  const [controlAd, setControlAd] = useState('サロン品質の仕上がりをご自宅で。美しい髪へ。');

  // Treatment
  const [treatmentLabel, setTreatmentLabel] = useState('エコ・サステナブル版（価格: 1,480円）');
  const [treatmentDesc, setTreatmentDesc] = useState('高機能プレミアムヘアケアシャンプー。100%海洋回収再生プラスチック容器を採用し、売上の1%を国内森林保全に寄付します。');
  const [treatmentPrice, setTreatmentPrice] = useState<number>(1480);
  const [treatmentAd, setTreatmentAd] = useState('美しい髪と、美しい地球のために。毎日使うものから、未来を変える。');

  const [orderDesign, setOrderDesign] = useState<'counterbalanced' | 'randomized'>('counterbalanced');
  const [executionEngine, setExecutionEngine] = useState<'gemini' | 'mock'>('gemini');
  const [sampleSize, setSampleSize] = useState<number>(30);
  const [isRunning, setIsRunning] = useState(false);
  const [currentExperiment, setCurrentExperiment] = useState<VirtualABExperiment | null>(null);
  const [pastExperiments, setPastExperiments] = useState<any[]>([]);

  useEffect(() => {
    if (activeCohort) {
      setSelectedCohortId(activeCohort.id);
      loadPastExperiments(activeCohort.id);
    } else if (cohorts.length > 0) {
      setSelectedCohortId(cohorts[0].id);
      loadPastExperiments(cohorts[0].id);
    }
  }, [activeCohort, cohorts]);

  const loadPastExperiments = async (cohortId: string) => {
    try {
      const list = await fetchABExperiments(cohortId);
      setPastExperiments(list);
      if (list.length > 0 && !currentExperiment) {
        // load latest
        setCurrentExperiment(list[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleApplyPreset = (type: string) => {
    if (type === 'sustainable') {
      setTitle('環境配慮・サステナブル訴求 vs 通常版の受容性RCT実験');
      setResearchQuestion('100%再生容器と環境寄付つきプレミアム版は+280円の価格でも購入意向が維持されるか？');
      setControlLabel('通常版（価格: 1,200円）');
      setControlDesc('高機能プレミアムヘアケアシャンプー。指通りの良いうるおいと輝きを与えます。');
      setControlPrice(1200);
      setControlAd('サロン品質の仕上がりをご自宅で。美しい髪へ。');
      setTreatmentLabel('エコ・サステナブル版（価格: 1,480円）');
      setTreatmentDesc('高機能プレミアムシャンプー。100%海洋回収プラ容器＆売上の1%を森林保全に寄付。');
      setTreatmentPrice(1480);
      setTreatmentAd('美しい髪と、美しい地球のために。未来を変えるヘアケア。');
    } else if (type === 'ai_feature') {
      setTitle('AI自動レコメンド機能搭載モデルの価格受容性実験');
      setResearchQuestion('好みを学習して自動パーソナライズするスマート家電は、月額サブスク500円増でも受容されるか？');
      setControlLabel('スタンダードモデル（月額 980円）');
      setControlDesc('手動で好みの設定をカスタマイズできる高性能スマートデバイス。');
      setControlPrice(980);
      setControlAd('毎日の暮らしを、もっと自由に快適に。');
      setTreatmentLabel('AIパーソナライズモデル（月額 1,480円）');
      setTreatmentDesc('Gemini AIがあなたの生活リズムや好みを自動解析し、最適な運転を完全自動提案。');
      setTreatmentPrice(1480);
      setTreatmentAd('あなただけの専属AIが、最高に心地よい時間を演出。');
    }
  };

  const handleRunExperiment = async () => {
    if (!selectedCohortId) {
      alert('実験対象のペルソナコホートを選択してください');
      return;
    }
    setIsRunning(true);
    try {
      const exp = await runVirtualABExperiment({
        cohort_id: selectedCohortId,
        title,
        research_question: researchQuestion,
        control_condition: {
          label: controlLabel,
          description: controlDesc,
          price: controlPrice,
          ad_copy: controlAd,
        },
        treatment_condition: {
          label: treatmentLabel,
          description: treatmentDesc,
          price: treatmentPrice,
          ad_copy: treatmentAd,
        },
        order_design: orderDesign,
        use_mock: executionEngine === 'mock',
        sample_size: sampleSize,
      } as any);
      if (exp.status === 'mock_fallback_warning') {
        alert(exp.warning || 'Gemini API実行エラーのためモックにフォールバックしました');
      }
      setCurrentExperiment(exp);
      setPastExperiments((prev) => [exp, ...prev]);
    } catch (err: any) {
      alert('仮想A/B実験の実行に失敗しました: ' + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const metrics = currentExperiment?.results?.metric_analysis;
  const primaryIntent = metrics?.purchase_intent;
  const secondaryInterest = metrics?.interest;
  const secondaryPrice = metrics?.price_fairness;
  const subgroups = currentExperiment?.results?.subgroups;

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <FlaskConical className="w-6 h-6 text-indigo-600" />
              仮想A/B実験（Nature 2026 RCTシミュレータ）
            </h2>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
              Nature 2026 Reference
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            同一ペルソナ集団に対しControl（統制群）とTreatment（介入群）を提示し、回答順序バイアスを相殺しながら効果量（Cohen's d）を統計的検定します
          </p>
        </div>

        {cohorts.length > 0 && (
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500 font-medium">評価対象コホート:</label>
            <select
              value={selectedCohortId}
              onChange={(e) => {
                setSelectedCohortId(e.target.value);
                const found = cohorts.find(c => c.id === e.target.value);
                if (found && onSelectCohort) onSelectCohort(found);
                loadPastExperiments(e.target.value);
              }}
              className="bg-white border border-slate-300 text-xs font-semibold rounded-lg px-3 py-2 shadow-xs focus:ring-2 focus:ring-indigo-500 text-slate-800"
            >
              {cohorts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.persona_count}人)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Preset Buttons */}
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-slate-500">クイック設定プリセット:</span>
        <button
          onClick={() => handleApplyPreset('sustainable')}
          className="px-3 py-1 bg-white border border-slate-200 hover:border-indigo-400 text-slate-700 rounded-lg text-xs font-medium transition-colors"
        >
          🌿 サステナブル訴求・価格受容性
        </button>
        <button
          onClick={() => handleApplyPreset('ai_feature')}
          className="px-3 py-1 bg-white border border-slate-200 hover:border-indigo-400 text-slate-700 rounded-lg text-xs font-medium transition-colors"
        >
          🤖 AIパーソナライズ機能・サブスク実験
        </button>
      </div>

      {/* Experiment Configuration Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-bold text-slate-700 mb-1">実験タイトル</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">順序効果バイアス制御</label>
            <select
              value={orderDesign}
              onChange={(e: any) => setOrderDesign(e.target.value)}
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              <option value="counterbalanced">カウンターバランス法（50% A→B / 50% B→A）</option>
              <option value="randomized">完全ランダム化順序提示</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-700 mb-1">検証課題・リサーチクエスチョン（仮説）</label>
          <input
            type="text"
            value={researchQuestion}
            onChange={(e) => setResearchQuestion(e.target.value)}
            className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* 2 Conditions Side by Side */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          {/* Control Card */}
          <div className="p-5 rounded-xl border-2 border-slate-200 bg-slate-50/50 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                Control 条件（統制群）
              </span>
              <span className="text-xs font-semibold text-slate-600">基準価格: ¥{controlPrice.toLocaleString()}</span>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">条件名 / ラベル</label>
              <input
                type="text"
                value={controlLabel}
                onChange={(e) => setControlLabel(e.target.value)}
                className="w-full text-xs px-3 py-1.5 bg-white border border-slate-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">提示価格 (円)</label>
              <input
                type="number"
                value={controlPrice}
                onChange={(e) => setControlPrice(Number(e.target.value))}
                className="w-full text-xs px-3 py-1.5 bg-white border border-slate-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">商品・サービス説明文（刺激文章）</label>
              <textarea
                rows={3}
                value={controlDesc}
                onChange={(e) => setControlDesc(e.target.value)}
                className="w-full text-xs p-2.5 bg-white border border-slate-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">広告キャッチコピー</label>
              <input
                type="text"
                value={controlAd}
                onChange={(e) => setControlAd(e.target.value)}
                className="w-full text-xs px-3 py-1.5 bg-white border border-slate-300 rounded-lg"
              />
            </div>
          </div>

          {/* Treatment Card */}
          <div className="p-5 rounded-xl border-2 border-indigo-200 bg-indigo-50/20 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-100 text-indigo-700">
                Treatment 条件（介入群）
              </span>
              <span className="text-xs font-semibold text-indigo-700">検証価格: ¥{treatmentPrice.toLocaleString()}</span>
            </div>
            <div>
              <label className="block text-xs font-semibold text-indigo-900 mb-1">条件名 / ラベル</label>
              <input
                type="text"
                value={treatmentLabel}
                onChange={(e) => setTreatmentLabel(e.target.value)}
                className="w-full text-xs px-3 py-1.5 bg-white border border-indigo-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-indigo-900 mb-1">提示価格 (円)</label>
              <input
                type="number"
                value={treatmentPrice}
                onChange={(e) => setTreatmentPrice(Number(e.target.value))}
                className="w-full text-xs px-3 py-1.5 bg-white border border-indigo-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-indigo-900 mb-1">商品・サービス説明文（刺激文章）</label>
              <textarea
                rows={3}
                value={treatmentDesc}
                onChange={(e) => setTreatmentDesc(e.target.value)}
                className="w-full text-xs p-2.5 bg-white border border-indigo-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-indigo-900 mb-1">広告キャッチコピー</label>
              <input
                type="text"
                value={treatmentAd}
                onChange={(e) => setTreatmentAd(e.target.value)}
                className="w-full text-xs px-3 py-1.5 bg-white border border-indigo-300 rounded-lg"
              />
            </div>
          </div>
        </div>

        {/* Execution Mode & Sample Size Setting */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-800 mb-1">推論エンジンモード</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setExecutionEngine('gemini')}
                className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 border transition-all ${
                  executionEngine === 'gemini'
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                Gemini 3.8 Flash (実推論)
              </button>
              <button
                type="button"
                onClick={() => setExecutionEngine('mock')}
                className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 border transition-all ${
                  executionEngine === 'mock'
                    ? 'bg-amber-600 text-white border-amber-600 shadow-xs'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
                }`}
              >
                <Sliders className="w-3.5 h-3.5" />
                ルールベース (デモモード)
              </button>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">
              {executionEngine === 'gemini' 
                ? '提示順序（Counterbalancing）をプロンプトに注入し、ペルソナごとに自律推論します'
                : 'APIを消費せず高速に統計相関モデルで模擬評価します（デモ用）'}
            </p>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-800 mb-1">実験サンプルサイズ (N数)</label>
            <select
              value={sampleSize}
              onChange={(e) => setSampleSize(Number(e.target.value))}
              className="w-full text-xs px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-800 font-semibold"
            >
              <option value={20}>20名（クイック検証・高速）</option>
              <option value={30}>30名（推奨バランス）</option>
              <option value={50}>50名（標準統計検定）</option>
              <option value={100}>100名（高精度検出力）</option>
            </select>
            <p className="text-[11px] text-slate-500 mt-1">
              コホートから無作為抽出したペルソナに対してA/B提示順序を均等割付します
            </p>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-slate-500 flex items-center gap-1.5">
            <Info className="w-4 h-4 text-slate-400" />
            <span>同一ペルソナによる被験者内評価を行い、ペア比較検定（Paired t-test）を実施します</span>
          </div>
          <button
            onClick={handleRunExperiment}
            disabled={isRunning}
            className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-md transition-all disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <RotateCcw className="w-4 h-4 animate-spin" />
                {executionEngine === 'gemini' ? 'Gemini 3.8 Flash でペルソナ推論中...' : '相関シミュレーション実行中...'}
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                仮想A/B実験を開始する
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results View */}
      {currentExperiment && currentExperiment.results && (
        <div className="space-y-6">
          {/* Results Header */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-100 gap-4">
              <div>
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                    RCT 結果サマリー (N={currentExperiment.results.sample_size})
                  </span>
                  {currentExperiment.results.engine_type === 'gemini_agent' ? (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-indigo-600" />
                      Gemini 3.8 Flash 実ペルソナ推論モード
                    </span>
                  ) : (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 flex items-center gap-1">
                      <Sliders className="w-3 h-3 text-amber-600" />
                      ルールベース・デモモード（相関シミュレーション）
                    </span>
                  )}
                </div>
                <h3 className="text-base font-bold text-slate-900 mt-1">
                  {currentExperiment.title}
                </h3>
                <p className="text-xs text-slate-500">
                  提示順序設計: {currentExperiment.order_design === 'counterbalanced' ? 'カウンターバランス法 (50:50割付・プロンプト順序反映)' : '完全ランダム提示'}
                </p>
                {currentExperiment.results.fallback_warning && (
                  <div className="mt-2 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-800 font-semibold">
                    {currentExperiment.results.fallback_warning}
                  </div>
                )}
              </div>

              <a
                href={getABExportCsvUrl(currentExperiment.id)}
                download
                className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors w-fit"
              >
                <Download className="w-4 h-4 text-slate-600" />
                A/B個票データ CSV ダウンロード (BOM付)
              </a>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6">
              {/* Primary: Purchase Intent */}
              <div className="p-5 rounded-xl border border-indigo-200 bg-indigo-50/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-indigo-900">購入意向 (5段階評価)</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    primaryIntent?.is_statistically_significant 
                      ? 'bg-emerald-100 text-emerald-800' 
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {primaryIntent?.is_statistically_significant ? '統計的有意差あり (p<0.05)' : '有意差なし'}
                  </span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900">
                    {primaryIntent?.delta_mean && primaryIntent.delta_mean > 0 ? `+${primaryIntent.delta_mean}` : primaryIntent?.delta_mean}
                  </span>
                  <span className="text-xs font-medium text-slate-500">点差 (Control比)</span>
                  <span className={`text-xs font-bold ml-auto ${
                    (primaryIntent?.percentage_change || 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'
                  }`}>
                    {(primaryIntent?.percentage_change || 0) >= 0 ? `+${primaryIntent?.percentage_change}%` : `${primaryIntent?.percentage_change}%`}
                  </span>
                </div>
                
                <div className="mt-4 pt-3 border-t border-indigo-100 space-y-1.5 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span>Control 平均:</span>
                    <span className="font-semibold">{primaryIntent?.control_mean} 点</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Treatment 平均:</span>
                    <span className="font-semibold text-indigo-700">{primaryIntent?.treatment_mean} 点</span>
                  </div>
                  <div className="flex justify-between">
                    <span>効果量 Cohen's d:</span>
                    <span className="font-bold text-indigo-900">{primaryIntent?.cohens_d} ({primaryIntent?.effect_size_label})</span>
                  </div>
                  <div className="flex justify-between">
                    <span>検定統計量 (t値 / p値):</span>
                    <span className="font-mono text-[11px]">t={primaryIntent?.t_statistic}, p={primaryIntent?.p_value}</span>
                  </div>
                </div>
              </div>

              {/* Secondary: Interest */}
              <div className="p-5 rounded-xl border border-slate-200 bg-white">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-800">興味関心スコア</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                    Cohen's d: {secondaryInterest?.cohens_d}
                  </span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900">
                    {secondaryInterest?.delta_mean && secondaryInterest.delta_mean > 0 ? `+${secondaryInterest.delta_mean}` : secondaryInterest?.delta_mean}
                  </span>
                  <span className="text-xs font-medium text-slate-500">点差</span>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 space-y-1.5 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span>Control 平均:</span>
                    <span className="font-semibold">{secondaryInterest?.control_mean} 点</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Treatment 平均:</span>
                    <span className="font-semibold">{secondaryInterest?.treatment_mean} 点</span>
                  </div>
                  <div className="flex justify-between">
                    <span>変化率:</span>
                    <span className="font-bold">+{secondaryInterest?.percentage_change}%</span>
                  </div>
                </div>
              </div>

              {/* Secondary: Price Acceptance */}
              <div className="p-5 rounded-xl border border-slate-200 bg-white">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-800">価格受容・妥当性評価</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                    Cohen's d: {secondaryPrice?.cohens_d}
                  </span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900">
                    {secondaryPrice?.delta_mean && secondaryPrice.delta_mean > 0 ? `+${secondaryPrice.delta_mean}` : secondaryPrice?.delta_mean}
                  </span>
                  <span className="text-xs font-medium text-slate-500">点差</span>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-100 space-y-1.5 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <span>Control (¥{controlPrice.toLocaleString()}):</span>
                    <span className="font-semibold">{secondaryPrice?.control_mean} 点</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Treatment (¥{treatmentPrice.toLocaleString()}):</span>
                    <span className="font-semibold">{secondaryPrice?.treatment_mean} 点</span>
                  </div>
                  <div className="flex justify-between">
                    <span>価格差影響:</span>
                    <span className="font-bold text-rose-600">{secondaryPrice?.percentage_change}%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Subgroups Breakdown */}
            {subgroups && (
              <div className="mt-8 pt-6 border-t border-slate-200 space-y-6">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <BarChart2 className="w-4 h-4 text-indigo-600" />
                  属性別・セグメント別の効果差分析（サブグループ解析）
                </h4>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* By Gender */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
                    <h5 className="text-xs font-bold text-slate-700 mb-3">性別ごとの介入効果（購入意向 $\Delta\mu$）</h5>
                    <div className="space-y-3">
                      {Object.entries(subgroups.by_gender || {}).map(([gender, item]: [string, any]) => (
                        <div key={gender} className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span className="font-semibold text-slate-700">{gender} (N={item.count})</span>
                            <span className="font-bold text-indigo-700">
                              {item.delta_mean >= 0 ? `+${item.delta_mean}` : item.delta_mean} 点 (d={item.cohens_d})
                            </span>
                          </div>
                          <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden flex">
                            <div 
                              className={`h-full ${item.delta_mean >= 0 ? 'bg-indigo-600' : 'bg-rose-500'}`} 
                              style={{ width: `${Math.min(100, Math.max(10, Math.abs(item.delta_mean * 25)))}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* By Age */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
                    <h5 className="text-xs font-bold text-slate-700 mb-3">年代ごとの介入効果（購入意向 $\Delta\mu$）</h5>
                    <div className="space-y-2">
                      {Object.entries(subgroups.by_age || {}).map(([age, item]: [string, any]) => (
                        <div key={age} className="flex justify-between items-center text-xs py-1 border-b border-slate-200 last:border-none">
                          <span className="text-slate-600 font-medium">{age}</span>
                          <span className="text-slate-400 text-[11px]">N={item.count}</span>
                          <span className={`font-bold ${item.delta_mean >= 0 ? 'text-indigo-700' : 'text-rose-600'}`}>
                            {item.delta_mean >= 0 ? `+${item.delta_mean}` : item.delta_mean} 点
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Individual Responses Table (Order & Reasons) */}
            {currentExperiment.results.individual_responses && currentExperiment.results.individual_responses.length > 0 && (
              <div className="mt-8 pt-6 border-t border-slate-200 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                    <FlaskConical className="w-4 h-4 text-emerald-600" />
                    ペルソナ別・提示順序と個別評価理由（抜粋）
                  </h4>
                  <span className="text-[11px] text-slate-500">
                    表示: 先頭 {Math.min(10, currentExperiment.results.individual_responses.length)} 件 / 全 {currentExperiment.results.individual_responses.length} 件
                  </span>
                </div>

                <div className="overflow-x-auto rounded-xl border border-slate-200">
                  <table className="min-w-full text-xs text-left">
                    <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-3">ペルソナ</th>
                        <th className="py-2.5 px-3">属性</th>
                        <th className="py-2.5 px-3">提示順序</th>
                        <th className="py-2.5 px-3">Control評価</th>
                        <th className="py-2.5 px-3">Treatment評価</th>
                        <th className="py-2.5 px-3">Δ購入意向</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 bg-white">
                      {currentExperiment.results.individual_responses.slice(0, 10).map((r: any, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="py-2.5 px-3 font-mono font-medium text-slate-800 whitespace-nowrap">
                            {r.persona_code}
                          </td>
                          <td className="py-2.5 px-3 text-slate-600 whitespace-nowrap">
                            {r.age_group} {r.gender} ({r.values_segment})
                          </td>
                          <td className="py-2.5 px-3 whitespace-nowrap">
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                              {r.presentation_order === 'control_first' ? 'Control → Treatment' : 'Treatment → Control'}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 max-w-[200px]">
                            <div className="font-bold text-slate-900">{r.control_purchase_intent}点</div>
                            <div className="text-[11px] text-slate-500 truncate" title={r.control_reason}>{r.control_reason || '-'}</div>
                          </td>
                          <td className="py-2.5 px-3 max-w-[200px]">
                            <div className="font-bold text-indigo-700">{r.treatment_purchase_intent}点</div>
                            <div className="text-[11px] text-slate-500 truncate" title={r.treatment_reason}>{r.treatment_reason || '-'}</div>
                          </td>
                          <td className="py-2.5 px-3 font-bold whitespace-nowrap">
                            <span className={r.delta_intent > 0 ? 'text-emerald-600' : r.delta_intent < 0 ? 'text-rose-600' : 'text-slate-500'}>
                              {r.delta_intent > 0 ? `+${r.delta_intent}` : r.delta_intent}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Academic Reference & Disclaimer Alert */}
            <div className="mt-8 p-4 rounded-xl bg-amber-50/80 border border-amber-200 text-xs text-amber-900 space-y-1">
              <div className="flex items-center gap-1.5 font-bold">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>学術研究リファレンスおよび検証上の注意</span>
              </div>
              <p className="text-amber-800 leading-relaxed">
                {currentExperiment.results.simulation_disclaimer}
              </p>
              <p className="text-[11px] text-amber-700 pt-1">
                参考論文: <em>Nature (2026) "Large Language Models Can Predict the Results of Social Science Experiments"</em> / 
                Stanford University AI for Public Benefit Lab (AI4PB).
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
