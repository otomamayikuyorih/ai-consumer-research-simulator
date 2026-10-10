import React from 'react';
import { 
  ScatterChart, 
  Scatter, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ZAxis,
  Cell
} from 'recharts';
import { Sparkles, Layers, Compass, Info } from 'lucide-react';

interface MultivariateSectionProps {
  multivariateData: any;
}

const CLUSTER_COLORS = ['#3b82f6', '#ec4899', '#10b981', '#f59e0b', '#8b5cf6'];

export const MultivariateSection: React.FC<MultivariateSectionProps> = ({ multivariateData }) => {
  if (!multivariateData || multivariateData.error) {
    return (
      <div className="p-8 text-center text-xs text-slate-400 bg-slate-50 rounded-xl border border-slate-200">
        多変量解析を実行するには、回答データが最低4件以上必要です。
      </div>
    );
  }

  const { pca, clustering } = multivariateData;
  const points = pca?.points || [];
  const expVar = pca?.explained_variance_ratio || [0, 0];
  const totalExp = pca?.total_variance_explained || 0;

  const clusterDist = clustering?.cluster_distribution || {};
  const clusterNames = clustering?.cluster_names || {};

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-xl border border-slate-200 text-xs space-y-1 z-50">
          <p className="font-bold text-slate-900">{data.name} ({data.persona_code})</p>
          <p className="text-slate-600">{data.gender}・{data.age}歳 / 年収 {data.income}万円</p>
          <p className="text-brand-600 font-semibold">{data.values_segment}</p>
          <div className="pt-1 mt-1 border-t border-slate-100 text-[10px] text-slate-400">
            所属: {data.cluster_name} (X: {data.x}, Y: {data.y})
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50/60 border border-blue-200 rounded-xl p-4">
          <span className="text-xs font-bold text-blue-900 flex items-center gap-1.5">
            <Compass className="w-4 h-4 text-blue-700" />
            主成分分析 (PCA) 寄与率
          </span>
          <p className="text-2xl font-bold text-blue-950 mt-1">
            {(totalExp * 100).toFixed(1)}% <span className="text-xs font-normal text-blue-800">累積説明分散</span>
          </p>
          <p className="text-[11px] text-blue-700 mt-1">
            第1主成分: {(expVar[0] * 100).toFixed(1)}% / 第2主成分: {(expVar[1] * 100).toFixed(1)}%
          </p>
        </div>

        <div className="bg-purple-50/60 border border-purple-200 rounded-xl p-4 md:col-span-2">
          <span className="text-xs font-bold text-purple-900 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-purple-700" />
            自動セグメンテーション（K-Means クラスタリング）
          </span>
          <div className="grid grid-cols-3 gap-2 mt-2">
            {Object.keys(clusterNames).map((clIdxStr, i) => {
              const clIdx = Number(clIdxStr);
              const count = clusterDist[clIdxStr] || clusterDist[clIdx] || 0;
              return (
                <div key={clIdx} className="bg-white/80 p-2.5 rounded-lg border border-purple-100 text-xs">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }}></span>
                    <span className="font-bold text-slate-800 truncate">{clusterNames[clIdx]}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">
                    構成比: <strong className="text-purple-700">{count}名</strong>
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 2D PCA Scatter Plot */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="font-bold text-sm text-slate-900">消費者の知覚・ポジショニングマップ（2次元PCA）</h4>
            <p className="text-xs text-slate-500 mt-0.5">
              アンケートの回答パターンおよび属性類似度に基づいて生活者を2次元空間上に写像
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            {Object.keys(clusterNames).map((clIdxStr, i) => (
              <div key={clIdxStr} className="flex items-center gap-1">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }}></span>
                <span className="text-slate-600">{clusterNames[Number(clIdxStr)]}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="h-96 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis 
                type="number" 
                dataKey="x" 
                name="第1主成分 (PC1)" 
                tick={{ fontSize: 11 }}
                stroke="#94a3b8" 
              />
              <YAxis 
                type="number" 
                dataKey="y" 
                name="第2主成分 (PC2)" 
                tick={{ fontSize: 11 }}
                stroke="#94a3b8" 
              />
              <ZAxis range={[60, 60]} />
              <Tooltip content={<CustomTooltip />} />
              <Scatter name="生活者ペルソナ" data={points}>
                {points.map((entry: any, index: number) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={CLUSTER_COLORS[entry.cluster % CLUSTER_COLORS.length]} 
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-3 bg-slate-50 p-3 rounded-lg border border-slate-200 text-xs text-slate-600 flex items-start gap-2">
          <Info className="w-4 h-4 text-brand-600 flex-shrink-0 mt-0.5" />
          <p>
            各点は個々の仮想生活者を表します。距離が近い生活者ほど設問に対する回答傾向や消費価値観が酷似しています。各クラスターにカーソルを合わせると個々のペルソナ属性を確認できます。
          </p>
        </div>
      </div>
    </div>
  );
};
