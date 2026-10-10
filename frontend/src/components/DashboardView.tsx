import React from 'react';
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
  Cpu
} from 'lucide-react';
import { Cohort, Survey } from '../types';

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
