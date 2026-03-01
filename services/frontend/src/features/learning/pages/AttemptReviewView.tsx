import { ArrowLeft, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '../../../shared/ui/button';
import { Badge } from '../../../shared/ui/badge';
import type { QuestionType } from '../../quiz/entities/question/types';

type BaseReviewItem = {
  id: string;
  type: QuestionType;
  prompt: string;
  theme: string;
  isCorrect: boolean;
};

type MultipleChoiceReviewItem = BaseReviewItem & {
  type: 'multiple-choice';
  options: string[];
  correctIndexes: number[];
  selectedIndexes: number[];
};

type FreeTextReviewItem = BaseReviewItem & {
  type: 'freitext';
  userText: string;
  solution: string;
};

type ClozeReviewItem = BaseReviewItem & {
  type: 'lueckentext';
  textParts: string[];
  userWords: string[];
  correctWords: string[];
  perBlankCorrect: boolean[];
};

export type AttemptReviewItem =
  | MultipleChoiceReviewItem
  | FreeTextReviewItem
  | ClozeReviewItem;

type AttemptReviewViewProps = {
  quizTitle: string;
  quizTheme: string;
  startedAt: Date;
  evaluatedAt: Date | null;
  score: number | null;
  items: AttemptReviewItem[];
  onBack: () => void;
};

const formatDate = (date: Date) => {
  return new Intl.DateTimeFormat('de-DE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

const getScoreBadgeColor = (score: number | null) => {
  if (score === null) return 'bg-slate-100 text-slate-600';
  if (score >= 90) return 'bg-green-100 text-green-700';
  if (score >= 70) return 'bg-blue-100 text-blue-700';
  if (score >= 50) return 'bg-yellow-100 text-yellow-700';
  return 'bg-red-100 text-red-700';
};

const getTypeLabel = (type: QuestionType) => {
  switch (type) {
    case 'multiple-choice':
      return 'Multiple Choice';
    case 'freitext':
      return 'Freitext';
    case 'lueckentext':
      return 'Lueckentext';
    default:
      return type;
  }
};

export function AttemptReviewView({
  quizTitle,
  quizTheme,
  startedAt,
  evaluatedAt,
  score,
  items,
  onBack,
}: AttemptReviewViewProps) {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
        <Button
          onClick={onBack}
          variant="ghost"
          className="mb-4 -ml-2 text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Zurueck zum Quiz
        </Button>
        <div className="flex items-start justify-between gap-6 flex-wrap">
          <div>
            <h2 className="text-slate-900 text-[26px] mb-1">{quizTitle}</h2>
            <p className="text-slate-600">{quizTheme}</p>
          </div>
          <div className="flex items-center gap-3">
            <Badge className={getScoreBadgeColor(score)}>
              Punktzahl: {score !== null ? `${Math.round(score)}%` : '-'}
            </Badge>
          </div>
        </div>
        <div className="mt-4 text-sm text-slate-600 flex flex-wrap gap-4">
          <span>Gestartet: {formatDate(startedAt)}</span>
          <span>
            Abgeschlossen: {evaluatedAt ? formatDate(evaluatedAt) : '-'}
          </span>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm text-slate-600">
          Keine Antworten fuer diesen Versuch gefunden.
        </div>
      ) : (
        items.map((item, index) => (
          <div key={item.id} className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h3 className="text-slate-900 text-[18px]">
                  Frage {index + 1}
                </h3>
                <p className="text-sm text-slate-600">
                  {getTypeLabel(item.type)} · {item.theme}
                </p>
              </div>
              <Badge className={item.isCorrect ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}>
                {item.isCorrect ? (
                  <span className="flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" />
                    Richtig
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <XCircle className="w-3 h-3" />
                    Falsch
                  </span>
                )}
              </Badge>
            </div>

            <p className="text-slate-900 mb-4">{item.prompt}</p>

            {item.type === 'multiple-choice' && (
              <div className="space-y-2">
                {item.options.map((option, optionIndex) => {
                  const isCorrectOption = item.correctIndexes.includes(optionIndex);
                  const isSelected = item.selectedIndexes.includes(optionIndex);
                  const baseClasses = 'w-full p-3 rounded-lg border text-left flex items-center justify-between';
                  const stateClasses = isCorrectOption
                    ? 'border-green-300 bg-green-50 text-green-800'
                    : isSelected
                      ? 'border-red-300 bg-red-50 text-red-800'
                      : 'border-slate-200 text-slate-700';
                  return (
                    <div key={optionIndex} className={`${baseClasses} ${stateClasses}`}>
                      <span>{option}</span>
                      {isCorrectOption && <span className="text-xs">Richtig</span>}
                      {!isCorrectOption && isSelected && <span className="text-xs">Deine Wahl</span>}
                    </div>
                  );
                })}
              </div>
            )}

            {item.type === 'freitext' && (
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-slate-500 mb-1">Deine Antwort</p>
                  <div className="p-3 rounded-lg border border-slate-200 bg-slate-50 text-slate-900">
                    {item.userText ? item.userText : 'Keine Antwort'}
                  </div>
                </div>
                <div>
                  <p className="text-sm text-slate-500 mb-1">Musterloesung</p>
                  <div className="p-3 rounded-lg border border-slate-200 bg-white text-slate-900">
                    {item.solution}
                  </div>
                </div>
              </div>
            )}

            {item.type === 'lueckentext' && (
              <div className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-lg">
                  {item.textParts.map((part, partIndex) => (
                    <span key={partIndex}>
                      {part}
                      {partIndex < item.textParts.length - 1 && (
                        <span
                          className={`inline-flex items-center justify-center min-w-[110px] mx-1 px-3 py-1 rounded border-2 ${
                            item.perBlankCorrect[partIndex]
                              ? 'bg-green-50 border-green-300 text-green-700'
                              : 'bg-red-50 border-red-300 text-red-700'
                          }`}
                        >
                          {item.userWords[partIndex] || '___'}
                        </span>
                      )}
                    </span>
                  ))}
                </div>
                <div className="text-sm text-slate-600 flex flex-wrap gap-2">
                  <span className="font-medium">Richtige Loesung:</span>
                  {item.correctWords.map((word, wordIndex) => (
                    <span key={wordIndex} className="px-2 py-0.5 bg-slate-100 rounded">
                      {wordIndex + 1}. {word}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}
