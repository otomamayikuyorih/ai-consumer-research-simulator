import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  AlertTriangle, 
  TrendingUp, 
  BarChart2, 
  FileText, 
  Database, 
  RotateCcw,
  Sparkles,
  HelpCircle,
  Award,
  Layers,
  ArrowRight,
  Info
} from 'lucide-react';
import { Survey, HumanAIValidation } from '../types';
import { runHumanAIValidation, fetchValidations } from '../services/api';

interface ValidationViewProps {
  surveys: Survey[];
  activeSurvey: Survey | null;
  onSelectSurvey?: (survey: Survey) => void;
}

export const ValidationView: React.FC<ValidationViewProps> = ({
  surveys,
  activeSurvey,
  onSelectSurvey,
}) => {
  const [selectedSurveyId, setSelectedSurveyId] = useState<string>(activeSurvey?.id || '');
  const [useDemoData, setUseDemoData] = useState(true);
  const [datasetName, setDatasetName] = useState('【デモ実測データ（架空の消費者モニター調査 N=100）】');
  const [rawCsv, setRawCsv] = useState('');
  const [splitRatio, setSplitRatio] = useState<'50_50_split' | '70_30_split'>('50_50_split');
  const [isValidating, setIsValidating] = useState(false);
  const [currentValidation, setCurrentValidation] = useState<HumanAIValidation | null>(null);
  const [pastValidations, setPastValidations] = useState<any[]>([]);

  useEffect(() => {
    if (activeSurvey) {
      setSelectedSurveyId(activeSurvey.id);
      loadPastValidations(activeSurvey.id);
    } else if (surveys.length > 0) {
      setSelectedSurveyId(surveys[0].id);
      loadPastValidations(surveys[0].id);
    }
  }, [activeSurvey, surveys]);

  const loadPastValidations = async (surveyId: string) => {
    try {
      const list = await fetchValidations(surveyId);
      setPastValidations(list);
      if (list.length > 0 && !currentValidation) {
        setCurrentValidation(list[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunValidation = async () => {
    if (!selectedSurveyId) {
      alert('検証対象のアンケート調査を選択してください');
      return;
    }

    setIsValidating(true);
    try {
      const result = await runHumanAIValidation({
        survey_id: selectedSurveyId,
        dataset_name: useDemoData ? '【デモ実測データ（架空の人手調査 N=100）】' : datasetName,
        is_demo: useDemoData,
        human_data_csv: useDemoData ? undefined : rawCsv,
        split_ratio: splitRatio,
      });
      setCurrentValidation(result);
      setPastValidations((prev) => [result, ...prev]);
    } catch (err: any) {
      alert('Human-AI検証の実行に失敗しました: ' + err.message);
    } finally {
      setIsValidating(false);
    }
  };

  const results = currentValidation?.results;
  const overall = results?.overall_metrics;
  const outOfSample = results?.out_of_sample_validation;
  const questionLevel = overall?.question_level || {};

  return (
    <div className="space-y-8 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <CheckCircle className="w-6 h-6 text-emerald-600" />
              Human-AI 精度検証ダッシュボード
            </h2>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              Stanford AI4PB Method
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            人手による実際のアンケート回答とGemini AI予測回答をベンチマーク比較し、MAE・RMSE・Pearson相関および未知データへの汎化性能を検証します
          </p>
        </div>

        {surveys.length > 0 && (
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500 font-medium">比較対象アンケート:</label>
            <select
              value={selectedSurveyId}
              onChange={(e) => {
                setSelectedSurveyId(e.target.value);
                const found = surveys.find(s => s.id === e.target.value);
                if (found && onSelectSurvey) onSelectSurvey(found);
                loadPastValidations(e.target.value);
              }}
              className="bg-white border border-slate-300 text-xs font-semibold rounded-lg px-3 py-2 shadow-xs focus:ring-2 focus:ring-emerald-500 text-slate-800"
            >
              {surveys.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title} ({s.response_count}回答)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Validation Setup Form Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-600" />
          実測人間データセットの指定・分割設定
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Option A: Demo Data */}
          <div 
            onClick={() => setUseDemoData(true)}
            className={`p-5 rounded-xl border-2 cursor-pointer transition-all ${
              useDemoData 
                ? 'border-emerald-500 bg-emerald-50/30 ring-2 ring-emerald-500/20' 
                : 'border-slate-200 bg-slate-50/50 hover:border-slate-300'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-800 flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${useDemoData ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                デモ用実測データセットを使用
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-200">
                デモデータ（架空）
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              即座に検証フローを体験するためのデモ人間回答データ（N=100）。実データと混同しないよう明記されます。
            </p>
          </div>

          {/* Option B: Real CSV Upload */}
          <div 
            onClick={() => setUseDemoData(false)}
            className={`p-5 rounded-xl border-2 cursor-pointer transition-all ${
              !useDemoData 
                ? 'border-emerald-500 bg-emerald-50/30 ring-2 ring-emerald-500/20' 
                : 'border-slate-200 bg-slate-50/50 hover:border-slate-300'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-800 flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${!useDemoData ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                独自の実測アンケートCSVを読み込む
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800 border border-blue-200">
                実測データ対応
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              自社で実施済みの本調査CSVデータをアップロードして、AIシミュレーションの予測精度を客観評価します。
            </p>
          </div>
        </div>

        {!useDemoData && (
          <div className="space-y-3 pt-2">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">データセット名称</label>
              <input
                type="text"
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                placeholder="例: 2026年3月 自社ヘアケアWebアンケート本調査実測データ (N=300)"
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">実測回答CSVデータ貼り付け（またはヘッダー付きテキスト）</label>
              <textarea
                rows={4}
                value={rawCsv}
                onChange={(e) => setRawCsv(e.target.value)}
                placeholder="q1,q2,age_group,gender&#10;ぜひ購入したい,4,30代,女性&#10;機会があれば購入したい,3,20代,男性"
                className="w-full text-xs font-mono p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>
        )}

        {/* Train/Test Split Setting */}
        <div className="pt-2 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-700">頑健性検証用データ分割:</span>
            <select
              value={splitRatio}
              onChange={(e: any) => setSplitRatio(e.target.value)}
              className="text-xs px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
            >
              <option value="50_50_split">50:50 折半サンプリング頑健性検証（Split-Half Robustness 50% / 50%）- 推奨</option>
              <option value="70_30_split">70:30 サブサンプリング検証（70% / 30%）</option>
            </select>
          </div>

          <button
            onClick={handleRunValidation}
            disabled={isValidating}
            className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-md transition-all disabled:opacity-50"
          >
            {isValidating ? (
              <>
                <RotateCcw className="w-4 h-4 animate-spin" />
                予測精度を計算中...
              </>
            ) : (
              <>
                <TrendingUp className="w-4 h-4" />
                Human-AI 精度検証を実行する
              </>
            )}
          </button>
        </div>
      </div>

      {/* Validation Results View */}
      {currentValidation && results && (
        <div className="space-y-6">
          {/* Scientific Transparency Alert */}
          <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200 flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
            <div className="text-xs text-blue-900 space-y-1">
              <span className="font-bold">【科学的透明性】Zero-shot 折半サンプリング検証について</span>
              <p className="text-blue-800 leading-relaxed">
                {results.scientific_transparency_notice || "本検証は事後的なパラメータ最適化（校正）を行わないZero-shot推論であり、50/50折半サンプリングにより実測データとの一致度およびサンプリング頑健性を客観測定しています。"}
              </p>
            </div>
          </div>

          {/* Demo Alert if applicable */}
          {results.is_demo_dataset && (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="text-xs text-amber-900 space-y-1">
                <span className="font-bold">【重要】デモ用データセットによる参考検証</span>
                <p className="text-amber-800 leading-relaxed">
                  {results.dataset_notice}
                </p>
              </div>
            </div>
          )}

          {/* KPI Metrics Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* MAE */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                <span>平均絶対誤差 (MAE)</span>
                <Award className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-900">
                  {overall?.overall_mae != null ? `${Math.round(overall.overall_mae * 1000) / 10}%` : 'N/A'}
                </span>
                <span className="text-xs text-slate-500">回答比率のズレ</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                0に近いほど実測とAI回答割合が完全一致
              </p>
            </div>

            {/* RMSE */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                <span>二乗平均平方根誤差 (RMSE)</span>
                <BarChart2 className="w-4 h-4 text-indigo-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-900">
                  {overall?.overall_rmse != null ? `${Math.round(overall.overall_rmse * 1000) / 10}%` : 'N/A'}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                大きな外れ値・極端な予測誤差に対する罰則指標
              </p>
            </div>

            {/* Pearson r */}
            <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                <span>Pearson 相関係数 (r)</span>
                <TrendingUp className="w-4 h-4 text-blue-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-slate-900">
                  {overall?.pearson_r != null ? overall.pearson_r : 'N/A'}
                </span>
                {overall?.pearson_r != null && (
                  <span className="text-xs font-bold text-emerald-600">
                    {overall.pearson_r >= 0.7 ? '強い相関' : overall.pearson_r >= 0.4 ? '中程度の相関' : '弱い相関'}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-400 mt-2">
                実測分布の形状とAI分布の方向性の一致度
              </p>
            </div>

            {/* Held-out Test Split MAE */}
            <div className="bg-white p-5 rounded-2xl border border-indigo-200 shadow-xs bg-indigo-50/10">
              <div className="flex items-center justify-between text-xs text-indigo-900 font-bold mb-1">
                <span>折半頑健性 (Held-out MAE)</span>
                <Layers className="w-4 h-4 text-indigo-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-indigo-950">
                  {outOfSample?.test_evaluation_split?.overall_mae != null 
                    ? `${Math.round(outOfSample.test_evaluation_split.overall_mae * 1000) / 10}%` 
                    : 'N/A'}
                </span>
                <span className="text-xs text-indigo-700">（50%折半分割）</span>
              </div>
              <p className="text-[11px] text-indigo-600 mt-2">
                {outOfSample?.scientific_interpretation || outOfSample?.generalization_notes || "Zero-shot折半推論による頑健性検証"}
              </p>
            </div>
          </div>

          {/* Question-Level Comparison Chart */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
            <h3 className="text-sm font-bold text-slate-900 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-emerald-600" />
                質問別 回答割合比較（実測人間回答 vs AIシミュレーション回答）
              </span>
              <span className="text-xs font-normal text-slate-500">
                実測サンプル数: N={results.human_sample_size} / AIサンプル数: N={results.ai_sample_size}
              </span>
            </h3>

            <div className="space-y-6">
              {Object.entries(questionLevel).map(([qId, qData]: [string, any]) => (
                <div key={qId} className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-3">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-slate-900">{qData.question_text}</span>
                    <span className="font-semibold text-emerald-700">質問単位 MAE: {Math.round(qData.mae * 1000) / 10}%</span>
                  </div>

                  <div className="space-y-3 pt-2">
                    {qData.options_comparison.map((opt: any, idx: number) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-xs text-slate-700">
                          <span className="font-medium truncate max-w-[260px]">{opt.option}</span>
                          <div className="flex gap-4 font-mono text-[11px]">
                            <span className="text-slate-600">実測: <strong>{opt.human_ratio_percent}%</strong></span>
                            <span className="text-indigo-600">AI: <strong>{opt.ai_ratio_percent}%</strong></span>
                            <span className="text-slate-400">誤差: {opt.abs_error_percent}%</span>
                          </div>
                        </div>

                        {/* Dual Bar (Human vs AI) */}
                        <div className="space-y-1">
                          {/* Human bar */}
                          <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
                            <div 
                              className="h-full bg-slate-600 rounded-full" 
                              style={{ width: `${opt.human_ratio_percent}%` }}
                              title={`実測人間: ${opt.human_ratio_percent}%`}
                            />
                          </div>
                          {/* AI bar */}
                          <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
                            <div 
                              className="h-full bg-indigo-500 rounded-full" 
                              style={{ width: `${opt.ai_ratio_percent}%` }}
                              title={`AI予測: ${opt.ai_ratio_percent}%`}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Legend */}
                  <div className="flex items-center gap-4 text-[10px] text-slate-500 pt-2 border-t border-slate-200">
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-slate-600 inline-block" />
                      実測人間回答割合
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 inline-block" />
                      AIシミュレーション回答割合
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Subgroup Breakdown Error */}
            {results.subgroup_errors && (
              <div className="pt-4 border-t border-slate-200">
                <h4 className="text-xs font-bold text-slate-800 mb-3">年代別・セグメント別の予測誤差 (MAE)</h4>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  {Object.entries(results.subgroup_errors.mae_by_age_group || {}).map(([age, errVal]: [string, any]) => (
                    <div key={age} className="p-3 bg-white rounded-lg border border-slate-200 text-center">
                      <span className="block text-[11px] font-semibold text-slate-500">{age}</span>
                      <span className="block text-base font-bold text-slate-800 mt-0.5">
                        {Math.round(errVal * 1000) / 10}%
                      </span>
                      <span className="text-[10px] text-slate-400">平均誤差</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
