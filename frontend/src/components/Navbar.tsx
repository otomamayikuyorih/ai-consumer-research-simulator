import React, { useState } from 'react';
import { 
  Users, 
  FileQuestion, 
  PlayCircle, 
  BarChart3, 
  MessageSquare, 
  Sparkles, 
  LayoutDashboard,
  Cpu,
  FlaskConical,
  Award,
  ChevronDown,
  ChevronRight,
  Compass
} from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  systemStatus: { has_gemini_key: boolean; mode: string } | null;
  activeCohortName?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  systemStatus,
  activeCohortName
}) => {
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  // 9つの機能を4つの分かりやすい親カテゴリに構造化（中身・名称・機能は完全維持）
  const categories = [
    {
      id: 'dashboard_cat',
      label: 'ダッシュボード',
      icon: LayoutDashboard,
      defaultTab: 'dashboard',
      isSingle: true,
      items: [
        { id: 'dashboard', label: 'ダッシュボード', icon: LayoutDashboard, desc: '調査・シミュレーション全体の概況とサマリー' },
      ],
    },
    {
      id: 'research_cat',
      label: '基本調査フロー',
      icon: Compass,
      defaultTab: 'personas',
      hasFlowArrow: true,
      items: [
        { id: 'personas', label: 'ペルソナ生成・検証', icon: Users, desc: '公的統計準拠の消費者コホート生成・属性検証' },
        { id: 'builder', label: 'アンケート作成', icon: FileQuestion, desc: '設問作成（単一・複数・5段階・自由記述）' },
        { id: 'runner', label: '調査シミュレーション', icon: PlayCircle, desc: 'ペルソナ集団へのGemini回答配信・推論実行' },
        { id: 'analytics', label: '結果解析・多変量', icon: BarChart3, desc: 'クロス集計、カイ二乗検定、PCA知覚マップ、K-Means' },
      ],
    },
    {
      id: 'ai4pb_cat',
      label: 'AI4PB 学術実験・検証',
      badge: 'Nature 2026',
      icon: FlaskConical,
      defaultTab: 'ab_test',
      isSpecial: true,
      items: [
        { id: 'ab_test', label: '仮想A/B実験', icon: FlaskConical, desc: 'Control vs Treatment、カウンターバランス法、Cohen\'s d' },
        { id: 'validation', label: 'Human-AI検証', icon: Award, desc: '実測人間回答 vs AI回答のMAE・RMSE・50/50汎化検証' },
      ],
    },
    {
      id: 'qualitative_cat',
      label: '定性対話・商品評価',
      icon: MessageSquare,
      defaultTab: 'interview',
      items: [
        { id: 'interview', label: 'AIインタビュー', icon: MessageSquare, desc: '選択したペルソナ（生声引用保持）との1on1深掘り対話' },
        { id: 'concept', label: 'コンセプト評価', icon: Sparkles, desc: '新商品・サービスの価格受容性・購入意向A/B評価' },
      ],
    },
  ];

  // 現在のタブがどの親カテゴリに属しているかを特定
  const activeCategory = categories.find(cat => cat.items.some(item => item.id === currentTab)) || categories[0];

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Row 1: ロゴ & タイトル（左） + システム稼働状況・選択中コホート（右） */}
        <div className="flex items-center justify-between h-13 py-2 border-b border-slate-100">
          {/* Logo & Title */}
          <div className="flex items-center gap-2.5 shrink-0 whitespace-nowrap">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center text-white shadow-xs shrink-0">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base text-slate-900 tracking-tight whitespace-nowrap">
                  AI Consumer Research Simulator
                </span>
                <span className="text-[10px] font-bold px-1.5 py-0.2 rounded-full bg-slate-100 text-slate-600 border border-slate-200 whitespace-nowrap">
                  MVP v1.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden md:block whitespace-nowrap">
                公的統計準拠ペルソナ群 × Google Gemini AI リサーチエンジン
              </p>
            </div>
          </div>

          {/* Status indicators */}
          <div className="flex items-center gap-2 shrink-0">
            {activeCohortName && (
              <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 text-xs text-slate-700 border border-slate-200 whitespace-nowrap">
                <Users className="w-3.5 h-3.5 text-brand-600 shrink-0" />
                <span className="text-slate-400">コホート:</span>
                <span className="font-medium truncate max-w-[140px]">{activeCohortName}</span>
              </div>
            )}
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-emerald-50 text-emerald-700 border-emerald-200 whitespace-nowrap">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0"></span>
              <span>{systemStatus?.has_gemini_key ? 'Gemini API 稼働中' : '統計推計シミュレーション'}</span>
            </div>
          </div>
        </div>

        {/* Row 2: 4つの主要カテゴリ（全幅を広く使い、文字の改行を100%防止） */}
        <nav className="flex items-center gap-1.5 sm:gap-2.5 py-1.5 overflow-x-auto scrollbar-none">
          {categories.map((cat) => {
            const Icon = cat.icon;
            const isCatActive = activeCategory.id === cat.id;
            const isOpen = openDropdown === cat.id;

            if (cat.isSingle) {
              return (
                <button
                  key={cat.id}
                  onClick={() => setCurrentTab('dashboard')}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap shrink-0 transition-all ${
                    isCatActive
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5 shrink-0" />
                  <span className="whitespace-nowrap">{cat.label}</span>
                </button>
              );
            }

            return (
              <div 
                key={cat.id} 
                className="relative shrink-0"
                onMouseEnter={() => setOpenDropdown(cat.id)}
                onMouseLeave={() => setOpenDropdown(null)}
              >
                <button
                  onClick={() => {
                    if (!isCatActive) {
                      setCurrentTab(cat.defaultTab);
                    }
                  }}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap shrink-0 transition-all ${
                    isCatActive
                      ? cat.isSpecial
                        ? 'bg-indigo-600 text-white shadow-xs ring-1 ring-indigo-400'
                        : 'bg-slate-900 text-white shadow-xs'
                      : cat.isSpecial
                      ? 'text-indigo-700 bg-indigo-50/70 hover:bg-indigo-100/70 border border-indigo-200/60'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5 shrink-0" />
                  <span className="whitespace-nowrap">{cat.label}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold whitespace-nowrap ${
                    isCatActive 
                      ? 'bg-white/20 text-white' 
                      : cat.isSpecial ? 'bg-indigo-200/80 text-indigo-800' : 'bg-slate-200 text-slate-600'
                  }`}>
                    {cat.items.length}
                  </span>
                  <ChevronDown className="w-3 h-3 opacity-60 shrink-0" />
                </button>

                {/* Dropdown Menu for Direct 1-Click Jumping */}
                {isOpen && (
                  <div className="absolute top-full left-0 mt-1 w-72 bg-white rounded-xl shadow-xl border border-slate-200 p-1.5 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
                    <div className="text-[10px] font-bold text-slate-400 px-2 py-1 uppercase tracking-wider whitespace-nowrap">
                      {cat.label} 内のメニュー
                    </div>
                    <div className="space-y-0.5">
                      {cat.items.map((sub) => {
                        const SubIcon = sub.icon;
                        const isSubActive = currentTab === sub.id;
                        return (
                          <button
                            key={sub.id}
                            onClick={() => {
                              setCurrentTab(sub.id);
                              setOpenDropdown(null);
                            }}
                            className={`w-full text-left px-2.5 py-2 rounded-lg text-xs transition-colors flex items-start gap-2.5 ${
                              isSubActive
                                ? 'bg-brand-50 text-brand-900 font-bold'
                                : 'text-slate-700 hover:bg-slate-50'
                            }`}
                          >
                            <SubIcon className={`w-4 h-4 shrink-0 mt-0.5 ${
                              isSubActive ? 'text-brand-600' : 'text-slate-400'
                            }`} />
                            <div>
                              <span className="block leading-tight whitespace-nowrap">{sub.label}</span>
                              <span className="block text-[10px] text-slate-400 font-normal leading-tight mt-0.5">
                                {sub.desc}
                              </span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </div>

      {/* Row 3: 選択されたカテゴリのサブナビゲーション（1行でゆったり横並び表示） */}
      {activeCategory.id !== 'dashboard_cat' && (
        <div className="bg-slate-50 border-t border-slate-200/90 py-1.5 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto scrollbar-none text-xs">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-1 whitespace-nowrap hidden sm:inline">
                {activeCategory.label}:
              </span>

              {activeCategory.items.map((item, idx) => {
                const Icon = item.icon;
                const isActive = currentTab === item.id;
                return (
                  <React.Fragment key={item.id}>
                    <button
                      onClick={() => setCurrentTab(item.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap shrink-0 transition-all ${
                        isActive
                          ? 'bg-white text-brand-700 shadow-xs border border-slate-200/80 ring-1 ring-brand-500/10'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                      }`}
                    >
                      <Icon className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-brand-600' : 'text-slate-400'}`} />
                      <span className="whitespace-nowrap">{item.label}</span>
                    </button>

                    {/* 基本調査フローの場合はステップ順を矢印で分かりやすく提示 */}
                    {activeCategory.hasFlowArrow && idx < activeCategory.items.length - 1 && (
                      <ChevronRight className="w-3.5 h-3.5 text-slate-300 shrink-0 hidden sm:block" />
                    )}
                  </React.Fragment>
                );
              })}
            </div>

            {/* AI4PB 学術注記バッジ */}
            {activeCategory.id === 'ai4pb_cat' && (
              <span className="text-[10px] text-indigo-600 font-bold hidden md:inline bg-indigo-100/60 px-2 py-0.5 rounded whitespace-nowrap">
                Stanford AI4PB & Nature 2026 Reference
              </span>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
