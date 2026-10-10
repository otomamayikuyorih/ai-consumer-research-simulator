import React, { useState } from 'react';
import { Table, CheckCircle2, AlertCircle } from 'lucide-react';

interface CrossTabTableProps {
  crosstabs: Record<string, any>;
  questionId: string;
  questionText: string;
}

export const CrossTabTable: React.FC<CrossTabTableProps> = ({
  crosstabs,
  questionId,
  questionText,
}) => {
  const [breakdown, setBreakdown] = useState<string>('age_group');
  const [showRawCounts, setShowRawCounts] = useState<boolean>(false);

  const breakdownLabels: Record<string, string> = {
    age_group: '年代別 (20代〜70代)',
    gender: '性別 (男性・女性)',
    income_segment: '個人年収帯別',
    region: '全国8地方別',
    values_segment: '消費価値観別',
  };

  const data = crosstabs?.[questionId]?.[breakdown];

  if (!data) {
    return (
      <div className="p-8 text-center text-xs text-slate-400 bg-slate-50 rounded-xl border border-slate-200">
        この設問に対するクロス集計データはまだありません
      </div>
    );
  }

  const isPercentage = !showRawCounts;
  const matrix = isPercentage ? data.percentage : data.raw_counts;

  if (!matrix) return null;

  const rowKeys = Object.keys(matrix);
  if (rowKeys.length === 0) return null;
  const colKeys = Object.keys(matrix[rowKeys[0]] || {});

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">クロス軸:</label>
          <select
            value={breakdown}
            onChange={(e) => setBreakdown(e.target.value)}
            className="text-xs px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white font-medium text-slate-700 shadow-2xs"
          >
            {Object.entries(breakdownLabels).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3">
          {data.stats?.chi2 !== undefined && (
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-slate-500">カイ二乗検定:</span>
              <span className={`font-mono font-semibold ${data.stats.is_significant ? 'text-indigo-600' : 'text-slate-600'}`}>
                χ²={data.stats.chi2}, p={data.stats.p_value}
              </span>
              {data.stats.is_significant && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 font-bold border border-indigo-200">
                  有意差あり (p&lt;0.05)
                </span>
              )}
            </div>
          )}

          <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg text-xs">
            <button
              onClick={() => setShowRawCounts(false)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                !showRawCounts ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              構成比 (%)
            </button>
            <button
              onClick={() => setShowRawCounts(true)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                showRawCounts ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              度数 (実数)
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-slate-200 rounded-xl shadow-xs">
        <table className="w-full text-xs text-left">
          <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
            <tr>
              <th className="p-3 whitespace-nowrap min-w-[120px]">{breakdownLabels[breakdown]}</th>
              {colKeys.map((col) => (
                <th key={col} className="p-3 text-right whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rowKeys.map((rowKey) => (
              <tr key={rowKey} className="hover:bg-slate-50/80 transition-colors">
                <td className="p-3 font-semibold text-slate-800 whitespace-nowrap bg-slate-50/30">
                  {rowKey}
                </td>
                {colKeys.map((colKey) => {
                  const val = matrix[rowKey]?.[colKey] ?? 0;
                  // Heatmap style for percentage
                  const bgIntensity = isPercentage ? Math.min(100, Math.max(0, val)) : 0;
                  const bgColor = isPercentage && bgIntensity > 15 
                    ? `rgba(14, 165, 233, ${bgIntensity / 180})` 
                    : 'transparent';

                  return (
                    <td
                      key={colKey}
                      className="p-3 text-right font-mono transition-colors"
                      style={{ backgroundColor: bgColor }}
                    >
                      {isPercentage ? `${val.toFixed(1)}%` : val}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
