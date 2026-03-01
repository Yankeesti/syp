import { Check } from 'lucide-react';
import type { Question } from '../../quiz/entities/question/types';

interface QuestionProgressBarProps {
  questions: Question[];
  currentQuestionIndex: number;
  answeredQuestionIds: string[];
  onQuestionClick?: (index: number) => void;
}

export function QuestionProgressBar({
  questions,
  currentQuestionIndex,
  answeredQuestionIds,
  onQuestionClick,
}: QuestionProgressBarProps) {
  return (
    <div className="mb-6 bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-slate-700">Fragenübersicht</h3>
        <span className="text-xs text-slate-500">
          {answeredQuestionIds.length} von {questions.length} beantwortet
        </span>
      </div>
      <div className="flex items-center gap-2 flex-wrap">
        {questions.map((question, index) => {
          const isAnswered = answeredQuestionIds.includes(question.id);
          const isCurrent = index === currentQuestionIndex;
          
          return (
            <button
              key={question.id}
              onClick={() => onQuestionClick?.(index)}
              className={`
                relative flex items-center justify-center min-w-[44px] h-11 px-3 rounded-lg font-medium text-sm
                transition-all duration-200
                ${isCurrent 
                  ? 'bg-blue-600 text-white ring-2 ring-blue-300 ring-offset-2 z-10' 
                  : isAnswered
                  ? 'bg-green-100 text-green-700 hover:bg-green-200 border-2 border-green-300'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200 border-2 border-slate-300'
                }
                ${onQuestionClick ? 'cursor-pointer' : 'cursor-default'}
              `}
              title={`Frage ${index + 1}${isAnswered ? ' - Beantwortet' : ' - Nicht beantwortet'}`}
            >
              {isAnswered ? (
                <Check className="w-5 h-5" />
              ) : (
                <span className="text-base">{index + 1}</span>
              )}
              {isCurrent && (
                <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-blue-600 rounded-full" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

