import React, { useState } from 'react';
import { 
  FileQuestion, 
  Plus, 
  Trash2, 
  Save, 
  Sparkles, 
  ListChecks, 
  CheckSquare, 
  Sliders, 
  MessageSquare,
  BookOpen
} from 'lucide-react';
import { Cohort, QuestionDef, Survey } from '../types';
import { createSurvey } from '../services/api';

interface SurveyBuilderViewProps {
  cohorts: Cohort[];
  activeCohort: Cohort | null;
  onSurveyCreated: (survey: Survey) => void;
  onNavigateToRunner: (survey: Survey) => void;
}

const TEMPLATES = [
  {
    id: 'product_concept',
    title: '【テンプレート】新商品・新サービス受容性調査',
    description: '新商品の認知、購入意向、魅力度、価格感、改善点を検証する標準マーケティング調査',
    questions: [
      {
        id: 'q1',
        text: '今回提案された商品・サービスに対して、どの程度興味・関心を持ちましたか？',
        type: 'scale5' as const,
        options: ['1: 全く興味がない', '2: あまり興味がない', '3: どちらともいえない', '4: やや興味がある', '5: 非常に興味がある'],
      },
      {
        id: 'q2',
        text: 'この商品が発売された場合、購入または利用してみたいと思いますか？',
        type: 'single' as const,
        options: ['ぜひ購入したい', '機会があれば購入したい', 'あまり購入したくない', '絶対に購入したくない'],
      },
      {
        id: 'q3',
        text: 'この商品・サービスに魅力を感じる点（重視するポイント）をすべて選んでください。',
        type: 'multiple' as const,
        options: ['価格の手頃さ・コスパ', '機能性・利便性の高さ', '時間の節約（タイパ向上）', 'デザイン・世界観', '安心感・信頼性', '健康・環境への配慮'],
      },
      {
        id: 'q4',
        text: '購入をためらう理由や、改善してほしい点があれば率直にお聞かせください。',
        type: 'text' as const,
        options: [],
      },
    ],
  },
  {
    id: 'lifestyle_habits',
    title: '【テンプレート】消費行動・情報収集実態調査',
    description: '生活者の情報源、購買意思決定における重視点、月々の支出傾向を把握する基礎調査',
    questions: [
      {
        id: 'q1',
        text: '新しい商品やサービスを知るきっかけとして、最も影響力の高いメディアは何ですか？',
        type: 'single' as const,
        options: ['SNS（Instagram, X, TikTokなど）', 'YouTubeや動画サイト', 'テレビ番組やCM', 'Web検索・口コミ比較サイト', '知人・家族からの紹介'],
      },
      {
        id: 'q2',
        text: '商品を購入する際、事前にどのような情報を調べますか？（複数選択可）',
        type: 'multiple' as const,
        options: ['実際の購入者による低評価レビュー', '価格比較サイトでの最安値', '公式の機能スペックや成分表', 'SNSでのインフルエンサーの着用・使用感', '実店舗での現物確認'],
      },
      {
        id: 'q3',
        text: '直近1年間で、あなたの消費傾向は「節約志向」と「体験・プチ贅沢志向」のどちらに寄っていますか？',
        type: 'scale5' as const,
        options: ['1: 徹底した節約志向', '2: やや節約志向', '3: どちらともいえない', '4: やや体験・贅沢志向', '5: 強い体験・自己投資志向'],
      },
      {
        id: 'q4',
        text: '日々の暮らしの中で「これだけは妥協せずお金をかけたい」と考えているこだわりは何ですか？',
        type: 'text' as const,
        options: [],
      },
    ],
  },
];

