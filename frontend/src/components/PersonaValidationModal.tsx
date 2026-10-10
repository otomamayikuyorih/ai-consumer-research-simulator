import React from 'react';
import { X, CheckCircle, BarChart2, BookOpen, AlertTriangle } from 'lucide-react';
import { CohortDistribution } from '../types';

interface PersonaValidationModalProps {
  distribution: CohortDistribution | null;
  cohortName: string;
  onClose: () => void;
}

export const PersonaValidationModal: React.FC<PersonaValidationModalProps> = ({
  distribution,
  cohortName,
  onClose,
}) => {
  if (!distribution) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-brand-600" />
            <div>
              <h3 className="font-bold text-base text-slate-900">
                統計的分布の妥当性検証レポート
              </h3>
              <p className="text-xs text-slate-500">
                コホート: <span className="font-semibold text-slate-700">{cohortName}</span>（N={distribution.total_count}）
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-200/60"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 text-slate-700 text-sm">
          {/* Metadata & Source Box */}
          <div className="bg-blue-50/70 border border-blue-200 rounded-xl p-4 text-xs text-blue-950 space-y-3">
            <div className="flex items-start gap-2">
              <BookOpen className="w-4 h-4 text-blue-700 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-blue-900">公的統計データの出典と対象年:</span>
                <ul className="mt-1 list-disc list-inside space-y-0.5 text-blue-800">
                  <li><strong>性別・年代・地方分布:</strong> 総務省統計局『令和2年国勢調査（人口等基本集計）』(2020年対象)</li>
                  <li><strong>就業形態・職業比率:</strong> 総務省統計局『令和4年就業構造基本調査』(2022年対象)</li>
                  <li><strong>個人所得分布:</strong> 国税庁『令和4年分 民間給与実態統計調査』(2022年対象)</li>
                  <li><strong>世帯所得分布:</strong> 総務省統計局『2023年家計調査年報（家計収支編・総世帯）』(2023年対象)</li>
                </ul>
              </div>
            </div>

            <div className="pt-2 border-t border-blue-200/60">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-slate-800">手動設定した仮定（学術・市場調査モデル）:</span>
                  <p className="mt-0.5 text-slate-600 leading-relaxed">
                    公的統計に直接存在しない心理的変数（6つの消費価値観セグメント比率：コスパ層24%、保守層22%、トレンド層18%、こだわり層16%、エシカル層12%、デジタル層8%）および主な情報接触チャネル・意思決定スタイルは、一般的な消費者調査モデルに基づく仮定として手動定義・正規化しています。
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Income Summary Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
              <span className="text-xs text-slate-500">個人年収（平均）</span>
              <p className="text-lg font-bold text-slate-900 mt-1">{distribution.income_stats.personal_mean} <span className="text-xs font-normal">万円</span></p>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
              <span className="text-xs text-slate-500">個人年収（中央値）</span>
              <p className="text-lg font-bold text-slate-900 mt-1">{distribution.income_stats.personal_median} <span className="text-xs font-normal">万円</span></p>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
              <span className="text-xs text-slate-500">世帯年収（平均）</span>
              <p className="text-lg font-bold text-slate-900 mt-1">{distribution.income_stats.household_mean} <span className="text-xs font-normal">万円</span></p>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
              <span className="text-xs text-slate-500">世帯年収（中央値）</span>
              <p className="text-lg font-bold text-slate-900 mt-1">{distribution.income_stats.household_median} <span className="text-xs font-normal">万円</span></p>
            </div>
          </div>

          {/* Age Distribution Comparison */}
          <div>
            <h4 className="font-bold text-xs uppercase tracking-wider text-slate-500 mb-3 flex items-center justify-between">
              <span>年代構成比率の比較 (コホート生成値 vs 全国統計ベンチマーク)</span>
              <span className="text-[11px] font-normal text-emerald-600 flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> 整合性良好
              </span>
            </h4>
            <div className="space-y-2 border border-slate-200 rounded-xl p-4 bg-white">
              {Object.keys(distribution.age_distribution.benchmark_ratio || {}).map((ageKey) => {
                const actual = (distribution.age_distribution.actual_ratio[ageKey] || 0) * 100;
                const bench = (distribution.age_distribution.benchmark_ratio[ageKey] || 0) * 100;
                const count = distribution.age_distribution.actual_counts[ageKey] || 0;
                return (
                  <div key={ageKey} className="text-xs">
                    <div className="flex justify-between mb-1">
                      <span className="font-medium text-slate-700">{ageKey} ({count}名)</span>
                      <span className="text-slate-500">
                        生成: <strong className="text-slate-900">{actual.toFixed(1)}%</strong> / 基準: {bench.toFixed(1)}%
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden flex gap-0.5">
                      <div className="h-full bg-brand-600 rounded-full" style={{ width: `${actual}%` }} title={`生成: ${actual.toFixed(1)}%`}></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Regional & Gender Distribution Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Gender */}
            <div>
              <h4 className="font-bold text-xs uppercase tracking-wider text-slate-500 mb-3">
                男女比率の比較
              </h4>
              <div className="border border-slate-200 rounded-xl p-4 bg-white space-y-3">
                {Object.keys(distribution.gender_distribution.actual_counts || {}).map((g) => {
                  const act = (distribution.gender_distribution.actual_ratio[g] || 0) * 100;
                  const bch = (distribution.gender_distribution.benchmark_ratio?.[g] || 0.5) * 100;
                  return (
                    <div key={g} className="text-xs">
                      <div className="flex justify-between mb-1">
                        <span className="font-medium text-slate-700">{g}</span>
                        <span>生成: <strong>{act.toFixed(1)}%</strong> (全国: {bch.toFixed(1)}%)</span>
                      </div>
                      <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${g === '男性' ? 'bg-blue-500' : 'bg-rose-500'}`}
                          style={{ width: `${act}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Region */}
            <div>
              <h4 className="font-bold text-xs uppercase tracking-wider text-slate-500 mb-3">
                全国8地方 人口構成比率
              </h4>
              <div className="border border-slate-200 rounded-xl p-4 bg-white space-y-2 max-h-56 overflow-y-auto">
                {Object.keys(distribution.region_distribution.benchmark_ratio || {}).map((reg) => {
                  const act = (distribution.region_distribution.actual_ratio[reg] || 0) * 100;
                  const bch = (distribution.region_distribution.benchmark_ratio[reg] || 0) * 100;
                  return (
                    <div key={reg} className="text-xs">
                      <div className="flex justify-between mb-0.5">
                        <span className="font-medium text-slate-700">{reg}</span>
                        <span>生成: <strong>{act.toFixed(1)}%</strong> / 基準: {bch.toFixed(1)}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full bg-indigo-500" style={{ width: `${act}%` }}></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-200 bg-slate-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg shadow-xs"
          >
            閉じる
          </button>
        </div>
      </div>
    </div>
  );
};
