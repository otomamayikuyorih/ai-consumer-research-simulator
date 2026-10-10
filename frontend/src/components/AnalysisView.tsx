import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Download, 
  Table, 
  Compass, 
  FileText, 
  Sparkles, 
  CheckCircle, 
  Loader2,
  TrendingUp,
  MessageSquare,
  ThumbsUp,
  Sliders,
  Filter
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell 
} from 'recharts';
import { Survey, SurveyAnalysis } from '../types';
import { fetchSurveyAnalysis, getSurveyExportCsvUrl } from '../services/api';
import { CrossTabTable } from './CrossTabTable';
import { MultivariateSection } from './MultivariateSection';

interface AnalysisViewProps {
  surveys: Survey[];
  activeSurvey: Survey | null;
  onSelectSurvey: (survey: Survey) => void;
}

const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#64748b'];

export const AnalysisView: React.FC<AnalysisViewProps> = ({
  surveys,
  activeSurvey,
  onSelectSurvey,
}) => {
  const [analysis, setAnalysis] = useState<SurveyAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [subTab, setSubTab] = useState<'summary' | 'crosstab' | 'multivariate' | 'qualitative'>('summary');

  useEffect(() => {
    if (activeSurvey) {
      loadAnalysis(activeSurvey.id);
    }
  }, [activeSurvey]);

  const loadAnalysis = async (surveyId: string) => {
    setIsLoading(true);
    try {
      const data = await fetchSurveyAnalysis(surveyId);
      setAnalysis(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!activeSurvey) {
    return (
      <div className="text-center py-24 bg-white rounded-2xl border border-slate-200">
        <BarChart3 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <h3 className="font-bold text-slate-700 text-sm">アンケートが選択されていません</h3>
        <p className="text-xs text-slate-400 mt-1">アンケートを作成・実行した後に解析結果が表示されます</p>
      </div>
    );
  }

  const questions = activeSurvey.questions || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header & Survey Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-brand-600" />
            アンケート結果解析・ダッシュボード
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            調査名: <span className="font-semibold text-slate-800">{activeSurvey.title}</span> (回収回答数: {analysis?.total_respondents || activeSurvey.response_count}件)
          </p>
        </div>

        <div className="flex items-center gap-2">
          {surveys.length > 1 && (
            <select
              value={activeSurvey.id}
              onChange={(e) => {
                const found = surveys.find((s) => s.id === e.target.value);
                if (found) onSelectSurvey(found);
              }}
              className="text-xs font-semibold px-3 py-2 border border-slate-300 rounded-lg bg-white"
            >
              {surveys.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title} ({s.response_count}件)
                </option>
              ))}
            </select>
          )}

          <a
            href={getSurveyExportCsvUrl(activeSurvey.id)}
            download
            className="px-3.5 py-2 rounded-lg bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-xs flex items-center gap-1.5 shadow-xs transition-all"
          >
            <Download className="w-3.5 h-3.5 text-brand-600" />
            CSVダウンロード
          </a>
        </div>
      </div>

      {/* Sub Tabs */}
      <div className="flex space-x-1 border-b border-slate-200">
        {[
          { id: 'summary', label: '単純集計・グラフ', icon: BarChart3 },
          { id: 'crosstab', label: 'クロス集計表', icon: Table },
          { id: 'multivariate', label: '多変量解析 (PCA/クラスター)', icon: Compass },
          { id: 'qualitative', label: '定性AIインサイト・要約', icon: Sparkles },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = subTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setSubTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all ${
                isActive
                  ? 'border-brand-600 text-brand-700 bg-brand-50/50'
                  : 'border-transparent text-slate-500 hover:text-slate-900 hover:border-slate-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Loading indicator */}
      {isLoading ? (
        <div className="p-16 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
          <Loader2 className="w-5 h-5 animate-spin text-brand-600" />
          アンケート解析データを集計中...
        </div>
      ) : !analysis || analysis.total_respondents === 0 ? (
        <div className="p-16 text-center bg-white rounded-2xl border border-slate-200 text-slate-400 text-xs">
          まだ回答データが存在しません。「調査シミュレーション」タブでシミュレーションを実行してください。
        </div>
      ) : (
        <div>
          {/* TAB 1: 単純集計 */}
          {subTab === 'summary' && (
            <div className="space-y-6">
              {questions.map((q, idx) => {
                const qSummary = analysis.questions_summary?.[q.id];
                if (!qSummary) return null;

                // Format data for chart
                let chartData: any[] = [];
                if (q.type === 'single' || q.type === 'multiple') {
                  const counts = qSummary.counts || {};
                  chartData = Object.entries(counts).map(([name, count]) => ({
                    name,
                    count,
                    percentage: ((count as number) / (qSummary.total || 1)) * 100,
                  }));
                } else if (q.type === 'scale5') {
                  const freq = qSummary.freq || {};
                  chartData = [1, 2, 3, 4, 5].map((val) => ({
                    name: `${val}点`,
                    count: freq[String(val)] || 0,
                    percentage: ((freq[String(val)] || 0) / (qSummary.total || 1)) * 100,
                  }));
                }

                return (
                  <div key={q.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-brand-600 font-mono">Q{idx + 1}</span>
                          <h4 className="font-bold text-sm text-slate-900">{q.text}</h4>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">
                          形式: {q.type === 'single' ? '単一選択' : q.type === 'multiple' ? '複数選択' : q.type === 'scale5' ? '5段階評価' : '自由記述'}
                        </p>
                      </div>

                      {q.type === 'scale5' && (
                        <div className="flex items-center gap-4 bg-slate-50 px-4 py-2 rounded-xl border border-slate-200 text-xs">
                          <div>
                            <span className="text-slate-400 block text-[10px]">平均スコア</span>
                            <span className="font-bold text-slate-900 text-base">{qSummary.mean}</span>
                            <span className="text-slate-400 text-[10px]"> / 5.0</span>
                          </div>
                          <div className="border-l border-slate-200 pl-4">
                            <span className="text-slate-400 block text-[10px]">Top-2 Box (4点+5点)</span>
                            <span className="font-bold text-emerald-600 text-base">
                              {((qSummary.top2_box_ratio || 0) * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Chart & Tables */}
                    {(q.type === 'single' || q.type === 'multiple' || q.type === 'scale5') && (
                      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center pt-2">
                        {/* Bar Chart */}
                        <div className="lg:col-span-8 h-64 w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 25 }}>
                              <XAxis 
                                dataKey="name" 
                                tick={{ fontSize: 10 }} 
                                interval={0} 
                                angle={-15} 
                                textAnchor="end"
                              />
                              <YAxis tick={{ fontSize: 10 }} />
                              <Tooltip 
                                formatter={(value: any) => [`${value}件`, '回答数']}
                              />
                              <Bar dataKey="count" fill="#0267c7" radius={[4, 4, 0, 0]} />
                            </BarChart>
                          </ResponsiveContainer>
                        </div>

                        {/* Breakdown Table */}
                        <div className="lg:col-span-4 bg-slate-50 rounded-xl p-3 border border-slate-200 text-xs">
                          <table className="w-full text-left">
                            <thead>
                              <tr className="border-b border-slate-200 text-slate-500 font-semibold">
                                <th className="pb-1.5">項目</th>
                                <th className="pb-1.5 text-right">回答数</th>
                                <th className="pb-1.5 text-right">割合</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                              {chartData.map((d, i) => (
                                <tr key={i} className="hover:bg-white/50">
                                  <td className="py-1 font-medium text-slate-700 truncate max-w-[120px]" title={d.name}>
                                    {d.name}
                                  </td>
                                  <td className="py-1 text-right font-mono">{d.count}</td>
                                  <td className="py-1 text-right font-mono font-semibold text-brand-700">
                                    {d.percentage.toFixed(1)}%
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Qualitative Sample Comments */}
                    {q.type === 'text' && (
                      <div className="space-y-2 pt-2">
                        <span className="text-xs font-semibold text-slate-700">ペルソナからの回答コメント（抜粋）:</span>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-72 overflow-y-auto">
                          {qSummary.sample_comments?.map((comment: string, cIdx: number) => (
                            <div key={cIdx} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 leading-relaxed">
                              "{comment}"
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* TAB 2: クロス集計 */}
          {subTab === 'crosstab' && (
            <div className="space-y-8">
              {questions
                .filter((q) => q.type === 'single' || q.type === 'scale5')
                .map((q) => (
                  <div key={q.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
                    <div>
                      <span className="font-bold text-xs text-brand-600 font-mono">{q.id.toUpperCase()}</span>
                      <h4 className="font-bold text-sm text-slate-900 mt-0.5">{q.text}</h4>
                    </div>
                    <CrossTabTable
                      crosstabs={analysis.crosstabs}
                      questionId={q.id}
                      questionText={q.text}
                    />
                  </div>
                ))}
            </div>
          )}

          {/* TAB 3: 多変量解析 */}
          {subTab === 'multivariate' && (
            <MultivariateSection multivariateData={analysis.multivariate} />
          )}

          {/* TAB 4: 定性AIインサイト・要約 */}
          {subTab === 'qualitative' && (
            <div className="space-y-6">
              {Object.entries(analysis.text_summaries || {}).map(([qid, textSum]) => {
                const q = questions.find((item) => item.id === qid);
                const pos = (textSum.sentiment_ratio?.positive || 0) * 100;
                const neu = (textSum.sentiment_ratio?.neutral || 0) * 100;
                const neg = (textSum.sentiment_ratio?.negative || 0) * 100;

                return (
                  <div key={qid} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-5">
                    <div>
                      <span className="font-bold text-xs text-purple-600 font-mono">{qid.toUpperCase()}</span>
                      <h4 className="font-bold text-base text-slate-900 mt-0.5">{q?.text}</h4>
                    </div>

                    {/* AI Summary Box */}
                    <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-xl p-5 text-slate-800 text-xs sm:text-sm leading-relaxed">
                      <div className="flex items-center gap-2 text-purple-900 font-bold mb-2">
                        <Sparkles className="w-4 h-4 text-purple-600" />
                        Gemini AIによる定性エグゼクティブ・サマリー
                      </div>
                      <p>{textSum.summary}</p>
                    </div>

                    {/* Sentiment Ratio Bar */}
                    <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/50 space-y-2">
                      <span className="text-xs font-bold text-slate-700">感情・受容トーン比率</span>
                      <div className="h-3 w-full bg-slate-200 rounded-full overflow-hidden flex">
                        <div className="h-full bg-emerald-500" style={{ width: `${pos}%` }} title={`ポジティブ: ${pos.toFixed(1)}%`}></div>
                        <div className="h-full bg-slate-400" style={{ width: `${neu}%` }} title={`中立: ${neu.toFixed(1)}%`}></div>
                        <div className="h-full bg-rose-500" style={{ width: `${neg}%` }} title={`ネガティブ/慎重: ${neg.toFixed(1)}%`}></div>
                      </div>
                      <div className="flex justify-between text-[11px] text-slate-600 pt-1">
                        <span className="text-emerald-700 font-medium">● 好意的・受容的: {pos.toFixed(1)}%</span>
                        <span className="text-slate-600">● 中立・条件付き: {neu.toFixed(1)}%</span>
                        <span className="text-rose-700 font-medium">● 慎重・懸念: {neg.toFixed(1)}%</span>
                      </div>
                    </div>

                    {/* Key Themes List */}
                    <div>
                      <span className="text-xs font-bold text-slate-700 block mb-2">抽出された主要な発言テーマ</span>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        {textSum.key_themes?.map((th, tIdx) => (
                          <div key={tIdx} className="bg-white p-3 rounded-lg border border-slate-200 text-xs shadow-2xs">
                            <span className="text-[10px] text-slate-400 font-bold block mb-1">THEME {tIdx + 1}</span>
                            <span className="font-semibold text-slate-800">{th.theme}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
