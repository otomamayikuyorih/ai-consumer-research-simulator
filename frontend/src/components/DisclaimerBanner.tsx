import React, { useState } from 'react';
import { AlertCircle, X, ShieldAlert } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 text-xs text-amber-900 flex items-center justify-between">
      <div className="flex items-center gap-2 max-w-5xl">
        <ShieldAlert className="w-4 h-4 text-amber-600 flex-shrink-0" />
        <div>
          <span className="font-semibold text-amber-800">【シミュレーション検証上の注意点】</span>
          本システムによるペルソナ属性およびアンケート・インタビュー回答は、日本の公的統計データ等を基にしたAI合成シミュレーションであり、実在の消費者調査結果や市場予測を保証するものではありません。合成ペルソナの回答比率は、実母集団の統計的推定値と混同しないようご留意ください。
        </div>
      </div>
      <button
        onClick={() => setDismissed(true)}
        className="text-amber-500 hover:text-amber-700 ml-4 p-1 rounded"
        title="閉じる"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
