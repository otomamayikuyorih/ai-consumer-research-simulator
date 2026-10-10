import React, { useState } from 'react';
import { 
  Sparkles, 
  Plus, 
  Trash2, 
  Play, 
  CheckCircle2, 
  Loader2, 
  TrendingUp, 
  Scale, 
  AlertCircle,
  ThumbsUp,
  Tag
} from 'lucide-react';
import { Cohort, ConceptItem, ConceptComparison } from '../types';
import { evaluateConcepts } from '../services/api';

interface ConceptEvaluationViewProps {
  cohorts: Cohort[];
  activeCohort: Cohort | null;
}

const DEFAULT_CONCEPTS: ConceptItem[] = [
  {
    name: '案A: AI家計簿＆自動節約アシスタント',
    description: '銀行口座やレシート画像と連携し、AIが日々の無駄遣いやサブスクの最適化を自動提案。目標貯蓄額に合わせたパーソナライズ節約アドバイスを提供。',
    price: 680,
    target_category: 'FinTech / 家計管理サービス（月額サブスク）',
  },
  {
    name: '案B: 週末体験型ご褒美グルメ定期便',
    description: '全国の隠れた名店の職人が手掛ける、週末限定の贅沢ディナーキット。金曜の夜に届き、調理時間10分で本格レストランの味を家族や大切な人と楽しめる。',
    price: 4980,
    target_category: 'フードデリバリー / サブスクリプション',
  },
];