export const SurveyBuilderView: React.FC<SurveyBuilderViewProps> = ({
  cohorts,
  activeCohort,
  onSurveyCreated,
  onNavigateToRunner,
}) => {
  const [selectedCohortId, setSelectedCohortId] = useState<string>(activeCohort?.id || (cohorts[0]?.id || ''));
  const [title, setTitle] = useState('新商品受容性・消費実態調査');
  const [description, setDescription] = useState('仮想生活者コホートによるアンケートシミュレーション');
  const [questions, setQuestions] = useState<QuestionDef[]>(TEMPLATES[0].questions);
  const [isSaving, setIsSaving] = useState(false);

  const applyTemplate = (tmpl: typeof TEMPLATES[0]) => {
    setTitle(tmpl.title.replace('【テンプレート】', ''));
    setDescription(tmpl.description);
    setQuestions(JSON.parse(JSON.stringify(tmpl.questions)));
  };

  const handleAddQuestion = (type: QuestionDef['type']) => {
    const newId = `q${questions.length + 1}`;
    let defaultOptions: string[] = [];
    if (type === 'single' || type === 'multiple') {
      defaultOptions = ['選択肢1', '選択肢2', '選択肢3'];
    }
    const newQ: QuestionDef = {
      id: newId,
      text: '新しい設問文を入力してください',
      type,
      options: defaultOptions,
      required: true,
    };
    setQuestions([...questions, newQ]);
  };

  const handleUpdateQuestionText = (index: number, text: string) => {
    const updated = [...questions];
    updated[index].text = text;
    setQuestions(updated);
  };

  const handleUpdateOptions = (index: number, optionsStr: string) => {
    const updated = [...questions];
    updated[index].options = optionsStr.split('\n').filter((opt) => opt.trim() !== '');
    setQuestions(updated);
  };

  const handleDeleteQuestion = (index: number) => {
    const updated = questions.filter((_, i) => i !== index);
    setQuestions(updated);
  };

  const handleSaveSurvey = async () => {
    if (!selectedCohortId) {
      alert('調査対象のコホートを選択してください');
      return;
    }
    if (questions.length === 0) {
      alert('設問を最低1問追加してください');
      return;
    }

    setIsSaving(true);
    try {
      const created = await createSurvey({
        cohort_id: selectedCohortId,
        title,
        description,
        questions,
      });
      onSurveyCreated(created);
      onNavigateToRunner(created);
    } catch (err) {
      alert('アンケート作成に失敗しました: ' + err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8 pb-12 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <FileQuestion className="w-6 h-6 text-purple-600" />
          アンケート調査の作成
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          単一選択・複数選択・5段階評価・自由記述を自由に組み合わせ、コホートに対する質問票を設計します
        </p>
      </div>

      {/* Template Quick Selection */}
      <div className="bg-purple-50/60 border border-purple-200 rounded-2xl p-5 shadow-xs">
        <h3 className="text-xs font-bold text-purple-900 mb-2 flex items-center gap-1.5">
          <BookOpen className="w-4 h-4 text-purple-700" />
          マーケティング調査テンプレートから即時設定
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
          {TEMPLATES.map((tmpl) => (
            <div
              key={tmpl.id}
              onClick={() => applyTemplate(tmpl)}
              className="bg-white p-3.5 rounded-xl border border-purple-200 hover:border-purple-400 hover:shadow-xs transition-all cursor-pointer group"
            >
              <h4 className="font-bold text-xs text-slate-800 group-hover:text-purple-700 transition-colors">
                {tmpl.title}
              </h4>
              <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">{tmpl.description}</p>
              <span className="text-[10px] text-purple-600 font-medium inline-block mt-2">
                この設問を読み込む ({tmpl.questions.length}問) &rarr;
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Main Survey Meta Settings */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-700 mb-1">アンケートタイトル</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500"
              placeholder="例: 新商品受容性調査"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">調査対象コホート</label>
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

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">調査の目的・説明（任意）</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500"
            placeholder="ペルソナへの前提説明や調査背景"
          />
        </div>
      </div>

      {/* Questions List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <span>設問リスト ({questions.length}問)</span>
          </h3>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => handleAddQuestion('single')}
              className="px-2.5 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 shadow-xs"
            >
              <ListChecks className="w-3.5 h-3.5 text-blue-600" />
              単一選択
            </button>
            <button
              onClick={() => handleAddQuestion('multiple')}
              className="px-2.5 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 shadow-xs"
            >
              <CheckSquare className="w-3.5 h-3.5 text-emerald-600" />
              複数選択
            </button>
            <button
              onClick={() => handleAddQuestion('scale5')}
              className="px-2.5 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 shadow-xs"
            >
              <Sliders className="w-3.5 h-3.5 text-amber-600" />
              5段階尺度
            </button>
            <button
              onClick={() => handleAddQuestion('text')}
              className="px-2.5 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1 shadow-xs"
            >
              <MessageSquare className="w-3.5 h-3.5 text-purple-600" />
              自由記述
            </button>
          </div>
        </div>

        {questions.map((q, idx) => {
          const typeLabels: Record<string, { label: string; color: string }> = {
            single: { label: '単一選択', color: 'bg-blue-50 text-blue-700 border-blue-200' },
            multiple: { label: '複数選択', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
            scale5: { label: '5段階評価 (1-5)', color: 'bg-amber-50 text-amber-700 border-amber-200' },
            text: { label: '自由記述', color: 'bg-purple-50 text-purple-700 border-purple-200' },
          };
          const badge = typeLabels[q.type];

          return (
            <div key={idx} className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3 relative group">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-xs text-slate-400 font-mono">Q{idx + 1}</span>
                  <span className={`text-[11px] px-2 py-0.5 rounded-full border font-semibold ${badge.color}`}>
                    {badge.label}
                  </span>
                </div>
                <button
                  onClick={() => handleDeleteQuestion(idx)}
                  className="text-slate-400 hover:text-rose-600 p-1 rounded transition-colors"
                  title="設問を削除"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Question Text */}
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 mb-1">設問文</label>
                <input
                  type="text"
                  value={q.text}
                  onChange={(e) => handleUpdateQuestionText(idx, e.target.value)}
                  className="w-full text-xs font-medium px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500"
                />
              </div>

              {/* Options Editor for single/multiple */}
              {(q.type === 'single' || q.type === 'multiple') && (
                <div>
                  <label className="block text-[11px] font-semibold text-slate-500 mb-1">
                    選択肢（1行に1項目）
                  </label>
                  <textarea
                    rows={3}
                    value={q.options.join('\n')}
                    onChange={(e) => handleUpdateOptions(idx, e.target.value)}
                    className="w-full text-xs font-mono px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              )}

              {q.type === 'scale5' && (
                <div className="text-[11px] text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-100 flex items-center justify-between">
                  <span>1: 全くそう思わない / 不満</span>
                  <span className="text-slate-400">↔</span>
                  <span>3: どちらともいえない</span>
                  <span className="text-slate-400">↔</span>
                  <span>5: 非常にそう思う / 満足</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Save & Run Action Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-200">
        <span className="text-xs text-slate-500">
          合計 {questions.length} 問が対象コホートに提示されます
        </span>
        <button
          onClick={handleSaveSurvey}
          disabled={isSaving}
          className="px-6 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs rounded-xl shadow-md shadow-brand-600/20 flex items-center gap-2 transition-all disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          アンケートを保存して調査実行へ進む &rarr;
        </button>
      </div>
    </div>
  );
};
