import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Sparkles, 
  BarChart2, 
  Search, 
  Filter, 
  MessageSquare, 
  Check, 
  Loader2,
  ChevronRight,
  ShieldCheck,
  Compass,
  MapPin,
  Briefcase,
  Wallet,
  GraduationCap,
  Heart,
  Quote,
  FileText,
  UploadCloud,
  Trash2,
  AlertCircle,
  Lock,
  Layers
} from 'lucide-react';
import { Cohort, Persona, InterviewDataset } from '../types';
import { 
  createCohort, 
  fetchCohortDetail, 
  fetchCohortPersonas,
  fetchInterviewDatasets,
  ingestInterviewDataset,
  deleteInterviewDataset 
} from '../services/api';
import { PersonaValidationModal } from './PersonaValidationModal';

interface PersonaGeneratorViewProps {
  cohorts: Cohort[];
  activeCohort: Cohort | null;
  onCohortCreated: (newCohort: Cohort) => void;
  onSelectCohort: (cohort: Cohort) => void;
  onStartInterviewWithPersona: (persona: Persona) => void;
}

export const PersonaGeneratorView: React.FC<PersonaGeneratorViewProps> = ({
  cohorts,
  activeCohort,
  onCohortCreated,
  onSelectCohort,
  onStartInterviewWithPersona,
}) => {
  // Form State
  const [name, setName] = useState('日本全国・代表サンプル（N=100）');
  const [targetCount, setTargetCount] = useState<number>(100);
  const [preset, setPreset] = useState('general_national');
  const [seed, setSeed] = useState<number>(42);
  const [generationMode, setGenerationMode] = useState<'mode_a' | 'mode_b' | 'mode_c'>('mode_b');
  const [interviewDatasets, setInterviewDatasets] = useState<InterviewDataset[]>([]);
  const [selectedInterviewDatasetId, setSelectedInterviewDatasetId] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);

  // Ingestion Modal State
  const [showIngestModal, setShowIngestModal] = useState(false);
  const [newDatasetName, setNewDatasetName] = useState('定性インタビュー記録 (2026年3月実施)');
  const [newDatasetContent, setNewDatasetContent] = useState('');
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);

  // Personas explorer state
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [search, setSearch] = useState('');
  const [genderFilter, setGenderFilter] = useState('');
  const [ageFilter, setAgeFilter] = useState('');
  const [valuesFilter, setValuesFilter] = useState('');
  const [selectedPersona, setSelectedPersona] = useState<Persona | null>(null);
  const [isLoadingPersonas, setIsLoadingPersonas] = useState(false);

  // Validation modal state
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [cohortDetail, setCohortDetail] = useState<Cohort | null>(null);

  useEffect(() => {
    loadInterviewDatasets();
  }, []);

  // Load personas when activeCohort changes or filters change
  useEffect(() => {
    if (activeCohort) {
      loadPersonas();
      loadDetail();
    }
  }, [activeCohort, genderFilter, ageFilter, valuesFilter]);

  const loadInterviewDatasets = async () => {
    try {
      const list = await fetchInterviewDatasets();
      setInterviewDatasets(list);
      if (list.length > 0 && !selectedInterviewDatasetId) {
        setSelectedInterviewDatasetId(list[0].id);
      }
    } catch (err) {
      console.error('Failed to load interview datasets:', err);
    }
  };

  const loadPersonas = async () => {
    if (!activeCohort) return;
    setIsLoadingPersonas(true);
    try {
      const res = await fetchCohortPersonas(activeCohort.id, {
        gender: genderFilter || undefined,
        age_group: ageFilter || undefined,
        values_segment: valuesFilter || undefined,
        search: search || undefined,
        limit: 100,
      });
      const list = res.personas || res.items || [];
      setPersonas(list);
      setTotalCount(res.total);
      if (list.length > 0 && !selectedPersona) {
        setSelectedPersona(list[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoadingPersonas(false);
    }
  };

  const loadDetail = async () => {
    if (!activeCohort) return;
    try {
      const detail = await fetchCohortDetail(activeCohort.id);
      setCohortDetail(detail);
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (generationMode === 'mode_c' && !selectedInterviewDatasetId) {
      alert('Mode C（実測インタビュー接地）を選択した場合は、根拠とするインタビューデータセットを選択してください');
      return;
    }

    setIsGenerating(true);
    try {
      const newCohort = await createCohort({
        name,
        target_count: targetCount,
        seed,
        preset,
        generation_mode: generationMode,
        interview_dataset_id: generationMode === 'mode_c' ? selectedInterviewDatasetId : undefined,
      });
      onCohortCreated(newCohort);
      onSelectCohort(newCohort);
    } catch (err) {
      alert('コホート生成に失敗しました: ' + err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleIngestDataset = async () => {
    if (!consentConfirmed) {
      alert('個人情報保護および本人の同意確認にチェックを入れてください。');
      return;
    }
    if (!newDatasetContent.trim()) {
      alert('インタビュー記録の本文を入力してください。');
      return;
    }

    setIsIngesting(true);
    try {
      const created = await ingestInterviewDataset({
        name: newDatasetName,
        source_type: 'text',
        raw_content: newDatasetContent,
        consent_confirmed: true,
        is_demo: false,
      });
      alert(`インタビューデータセット『${created.name}』を登録・抽出しました（参加者数: ${created.participant_count}名）`);
      await loadInterviewDatasets();
      setSelectedInterviewDatasetId(created.id);
      setShowIngestModal(false);
      setNewDatasetContent('');
    } catch (err: any) {
      alert('インタビュー取り込みに失敗しました: ' + err.message);
    } finally {
      setIsIngesting(false);
    }
  };

  const handleDeleteDataset = async (id: string) => {
    if (!confirm('同意撤回またはデータ削除を実行しますか？関連するペルソナ情報も削除されます。')) return;
    try {
      await deleteInterviewDataset(id);
      await loadInterviewDatasets();
    } catch (err: any) {
      alert('削除に失敗しました: ' + err.message);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <Users className="w-6 h-6 text-brand-600" />
              仮想消費者（ペルソナコホート）生成・検証
            </h2>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
              3-Mode Generation (AI4PB 準拠)
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            日本の公的統計データ（国勢調査・就業構造・家計調査）および実測定性インタビュー記録に基づき仮想消費者を生成します
          </p>
        </div>

        {/* Existing Cohort Switcher */}
        {cohorts.length > 0 && (
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500 font-medium">現在のコホート:</label>
            <select
              value={activeCohort?.id || ''}
              onChange={(e) => {
                const found = cohorts.find((c) => c.id === e.target.value);
                if (found) onSelectCohort(found);
              }}
              className="bg-white border border-slate-300 text-xs font-semibold rounded-lg px-3 py-2 shadow-xs focus:ring-2 focus:ring-brand-500 text-slate-800"
            >
              {cohorts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.persona_count}人) [{c.generation_mode === 'mode_a' ? 'Mode A' : c.generation_mode === 'mode_c' ? 'Mode C (接地)' : 'Mode B'}]
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Cohort Creation Form Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <h3 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-brand-600" />
          新規コホートの生成設定
        </h3>
        
        <form onSubmit={handleGenerate} className="space-y-6">
          {/* Mode Selection 3 Cards */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-2">
              ペルソナ生成モード選択（Stanford AI4PB 研究フレームワーク準拠）
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {/* Mode A */}
              <div 
                onClick={() => setGenerationMode('mode_a')}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  generationMode === 'mode_a'
                    ? 'border-slate-800 bg-slate-50 ring-2 ring-slate-800/10'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-slate-900">Mode A: 人口統計ペルソナ</span>
                  {generationMode === 'mode_a' && <Check className="w-4 h-4 text-slate-900" />}
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">
                  年齢・性別・地域・年収・職業など<strong>客観的属性のみ</strong>でペルソナを定義。属性による回答傾向を純粋比較できます。
                </p>
                <span className="inline-block mt-2 text-[10px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                  Demographic Only
                </span>
              </div>

              {/* Mode B */}
              <div 
                onClick={() => setGenerationMode('mode_b')}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  generationMode === 'mode_b'
                    ? 'border-indigo-600 bg-indigo-50/40 ring-2 ring-indigo-600/10'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-indigo-950">Mode B: 合成生活史リッチ</span>
                  {generationMode === 'mode_b' && <Check className="w-4 h-4 text-indigo-600" />}
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  人口統計属性に加え、統計的相関に基づく<strong>架空の生活史ナラティブ・過去の購買経験</strong>をアルゴリズム生成して付与。
                </p>
                <span className="inline-block mt-2 text-[10px] font-semibold text-indigo-700 bg-indigo-100/70 px-2 py-0.5 rounded">
                  Synthetic Rich Persona (標準)
                </span>
              </div>

              {/* Mode C */}
              <div 
                onClick={() => setGenerationMode('mode_c')}
                className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                  generationMode === 'mode_c'
                    ? 'border-emerald-600 bg-emerald-50/40 ring-2 ring-emerald-600/10'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-emerald-950">Mode C: 実測インタビュー接地</span>
                  {generationMode === 'mode_c' && <Check className="w-4 h-4 text-emerald-600" />}
                </div>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  <strong>実際のインタビュー記録と元発言（Verbatim Quotes）</strong>を根拠としてペルソナを構築。要約損失を最小化（Stanford AI4PB）。
                </p>
                <span className="inline-block mt-2 text-[10px] font-semibold text-emerald-700 bg-emerald-100/70 px-2 py-0.5 rounded">
                  Interview-Grounded
                </span>
              </div>
            </div>
          </div>

          {/* If Mode C is selected: Dataset picker & Ingest */}
          {generationMode === 'mode_c' && (
            <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/20 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <span className="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                  <Quote className="w-4 h-4 text-emerald-600" />
                  接地するインタビューデータセットの選択
                </span>
                <button
                  type="button"
                  onClick={() => setShowIngestModal(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs"
                >
                  <UploadCloud className="w-3.5 h-3.5" />
                  新しいインタビューを登録
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {interviewDatasets.map((ds) => (
                  <div 
                    key={ds.id}
                    onClick={() => setSelectedInterviewDatasetId(ds.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all flex items-start justify-between ${
                      selectedInterviewDatasetId === ds.id
                        ? 'border-emerald-600 bg-white ring-2 ring-emerald-500/20'
                        : 'border-slate-200 bg-white/70 hover:bg-white'
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-800">{ds.name}</span>
                        {ds.is_demo ? (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-amber-100 text-amber-800">デモ</span>
                        ) : (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 flex items-center gap-0.5">
                            <Lock className="w-2.5 h-2.5" /> 同意確認済
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-slate-500">対象被験者: {ds.participant_count} 名</span>
                    </div>

                    {!ds.is_demo && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteDataset(ds.id);
                        }}
                        className="text-slate-400 hover:text-rose-600 p-1"
                        title="同意撤回・削除"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Form Basic Fields */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Cohort Name */}
            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-slate-700 mb-1">コホート名</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500"
                placeholder="例: 全国20〜60代 代表サンプル"
              />
            </div>

            {/* Target Sample Size */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">サンプル規模 (N)</label>
              <select
                value={targetCount}
                onChange={(e) => setTargetCount(Number(e.target.value))}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 bg-white"
              >
                <option value={20}>20人 (テスト用・最速)</option>
                <option value={100}>100人 (推奨・高速)</option>
                <option value={300}>300人 (中規模)</option>
                <option value={500}>500人 (大規模)</option>
                <option value={1000}>1,000人 (本格調査)</option>
              </select>
            </div>

            {/* Random Seed */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">再現性シード値</label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          {/* Preset Selection Cards */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-2">生成セグメント・プリセット</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                {
                  id: 'general_national',
                  title: '全国一般代表サンプル',
                  desc: '国勢調査の年齢ピラミッド・8地方人口比・男女比に完全準拠',
                },
                {
                  id: 'young_digital',
                  title: '20-30代 デジタルネイティブ',
                  desc: 'SNS情報収集・タイパ志向・新技術や体験消費を好む若年層',
                },
                {
                  id: 'working_parents',
                  title: '子育て・共働きファミリー層',
                  desc: '30〜40代中心、時短・教育・生活インフラへの関心が高い世帯',
                },
                {
                  id: 'senior_silver',
                  title: '60代以上 シニア・アクティブ層',
                  desc: '退職・再雇用、健康長寿・安心感・伝統メディア接触の多い層',
                },
              ].map((p) => (
                <div
                  key={p.id}
                  onClick={() => setPreset(p.id)}
                  className={`p-3 rounded-xl border cursor-pointer transition-all ${
                    preset === p.id
                      ? 'border-brand-500 bg-brand-50/60 ring-2 ring-brand-500/20'
                      : 'border-slate-200 bg-slate-50/50 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-slate-800">{p.title}</span>
                    {preset === p.id && <Check className="w-3.5 h-3.5 text-brand-600" />}
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed">{p.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-slate-500 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              日本の公的統計データに基づく相関ルール適用
            </span>
            <button
              type="submit"
              disabled={isGenerating}
              className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-xs flex items-center gap-2 shadow-xs transition-all disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  ペルソナ群を合成中...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  仮想消費者コホートを生成する
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Active Cohort Personas Explorer */}
      {activeCohort && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-900">
                  {activeCohort.name} のペルソナ一覧
                </h3>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  activeCohort.generation_mode === 'mode_a'
                    ? 'bg-slate-100 text-slate-700'
                    : activeCohort.generation_mode === 'mode_c'
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-indigo-100 text-indigo-800'
                }`}>
                  {activeCohort.generation_mode === 'mode_a'
                    ? 'Mode A (人口統計)'
                    : activeCohort.generation_mode === 'mode_c'
                    ? 'Mode C (実測接地)'
                    : 'Mode B (合成生活史)'}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                総ペルソナ数: {totalCount}名 / シード値: {activeCohort.seed}
              </p>
            </div>

            <button
              onClick={() => setShowValidationModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-white border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-xs"
            >
              <BarChart2 className="w-4 h-4 text-brand-600" />
              日本の統計分布との整合性を確認
            </button>
          </div>

          {/* Filters Bar */}
          <div className="flex flex-wrap items-center gap-3 bg-white p-3 rounded-xl border border-slate-200 shadow-xs">
            <div className="flex-1 min-w-[200px] relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="名前・職業・価値観で検索..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <select
              value={genderFilter}
              onChange={(e) => setGenderFilter(e.target.value)}
              className="text-xs px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white text-slate-700"
            >
              <option value="">全性別</option>
              <option value="男性">男性</option>
              <option value="女性">女性</option>
            </select>

            <select
              value={ageFilter}
              onChange={(e) => setAgeFilter(e.target.value)}
              className="text-xs px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white text-slate-700"
            >
              <option value="">全年代</option>
              <option value="20代">20代</option>
              <option value="30代">30代</option>
              <option value="40代">40代</option>
              <option value="50代">50代</option>
              <option value="60代">60代</option>
              <option value="70代以上">70代以上</option>
            </select>

            <select
              value={valuesFilter}
              onChange={(e) => setValuesFilter(e.target.value)}
              className="text-xs px-2.5 py-1.5 border border-slate-200 rounded-lg bg-white text-slate-700"
            >
              <option value="">全価値観セグメント</option>
              <option value="コスト・実利重視">コスト・実利重視</option>
              <option value="タイパ・効率重視">タイパ・効率重視</option>
              <option value="品質・本物志向">品質・本物志向</option>
              <option value="エコ・社会貢献志向">エコ・社会貢献志向</option>
              <option value="トレンド・自己投資志向">トレンド・自己投資志向</option>
              <option value="安心・定番重視">安心・定番重視</option>
            </select>

            <button
              onClick={loadPersonas}
              className="px-3 py-1.5 bg-slate-800 text-white rounded-lg text-xs font-medium hover:bg-slate-700 shadow-xs"
            >
              検索
            </button>
          </div>

          {/* Master-Detail Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Personas List */}
            <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs">
              <div className="p-3 bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-700 flex justify-between">
                <span>ペルソナ一覧</span>
                <span>{personas.length} 名</span>
              </div>
              <div className="divide-y divide-slate-100 max-h-[640px] overflow-y-auto">
                {isLoadingPersonas ? (
                  <div className="p-8 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
                    読込中...
                  </div>
                ) : personas.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 text-xs">
                    該当するペルソナが見つかりませんでした
                  </div>
                ) : (
                  personas.map((p) => {
                    const isSelected = selectedPersona?.id === p.id;
                    return (
                      <div
                        key={p.id}
                        onClick={() => setSelectedPersona(p)}
                        className={`p-3.5 cursor-pointer transition-colors ${
                          isSelected ? 'bg-brand-50/80 border-l-4 border-brand-600' : 'hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-xs text-slate-900">{p.name}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                              {p.persona_code}
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            {p.generation_mode === 'mode_c' && (
                              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                                接地
                              </span>
                            )}
                            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                              p.gender === '男性' ? 'bg-blue-50 text-blue-700' : 'bg-rose-50 text-rose-700'
                            }`}>
                              {p.gender}・{p.age}歳
                            </span>
                          </div>
                        </div>
                        <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-2">
                          <span>{p.prefecture}</span>
                          <span>•</span>
                          <span className="truncate max-w-[150px]">{p.occupation}</span>
                          <span>•</span>
                          <span className="font-medium text-slate-700">{p.personal_income}万円</span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-1">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-100">
                            {p.values_segment}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Persona Detail Card */}
            <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 p-6 shadow-xs sticky top-20">
              {selectedPersona ? (
                <div className="space-y-6">
                  {/* Persona Header */}
                  <div className="flex items-start justify-between pb-4 border-b border-slate-100">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-lg text-slate-900">{selectedPersona.name}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono">
                          {selectedPersona.persona_code}
                        </span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          selectedPersona.generation_mode === 'mode_a'
                            ? 'bg-slate-100 text-slate-700'
                            : selectedPersona.generation_mode === 'mode_c'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-indigo-100 text-indigo-800'
                        }`}>
                          {selectedPersona.generation_mode === 'mode_a'
                            ? 'Mode A (人口統計のみ)'
                            : selectedPersona.generation_mode === 'mode_c'
                            ? 'Mode C (実測接地)'
                            : 'Mode B (合成生活史)'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        {selectedPersona.age}歳 ({selectedPersona.age_group}) / {selectedPersona.gender} / {selectedPersona.prefecture} ({selectedPersona.region})
                      </p>
                    </div>
                    <button
                      onClick={() => onStartInterviewWithPersona(selectedPersona)}
                      className="px-3.5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-all"
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      1対1でAIインタビューする
                    </button>
                  </div>

                  {/* Mode C Verbatim Quotes if available */}
                  {selectedPersona.generation_mode === 'mode_c' && selectedPersona.grounded_interview?.verbatim_quotes && (
                    <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                          <Quote className="w-3.5 h-3.5 text-emerald-600" />
                          定性インタビュー 元発言引用（Verbatim Quotes - 要約前生声）
                        </span>
                        <span className="text-[10px] font-bold px-2 py-0.2 rounded bg-emerald-200/80 text-emerald-900">
                          本人同意取得済
                        </span>
                      </div>
                      <div className="space-y-1.5">
                        {selectedPersona.grounded_interview.verbatim_quotes.map((q: string, idx: number) => (
                          <p key={idx} className="text-xs text-emerald-950 italic pl-3 border-l-2 border-emerald-500">
                            「{q}」
                          </p>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Mode B Life History if available */}
                  {selectedPersona.generation_mode === 'mode_b' && selectedPersona.life_history && (
                    <div className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-100 space-y-2">
                      <span className="text-xs font-bold text-indigo-900 flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-indigo-600" />
                        仮想生活史（統計事前分布に基づく合成ナラティブ）
                      </span>
                      <p className="text-xs text-indigo-950 leading-relaxed">
                        {selectedPersona.life_history}
                      </p>
                      {selectedPersona.purchase_experiences && selectedPersona.purchase_experiences.length > 0 && (
                        <div className="pt-2 border-t border-indigo-100">
                          <span className="text-[11px] font-semibold text-indigo-800 block mb-1">最近の購買・利用エピソード:</span>
                          <ul className="list-disc pl-4 text-xs text-indigo-900 space-y-1">
                            {selectedPersona.purchase_experiences.map((exp: string, idx: number) => (
                              <li key={idx}>{exp}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Attributes Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block mb-0.5 flex items-center gap-1"><Briefcase className="w-3 h-3"/>職業・雇用</span>
                      <span className="font-medium text-slate-800">{selectedPersona.occupation}</span>
                    </div>
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block mb-0.5 flex items-center gap-1"><Wallet className="w-3 h-3"/>年収 (個人/世帯)</span>
                      <span className="font-medium text-slate-800">{selectedPersona.personal_income}万 / {selectedPersona.household_income}万</span>
                    </div>
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block mb-0.5 flex items-center gap-1"><GraduationCap className="w-3 h-3"/>最終学歴</span>
                      <span className="font-medium text-slate-800">{selectedPersona.education}</span>
                    </div>
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block mb-0.5">世帯構成</span>
                      <span className="font-medium text-slate-800">{selectedPersona.household}</span>
                    </div>
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block mb-0.5 flex items-center gap-1"><Compass className="w-3 h-3"/>意思決定スタイル</span>
                      <span className="font-medium text-slate-800">{selectedPersona.decision_style}</span>
                    </div>
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block mb-0.5 flex items-center gap-1"><Heart className="w-3 h-3"/>消費価値観</span>
                      <span className="font-medium text-brand-700">{selectedPersona.values_segment}</span>
                    </div>
                  </div>

                  {/* Badges / Tags */}
                  <div>
                    <h4 className="text-xs font-semibold text-slate-700 mb-2">趣味・情報収集チャネル</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedPersona.hobbies?.map((h) => (
                        <span key={h} className="text-[11px] px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 font-medium">
                          {h}
                        </span>
                      ))}
                      {selectedPersona.info_channels?.map((c) => (
                        <span key={c} className="text-[11px] px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 font-medium">
                          📱 {c}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Full Consumption Profile Story */}
                  <div>
                    <h4 className="text-xs font-semibold text-slate-700 mb-2">生活・消費行動プロファイル</h4>
                    <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 text-xs text-slate-700 leading-relaxed">
                      {selectedPersona.consumption_profile}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-16 text-slate-400 text-xs">
                  左側の一覧からペルソナを選択してください
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Ingest Interview Modal */}
      {showIngestModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <UploadCloud className="w-4 h-4 text-emerald-600" />
                定性インタビュー記録のアップロード（Gemini 発言・価値観抽出）
              </h3>
              <button 
                onClick={() => setShowIngestModal(false)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">データセット名称</label>
              <input
                type="text"
                value={newDatasetName}
                onChange={(e) => setNewDatasetName(e.target.value)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">インタビュー文字起こしテキスト（またはQ&A）</label>
              <textarea
                rows={6}
                value={newDatasetContent}
                onChange={(e) => setNewDatasetContent(e.target.value)}
                placeholder="参加者A: 34歳女性、都内在住の共働き子育て世帯。&#10;Q: 普段の日用品の購入で一番重視することは？&#10;A: 「スーパーの棚で迷う時間がもったいないので、Amazonの定期便でまとめ買いしてます。多少高くても時間の節約が最優先ですね」"
                className="w-full text-xs p-3 border border-slate-300 rounded-lg font-mono"
              />
            </div>

            {/* Mandatory Privacy Consent Checkbox */}
            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200">
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={consentConfirmed}
                  onChange={(e) => setConsentConfirmed(e.target.checked)}
                  className="mt-0.5 rounded text-emerald-600 focus:ring-emerald-500"
                />
                <span className="text-[11px] text-amber-900 leading-relaxed font-medium">
                  <strong>【個人情報保護・同意確認】</strong>実在の調査参加者からリサーチ目的での利用許諾を得ており、機微情報（氏名・詳細住所等）が含まれない、またはマスキング済みであることを確認しました。
                </span>
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowIngestModal(false)}
                className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-50"
              >
                キャンセル
              </button>
              <button
                type="button"
                onClick={handleIngestDataset}
                disabled={isIngesting || !consentConfirmed}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold disabled:opacity-50 flex items-center gap-1.5"
              >
                {isIngesting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                Geminiで価値観・発言引用を抽出して登録
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Validation Modal */}
      {showValidationModal && (
        <PersonaValidationModal
          distribution={cohortDetail?.distribution || null}
          cohortName={activeCohort?.name || ''}
          onClose={() => setShowValidationModal(false)}
        />
      )}
    </div>
  );
};
