import { ArrowLeft, Play, Edit, CheckCircle, XCircle, Clock, Trash2, Share2 } from 'lucide-react';
import { Button } from '../../../shared/ui/button';
import { Badge } from '../../../shared/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../../../shared/ui/alert-dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../../shared/ui/table';
import type { Quiz } from '../entities/quiz/types';
import type { QuizAttempt } from '../entities/attempt/types';
import type { QuestionType } from '../entities/question/types';

type EvaluationAnswerDetail = {
  taskId: string;
  label: string;
  type: QuestionType;
  percentage: number;
};

type EvaluationSummary = {
  attemptId: string;
  totalPercentage: number;
  evaluatedAt: Date;
  answers: EvaluationAnswerDetail[];
};

const formatDateTime = (date: Date) => {
  return new Intl.DateTimeFormat('de-DE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

interface QuizDetailViewProps {
  quiz: Quiz;
  attempts: QuizAttempt[];
  currentUserId: string;
  evaluationSummary?: EvaluationSummary | null;
  canManageShareLinks: boolean;
  onManageShareLinks: () => void;
  onBack: () => void;
  onStartAttempt: () => void;
  onReviewAttempt: (attemptId: string) => void;
  onEditQuiz: () => void;
  onDeleteQuiz: () => void;
}

export function QuizDetailView({
  quiz,
  attempts,
  currentUserId,
  evaluationSummary,
  canManageShareLinks,
  onManageShareLinks,
  onBack,
  onStartAttempt,
  onReviewAttempt,
  onEditQuiz,
  onDeleteQuiz,
}: QuizDetailViewProps) {
  const canEdit = quiz.ownerId === currentUserId || quiz.editors.includes(currentUserId);
  const canDelete = quiz.role === 'owner' || quiz.ownerId === currentUserId;
  const isReady = !quiz.status || quiz.status === 'completed';
  const isFailed = quiz.status === 'failed';

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
        return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  const formatDuration = (start: Date, end: Date | null) => {
    if (!end) return '-';
    const durationMs = end.getTime() - start.getTime();
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getScoreBadgeColor = (score: number | null) => {
    if (score === null) return 'bg-slate-100 text-slate-600';
    if (score >= 90) return 'bg-green-100 text-green-700';
    if (score >= 70) return 'bg-blue-100 text-blue-700';
    if (score >= 50) return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  const userAttempts = attempts.filter(a => a.userId === currentUserId);
  const bestScore = userAttempts.reduce((max, attempt) => {
    return attempt.score !== null && attempt.score > max ? attempt.score : max;
  }, 0);
  const statusLabel = getStatusLabel(quiz.status);
  const evaluationDetails = evaluationSummary?.answers ?? [];

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
        <Button
          onClick={onBack}
          variant="ghost"
          className="mb-4 -ml-2 text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Zurück zur Übersicht
        </Button>

        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <h2 className="text-slate-900 text-[28px] mb-2">{quiz.title}</h2>
            <p className="text-slate-600 mb-4">{quiz.theme}</p>
            <div className="flex items-center gap-3 flex-wrap">
              {quiz.questionTypes.map((type, index) => (
                <Badge key={index} className="bg-purple-50 text-purple-700 border border-purple-200">
                  {getTypeLabel(type)}
                </Badge>
              ))}
              {statusLabel && (
                <Badge className={getStatusBadgeColor(quiz.status)}>
                  Status: {statusLabel}
                </Badge>
              )}
              <span className="text-sm text-slate-600">
                {quiz.questionCount} Fragen
              </span>
              {bestScore > 0 && (
                <Badge className={getScoreBadgeColor(bestScore)}>
                  Beste Punktzahl: {bestScore}%
                </Badge>
              )}
            </div>
          </div>

          <div className="flex gap-2">
            {canManageShareLinks && (
              <Button
                onClick={onManageShareLinks}
                variant="outline"
                className="border-slate-300 hover:bg-slate-50"
              >
                <Share2 className="w-4 h-4 mr-2" />
                Quiz teilen
              </Button>
            )}
            {canEdit && (
              <Button
                onClick={onEditQuiz}
                variant="outline"
                disabled={!isReady}
                className="border-slate-300 hover:bg-slate-50"
              >
                <Edit className="w-4 h-4 mr-2" />
                Quiz bearbeiten
              </Button>
            )}
            {canDelete && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    className="border-red-200 text-red-600 hover:bg-red-50 hover:text-red-700"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Quiz loeschen
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Quiz loeschen?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Das Quiz und alle zugehoerigen Aufgaben werden dauerhaft entfernt.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Abbrechen</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={onDeleteQuiz}
                      className="bg-red-600 hover:bg-red-700 text-white"
                    >
                      Endgueltig loeschen
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
            <Button
              onClick={onStartAttempt}
              disabled={!isReady}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Play className="w-4 h-4 mr-2" />
              Neuen Versuch starten
            </Button>
          </div>
        </div>

        {!isReady && (
          <div
            className={`mt-4 rounded-lg border p-4 text-sm ${
              isFailed
                ? 'bg-red-50 border-red-200 text-red-700'
                : 'bg-yellow-50 border-yellow-200 text-yellow-800'
            }`}
          >
            {isFailed
              ? 'Die Generierung ist fehlgeschlagen. Bitte erstellen Sie das Quiz erneut.'
              : 'Das Quiz wird gerade generiert. Aktionen sind nach Abschluss verfuegbar.'}
          </div>
        )}
      </div>

      {evaluationSummary && (
        <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h3 className="text-slate-900 text-[20px] mb-1">Letzte Auswertung</h3>
              <p className="text-sm text-slate-600">
                Ausgewertet am {formatDateTime(evaluationSummary.evaluatedAt)}
              </p>
            </div>
            <Badge className={getScoreBadgeColor(evaluationSummary.totalPercentage)}>
              Gesamt: {Math.round(evaluationSummary.totalPercentage)}%
            </Badge>
          </div>

          {evaluationDetails.length === 0 ? (
            <p className="text-sm text-slate-500">Keine Detaildaten verfuegbar.</p>
          ) : (
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50">
                    <TableHead className="text-slate-700">Frage</TableHead>
                    <TableHead className="text-slate-700">Typ</TableHead>
                    <TableHead className="text-slate-700">Ergebnis</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {evaluationDetails.map((detail) => (
                    <TableRow key={detail.taskId} className="hover:bg-slate-50">
                      <TableCell className="text-slate-900">{detail.label}</TableCell>
                      <TableCell className="text-sm text-slate-600">
                        {getTypeLabel(detail.type)}
                      </TableCell>
                      <TableCell>
                        <Badge className={getScoreBadgeColor(detail.percentage)}>
                          {Math.round(detail.percentage)}%
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      )}

      {/* Attempts Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
        <h3 className="text-slate-900 text-[20px] mb-6">Meine Versuche</h3>

        {userAttempts.length === 0 ? (
          <div className="text-center py-12 bg-slate-50 rounded-lg border-2 border-dashed border-slate-200">
            <Play className="w-12 h-12 mx-auto text-slate-400 mb-4" />
            <h4 className="text-slate-900 mb-2">Noch keine Versuche</h4>
            <p className="text-slate-500 mb-6">
              Starten Sie Ihren ersten Versuch, um Ihr Wissen zu testen
            </p>
            <Button
              onClick={onStartAttempt}
              disabled={!isReady}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Play className="w-4 h-4 mr-2" />
              Ersten Versuch starten
            </Button>
          </div>
        ) : (
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="text-slate-700">#</TableHead>
                  <TableHead className="text-slate-700">Gestartet</TableHead>
                  <TableHead className="text-slate-700">Abgeschlossen</TableHead>
                  <TableHead className="text-slate-700">Dauer</TableHead>
                  <TableHead className="text-slate-700">Ergebnis</TableHead>
                  <TableHead className="text-slate-700">Punktzahl</TableHead>
                  <TableHead className="text-slate-700">Status</TableHead>
                  <TableHead className="text-slate-700">Aktion</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {userAttempts.map((attempt, index) => (
                  <TableRow key={attempt.id} className="hover:bg-slate-50">
                    <TableCell className="text-slate-900">
                      Versuch {userAttempts.length - index}
                    </TableCell>
                    <TableCell className="text-sm text-slate-600">
                      {formatDateTime(attempt.startedAt)}
                    </TableCell>
                    <TableCell className="text-sm text-slate-600">
                      {attempt.completedAt ? formatDateTime(attempt.completedAt) : '-'}
                    </TableCell>
                    <TableCell className="text-sm text-slate-600">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDuration(attempt.startedAt, attempt.completedAt)}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      {attempt.isComplete ? (
                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-1 text-green-600">
                            <CheckCircle className="w-4 h-4" />
                            {attempt.correctAnswers}
                          </div>
                          <div className="flex items-center gap-1 text-red-600">
                            <XCircle className="w-4 h-4" />
                            {attempt.totalQuestions - attempt.correctAnswers}
                          </div>
                        </div>
                      ) : (
                        <span className="text-slate-400">In Bearbeitung</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {attempt.score !== null ? (
                        <Badge className={getScoreBadgeColor(attempt.score)}>
                          {attempt.score}%
                        </Badge>
                      ) : (
                        <span className="text-slate-400 text-sm">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {attempt.isComplete ? (
                        <Badge className="bg-green-50 text-green-700 border-green-200">
                          Abgeschlossen
                        </Badge>
                      ) : (
                        <Badge className="bg-yellow-50 text-yellow-700 border-yellow-200">
                          Laufend
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {attempt.isComplete ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onReviewAttempt(attempt.id)}
                          className="border-slate-300"
                        >
                          Details ansehen
                        </Button>
                      ) : (
                        <span className="text-slate-400 text-sm">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </div>
  );
}