export const ConceptEvaluationView: React.FC<ConceptEvaluationViewProps> = ({
  cohorts,
  activeCohort,
}) => {
  const [selectedCohortId, setSelectedCohortId] = useState<string>(activeCohort?.id || (cohorts[0]?.id || ''));
  const [title, setTitle] = useState('新サービス受容性 A/Bテスト評価');
  const [concepts, setConcepts] = useState<ConceptItem[]>(DEFAULT_CONCEPTS);
  const [sampleSize, setSampleSize] = useState<number>(50);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [results, setResults] = useState<ConceptComparison | null>(null);

  const handleAddConcept = () => {
    const nextChar = String.fromCharCode(65 + concepts.length);
    setConcepts([
      ...concepts,
      {
        name: `案${nextChar}: 新規コンセプト案`,
        description: '商品やサービスの特徴・ベネフィットを入力してください。',
        price: 2980,
        target_category: 'カテゴリー名',
      },
    ]);
  };

  const handleUpdateConcept = (index: number, field: keyof ConceptItem, val: any) => {
    const updated = [...concepts];
    (updated[index] as any)[field] = val;
    setConcepts(updated);
  };

  const handleDeleteConcept = (index: number) => {
    if (concepts.length <= 1) return;
    setConcepts(concepts.filter((_, i) => i !== index));
  };

  const handleRunEvaluation = async () => {
    if (!selectedCohortId) {
      alert('評価対象のコホートを選択してください');
      return;
    }

    setIsEvaluating(true);
    try {
      const res = await evaluateConcepts({
        cohort_id: selectedCohortId,
        title,
        concepts,
        sample_size: sampleSize,
      });
      setResults(res.results);
    } catch (err: any) {
      alert('コンセプト評価に失敗しました: ' + err.message);
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <div className="space-y-8 pb-12 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-brand-600" />
          商品・サービスコンセプト評価（A/Bテスト）
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          新商品のコンセプト文や価格を入力し、仮想消費者群による購入意向・価格感・ためらい理由・改善提案を比較検証します
        </p>
      </div>

      {/* Setup Form */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-700 mb-1">評価タイトル</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">評価対象コホート</label>
            <select
              value={selectedCohortId}
              onChange={(e) => setSelectedCohortId(e.target.value)}
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-brand-500"
            >
              {cohorts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} (N={c.persona_count})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Concept Cards Editor */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800">
              評価対象コンセプト案 ({concepts.length}件)
            </h3>
            <button
              onClick={handleAddConcept}
              className="px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 shadow-2xs"
            >
              <Plus className="w-3.5 h-3.5 text-brand-600" />
              コンセプト案を追加
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {concepts.map((concept, idx) => (
              <div key={idx} className="bg-slate-50/60 rounded-xl border border-slate-200 p-5 space-y-3 relative group">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-brand-700">コンセプト {String.fromCharCode(65 + idx)}</span>
                  {concepts.length > 1 && (
                    <button
                      onClick={() => handleDeleteConcept(idx)}
                      className="text-slate-400 hover:text-rose-600 p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                <div>
                  <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">商品・サービス名</label>
                  <input
                    type="text"
                    value={concept.name}
                    onChange={(e) => handleUpdateConcept(idx, 'name', e.target.value)}
                    className="w-full text-xs font-semibold px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">想定価格（税込・円）</label>
                    <input
                      type="number"
                      value={concept.price}
                      onChange={(e) => handleUpdateConcept(idx, 'price', Number(e.target.value))}
                      className="w-full text-xs font-mono px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">カテゴリー</label>
                    <input
                      type="text"
                      value={concept.target_category}
                      onChange={(e) => handleUpdateConcept(idx, 'target_category', e.target.value)}
                      className="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-semibold text-slate-500 mb-0.5">コンセプト説明・特徴</label>
                  <textarea
                    rows={3}
                    value={concept.description}
                    onChange={(e) => handleUpdateConcept(idx, 'description', e.target.value)}
                    className="w-full text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          <span className="text-xs text-slate-500">
            選択中コホートの生活者サンプル（N={sampleSize}）が評価を実施します
          </span>
          <button
            onClick={handleRunEvaluation}
            disabled={isEvaluating}
            className="px-6 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs rounded-xl shadow-md shadow-brand-600/20 flex items-center gap-2 transition-all disabled:opacity-50"
          >
            {isEvaluating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                生活者評価シミュレーション中...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                コンセプト受容性評価を実行する
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results Section */}
      {results && (
        <div className="space-y-6">
          {/* Winner Banner */}
          <div className="bg-gradient-to-r from-emerald-950 via-slate-900 to-indigo-950 text-white rounded-2xl p-6 shadow-lg border border-slate-800">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs mb-2">
              <CheckCircle2 className="w-4 h-4" />
              受容性評価・A/B比較サマリー
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-3">
              <div className="bg-white/10 rounded-xl p-3.5 backdrop-blur-xs">
                <span className="text-[11px] text-slate-300 block">最高購入意向コンセプト</span>
                <p className="text-base font-bold text-white mt-0.5">
                  {results.best_purchase_intent.name}
                  <span className="text-emerald-400 ml-2 font-mono text-sm">
                    スコア: {results.best_purchase_intent.score} / 5.0
                  </span>
                </p>
              </div>
              <div className="bg-white/10 rounded-xl p-3.5 backdrop-blur-xs">
                <span className="text-[11px] text-slate-300 block">最高興味関心コンセプト</span>
                <p className="text-base font-bold text-white mt-0.5">
                  {results.best_interest.name}
                  <span className="text-brand-300 ml-2 font-mono text-sm">
                    スコア: {results.best_interest.score} / 5.0
                  </span>
                </p>
              </div>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed pt-2 border-t border-white/10">
              <strong className="text-white">戦略的インサイト:</strong> {results.strategic_recommendation}
            </p>
          </div>

          {/* Comparison Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {results.evaluated_concepts.map((ev, idx) => (
              <div key={idx} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-5">
                <div className="flex items-start justify-between pb-3 border-b border-slate-100">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Concept {String.fromCharCode(65 + idx)}</span>
                    <h4 className="font-bold text-base text-slate-900 mt-0.5">{ev.concept_name}</h4>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 block">購入意向</span>
                    <span className="text-lg font-bold text-brand-600 font-mono">{ev.mean_purchase_intent}</span>
                    <span className="text-xs text-slate-400"> / 5.0</span>
                  </div>
                </div>

                {/* Score Indicators */}
                <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <div>
                    <span className="text-slate-400 text-[10px]">興味・関心度</span>
                    <p className="font-bold text-slate-800 text-sm mt-0.5">{ev.mean_interest} <span className="text-[10px] font-normal text-slate-400">/ 5.0</span></p>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px]">適正価格評価比率</span>
                    <p className="font-bold text-emerald-600 text-sm mt-0.5">{ev.price_perception['妥当・適正価格'] || 0}%</p>
                  </div>
                </div>

                {/* Price Perception Breakdown */}
                <div className="space-y-1.5">
                  <span className="text-xs font-bold text-slate-700">価格に対する印象</span>
                  <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden flex">
                    <div className="h-full bg-emerald-500" style={{ width: `${ev.price_perception['安すぎる・お買い得'] || 0}%` }} title="お買い得"></div>
                    <div className="h-full bg-blue-500" style={{ width: `${ev.price_perception['妥当・適正価格'] || 0}%` }} title="妥当"></div>
                    <div className="h-full bg-amber-500" style={{ width: `${ev.price_perception['やや高い'] || 0}%` }} title="やや高い"></div>
                    <div className="h-full bg-rose-500" style={{ width: `${ev.price_perception['高すぎる'] || 0}%` }} title="高すぎる"></div>
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>妥当: {ev.price_perception['妥当・適正価格'] || 0}%</span>
                    <span>やや高い: {ev.price_perception['やや高い'] || 0}%</span>
                    <span>高すぎる: {ev.price_perception['高すぎる'] || 0}%</span>
                  </div>
                </div>

                {/* Qual Insights */}
                <div className="space-y-3 text-xs">
                  <div>
                    <span className="font-bold text-slate-700 block mb-1">想定利用シーン</span>
                    <div className="flex flex-wrap gap-1">
                      {ev.assumed_usage_scenes.map((sc, sIdx) => (
                        <span key={sIdx} className="text-[11px] px-2 py-0.5 bg-blue-50 text-blue-700 rounded-md">
                          {sc}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <span className="font-bold text-slate-700 block mb-1">購入をためらう理由</span>
                    <ul className="list-disc list-inside text-slate-600 space-y-0.5 text-[11px]">
                      {ev.hesitation_reasons.map((rs, rIdx) => (
                        <li key={rIdx}>{rs}</li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <span className="font-bold text-slate-700 block mb-1">受容性向上のための改善提案</span>
                    <ul className="list-disc list-inside text-emerald-800 space-y-0.5 text-[11px] bg-emerald-50/50 p-2.5 rounded-lg border border-emerald-100">
                      {ev.improvement_suggestions.map((sug, suIdx) => (
                        <li key={suIdx}>{sug}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Overall critique */}
                <div className="pt-2 border-t border-slate-100 text-xs text-slate-600 italic leading-relaxed">
                  "{ev.overall_critique}"
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
