import { Plus, Clock, User, Users } from 'lucide-react';
import { Button } from '../../../shared/ui/button';
import { Badge } from '../../../shared/ui/badge';
import type { Quiz } from '../entities/quiz/types';
import type { QuestionType } from '../entities/question/types';

interface QuizListViewProps {
  quizzes: Quiz[];
  currentUserId: string;
  onCreateQuiz: () => void;
  onSelectQuiz: (quizId: string) => void;
}

export function QuizListView({ quizzes, currentUserId, onCreateQuiz, onSelectQuiz }: QuizListViewProps) {
  const getTypeLabel = (type: QuestionType) => {
    switch (type) {
      case 'multiple-choice':
        return 'Multiple Choice';
      case 'freitext':
        return 'Freitext';
      case 'lueckentext':
        return 'Lückentext';
      default:
        return type;
    }
  };

  const getStatusLabel = (status: Quiz['status']) => {
    switch (status) {
      case 'pending':
        return 'Ausstehend';
      case 'generating':
        return 'Generierung laeuft';
      case 'completed':
        return 'Fertig';
      case 'failed':
        return 'Fehlgeschlagen';
      default:
        return null;
    }
  };

  const getStatusBadgeColor = (status: Quiz['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'failed':
        return 'bg-red-50 text-red-700 border-red-200';
      case 'pending':
      case 'generating':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      default:
        return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  const canEdit = (quiz: Quiz) => {
    return quiz.ownerId === currentUserId || quiz.editors.includes(currentUserId);
  };

  const formatDate = (date: Date) => {
    return new Intl.DateTimeFormat('de-DE', { 
      day: '2-digit', 
      month: 'short', 
      year: 'numeric' 
    }).format(date);
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-slate-900 text-[24px] mb-2">Meine Quizze</h2>
            <p className="text-slate-600">
              Verwalten Sie Ihre Quizze und starten Sie neue Lernversuche
            </p>
          </div>
          <Button onClick={onCreateQuiz} className="bg-blue-600 hover:bg-blue-700">
            <Plus className="w-4 h-4 mr-2" />
            Neues Quiz generieren
          </Button>
        </div>

        {quizzes.length === 0 ? (
          <div className="text-center py-16 bg-slate-50 rounded-lg border-2 border-dashed border-slate-200">
            <div className="text-slate-400 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-slate-900 mb-2">Noch keine Quizze vorhanden</h3>
            <p className="text-slate-500 mb-6">
              Erstellen Sie Ihr erstes Quiz, um mit dem Lernen zu beginnen
            </p>
            <Button onClick={onCreateQuiz} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Erstes Quiz erstellen
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {quizzes.map((quiz) => {
              const statusLabel = getStatusLabel(quiz.status);

              return (
                <div
                  key={quiz.id}
                  onClick={() => onSelectQuiz(quiz.id)}
                  className="bg-white border border-slate-200 rounded-lg p-5 hover:shadow-lg hover:border-blue-300 transition-all cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="text-slate-900 mb-1">{quiz.title}</h3>
                      <p className="text-sm text-slate-600">{quiz.theme}</p>
                    </div>
                    {quiz.ownerId === currentUserId && (
                      <Badge variant="secondary" className="bg-blue-50 text-blue-700 border-blue-200">
                        <User className="w-3 h-3 mr-1" />
                        Owner
                      </Badge>
                    )}
                    {quiz.ownerId !== currentUserId && canEdit(quiz) && (
                      <Badge variant="secondary" className="bg-green-50 text-green-700 border-green-200">
                        Editor
                      </Badge>
                    )}
                    {quiz.ownerId !== currentUserId && !canEdit(quiz) && (
                      <Badge variant="secondary" className="bg-slate-50 text-slate-600 border-slate-200">
                        <Users className="w-3 h-3 mr-1" />
                        Watcher
                      </Badge>
                    )}
                  </div>

                  <div className="flex items-center gap-2 mb-4 flex-wrap">
                    {quiz.questionTypes.map((type, index) => (
                      <Badge key={index} className="bg-purple-50 text-purple-700 border border-purple-200">
                        {getTypeLabel(type)}
                      </Badge>
                    ))}
                    {statusLabel && (
                      <Badge className={getStatusBadgeColor(quiz.status)}>
                        {statusLabel}
                      </Badge>
                    )}
                    <span className="text-xs text-slate-500">
                      {quiz.questionCount} Fragen
                    </span>
                  </div>

                  <div className="flex items-center text-xs text-slate-500 pt-3 border-t border-slate-100">
                    <Clock className="w-3 h-3 mr-1" />
                    Erstellt: {formatDate(quiz.createdAt)}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
