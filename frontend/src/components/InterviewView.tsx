import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  Send, 
  User, 
  Bot, 
  Sparkles, 
  Loader2, 
  ChevronRight,
  Briefcase,
  Wallet,
  Compass,
  Heart,
  HelpCircle
} from 'lucide-react';
import { Persona, Cohort, ChatMessage } from '../types';
import { fetchCohortPersonas, sendInterviewMessage, fetchInterviewHistory } from '../services/api';

interface InterviewViewProps {
  cohorts: Cohort[];
  activeCohort: Cohort | null;
  targetPersona: Persona | null;
  onSelectPersona: (persona: Persona) => void;
}

const SUGGESTED_PROMPTS = [
  'なぜ先ほどのアンケートでその選択肢を選ばれたのですか？',
  'もし商品の価格が2〜3割高くなったら、購入をためらいますか？',
  '新しい商品を知ったとき、普段どのような情報源（SNSや口コミ等）を確認しますか？',
  '日頃のお買い物で「これだけは譲れない」という決め手は何ですか？',
  'ご自身の今の生活スタイルで、一番ストレスや手間を感じていることは何ですか？',
];

export const InterviewView: React.FC<InterviewViewProps> = ({
  cohorts,
  activeCohort,
  targetPersona,
  onSelectPersona,
}) => {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Load cohort personas
  useEffect(() => {
    if (activeCohort) {
      fetchCohortPersonas(activeCohort.id, { limit: 50 }).then((res) => {
        setPersonas(res.items);
        if (!targetPersona && res.items.length > 0) {
          onSelectPersona(res.items[0]);
        }
      });
    }
  }, [activeCohort]);

  // Load chat history when targetPersona changes
  useEffect(() => {
    if (targetPersona) {
      fetchInterviewHistory(targetPersona.id).then((res) => {
        setMessages(res.messages || []);
      });
    }
  }, [targetPersona]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || !targetPersona || isSending) return;

    const userMsg: ChatMessage = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsSending(true);

    try {
      const res = await sendInterviewMessage(targetPersona.id, text);
      setMessages(res.history);
    } catch (err) {
      alert('メッセージの送信に失敗しました: ' + err);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <MessageSquare className="w-6 h-6 text-purple-600" />
          AIインタビュー（生活者1on1対話）
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          アンケート回答者から特定のペルソナを選択し、回答の背景や生活実感を深掘りインタビューできます
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Persona Selector & Persona Profile Card */}
        <div className="lg:col-span-4 space-y-4">
          {/* Persona Picker */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">対話する生活者を選択</label>
            <select
              value={targetPersona?.id || ''}
              onChange={(e) => {
                const found = personas.find((p) => p.id === e.target.value);
                if (found) onSelectPersona(found);
              }}
              className="w-full text-xs font-semibold px-3 py-2 border border-slate-300 rounded-lg bg-white"
            >
              {personas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.age}歳{p.gender} / {p.occupation})
                </option>
              ))}
            </select>
          </div>

          {/* Detailed Profile Summary */}
          {targetPersona && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
              <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
                <div className="w-11 h-11 rounded-full bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-sm">
                  {targetPersona.name.slice(0, 1)}
                </div>
                <div>
                  <h4 className="font-bold text-sm text-slate-900">{targetPersona.name}</h4>
                  <p className="text-xs text-slate-500">
                    {targetPersona.age}歳 ({targetPersona.gender})・{targetPersona.prefecture}在住
                  </p>
                </div>
              </div>

              <div className="space-y-2.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">職業・働き方</span>
                  <span className="font-medium text-slate-800 truncate max-w-[170px]">{targetPersona.occupation}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">世帯構成</span>
                  <span className="font-medium text-slate-800">{targetPersona.household}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">個人年収 / 世帯年収</span>
                  <span className="font-medium text-slate-800">{targetPersona.personal_income}万 / {targetPersona.household_income}万</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">消費価値観</span>
                  <span className="font-semibold text-brand-700">{targetPersona.values_segment}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">意思決定傾向</span>
                  <span className="font-medium text-slate-800">{targetPersona.decision_style}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100">
                <span className="text-[11px] font-semibold text-slate-400 block mb-1">趣味・利用情報源</span>
                <div className="flex flex-wrap gap-1">
                  {targetPersona.hobbies?.slice(0, 3).map((h) => (
                    <span key={h} className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                      {h}
                    </span>
                  ))}
                  {targetPersona.info_channels?.slice(0, 2).map((c) => (
                    <span key={c} className="text-[10px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700">
                      {c}
                    </span>
                  ))}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100">
                <span className="text-[11px] font-semibold text-slate-400 block mb-1">生活者プロファイル</span>
                <p className="text-[11px] text-slate-600 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                  {targetPersona.consumption_profile}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Right: Interactive Chat Room */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col h-[700px] overflow-hidden">
          {/* Chat Header */}
          <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-xs font-bold text-slate-800">
                {targetPersona?.name || 'ペルソナ'} とのリアルタイム対話中
              </span>
            </div>
            <span className="text-[11px] text-slate-400">
              ペルソナ一貫性プロンプト適用済み
            </span>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-slate-50/40">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-purple-100 text-purple-600 flex items-center justify-center">
                  <Sparkles className="w-6 h-6" />
                </div>
                <h4 className="font-bold text-slate-800 text-sm">{targetPersona?.name}さんへの深掘りインタビューを開始</h4>
                <p className="text-xs text-slate-500 max-w-sm">
                  「なぜあの回答をしたのか？」「いくらなら買うか？」など、マーケティング上の仮説検証となる質問を自由に投げかけてみてください。
                </p>
              </div>
            ) : (
              messages.map((msg, i) => {
                const isUser = msg.role === 'user';
                return (
                  <div key={i} className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
                    {!isUser && (
                      <div className="w-8 h-8 rounded-full bg-purple-600 text-white flex items-center justify-center font-bold text-xs flex-shrink-0 shadow-xs">
                        {targetPersona?.name.slice(0, 1)}
                      </div>
                    )}
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-xs ${
                        isUser
                          ? 'bg-brand-600 text-white rounded-br-none'
                          : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      <span className={`text-[9px] block mt-1.5 ${isUser ? 'text-brand-200 text-right' : 'text-slate-400'}`}>
                        {new Date(msg.timestamp).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                );
              })
            )}

            {isSending && (
              <div className="flex gap-3 justify-start items-center">
                <div className="w-8 h-8 rounded-full bg-purple-600 text-white flex items-center justify-center font-bold text-xs flex-shrink-0">
                  {targetPersona?.name.slice(0, 1)}
                </div>
                <div className="bg-white border border-slate-200 px-4 py-3 rounded-2xl rounded-bl-none text-xs text-slate-500 flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-600" />
                  {targetPersona?.name}さんが考えながら回答しています...
                </div>
              </div>
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Suggested Prompts Pill Strip */}
          <div className="px-4 py-2 bg-slate-100/70 border-t border-slate-200 overflow-x-auto flex gap-1.5 scrollbar-none">
            <span className="text-[10px] font-bold text-slate-500 whitespace-nowrap self-center mr-1 flex items-center gap-1">
              <HelpCircle className="w-3 h-3" /> おすすめの質問:
            </span>
            {SUGGESTED_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(prompt)}
                disabled={isSending}
                className="text-[11px] bg-white hover:bg-slate-50 text-slate-700 px-2.5 py-1 rounded-full border border-slate-200 whitespace-nowrap shadow-2xs transition-all disabled:opacity-50"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Footer */}
          <div className="p-4 bg-white border-t border-slate-200 flex items-center gap-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
              placeholder={`${targetPersona?.name || 'ペルソナ'}さんに質問を入力...`}
              disabled={isSending}
              className="flex-1 text-xs px-3.5 py-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={isSending || !inputMessage.trim()}
              className="px-4 py-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-xs transition-all disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              送信
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
