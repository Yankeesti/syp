import { useCallback, useEffect, useRef, useState } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom';
import { Header } from './layouts/Header';
import { NavigationSidebar } from './layouts/NavigationSidebar';
import { routes } from './routes';
import { QuestionCard, type QuestionAnswer } from '../features/learning/components/QuestionCard';
import { QuestionProgressBar } from '../features/learning/components/QuestionProgressBar';
import { AttemptReviewView, type AttemptReviewItem } from '../features/learning/pages/AttemptReviewView';
import { QuizListView } from '../features/quiz/pages/QuizListView';
import { QuizDetailView } from '../features/quiz/pages/QuizDetailView';
import { ShareLinksView } from '../features/quiz/pages/ShareLinksView';
import { QuizGenerateView } from '../features/quiz/pages/QuizGenerateView';
import { QuizEditView, type PendingChanges } from '../features/quiz/pages/QuizEditView';
import type { Question, QuestionType } from '../features/quiz/entities/question/types';
import type { Quiz } from '../features/quiz/entities/quiz/types';
import { clearAuthToken, clearUserEmail, getTokenPayload, getUserEmail } from '../features/auth/model/tokenStorage';
import { buildApiUrl, requestJson, isApiError } from '../shared/api/client';
import { Button } from '../shared/ui/button';
import { useQuizzes } from '../features/quiz/hooks/useQuizzes';
import { useAttemptFlow } from '../features/learning/hooks/useAttemptFlow';
import {
  useAttemptReviewCache,
  type AttemptReviewData,
  type AttemptReviewStatus,
} from '../features/learning/hooks/useAttemptReviewCache';
import { mapQuestionTypeToTaskType, mapTaskTypeToQuestionType, mapTasksToQuestions, mapQuestionToTaskUpdate } from '../features/quiz/model/mappers';
import {
  createShareLink,
  listShareLinks,
  revokeShareLink,
} from '../features/quiz/model/shareLinkApi';
import type {
  QuizCreateResponseApi,
  QuizDetailResponseApi,
  QuizEditSessionStartResponseApi,
  ShareLinkApi,
} from '../features/quiz/model/types';
import type {
  AttemptListItemApi,
  EvaluationResponseApi,
  ExistingAnswerApi,
} from '../features/learning/model/types';

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

const parsePercentage = (value: number | string | null | undefined) => {
  const parsed = typeof value === 'string' ? Number(value) : value ?? 0;
  return Number.isFinite(parsed) ? parsed : 0;
};

const isSameNumberSet = (left: number[], right: number[]) => {
  if (left.length !== right.length) {
    return false;
  }
  const rightSet = new Set(right);
  return left.every((value) => rightSet.has(value));
};

const matchesPattern = (pattern: string, value: string) => {
  if (!value) {
    return false;
  }
  try {
    const regex = new RegExp(`^(?:${pattern})$`);
    return regex.test(value);
  } catch {
    return pattern === value;
  }
};

const buildAttemptReviewItems = (
  questions: Question[],
  answers: ExistingAnswerApi[],
): AttemptReviewItem[] => {
  const answersByTaskId = answers.reduce<Record<string, ExistingAnswerApi>>((acc, answer) => {
    acc[answer.task_id] = answer;
    return acc;
  }, {});

  return questions.map((question) => {
    const answer = answersByTaskId[question.id];

    if (question.type === 'multiple-choice') {
      const mcAnswer = answer?.type === 'multiple_choice' ? answer : null;
      const selectedIndexes =
        mcAnswer && question.optionIds?.length
          ? mcAnswer.data.selected_option_ids
              .map((optionId) => question.optionIds?.indexOf(optionId) ?? -1)
              .filter((index) => index >= 0)
          : [];
      const answerPercentage = mcAnswer ? parsePercentage(mcAnswer.percentage_correct) : 0;
      const isCorrect =
        mcAnswer && mcAnswer.percentage_correct !== undefined
          ? answerPercentage >= 100
          : isSameNumberSet(selectedIndexes, question.correctAnswers);

      return {
        id: question.id,
        type: 'multiple-choice',
        prompt: question.question,
        theme: question.theme,
        isCorrect,
        options: question.options,
        correctIndexes: question.correctAnswers,
        selectedIndexes,
      };
    }

    if (question.type === 'freitext') {
      const textAnswer = answer?.type === 'free_text' ? answer : null;
      const answerPercentage = textAnswer ? parsePercentage(textAnswer.percentage_correct) : 0;

      return {
        id: question.id,
        type: 'freitext',
        prompt: question.question,
        theme: question.theme,
        isCorrect: textAnswer ? answerPercentage >= 100 : false,
        userText: textAnswer?.data.text_response ?? '',
        solution: question.solution,
      };
    }

    const clozeAnswer = answer?.type === 'cloze' ? answer : null;
    const blankIds = question.blankIds ?? [];
    const userWords = question.correctWords.map((_, index) => {
      const blankId = blankIds[index];
      if (!blankId || !clozeAnswer) {
        return '';
      }
      const match = clozeAnswer.data.provided_values.find((item) => item.blank_id === blankId);
      return match?.value ?? '';
    });
    const perBlankCorrect = question.correctWords.map((pattern, index) => {
      const value = userWords[index] ?? '';
      return matchesPattern(pattern, value);
    });

    return {
      id: question.id,
      type: 'lueckentext',
      prompt: question.textParts.join(' ___ '),
      theme: question.theme,
      isCorrect: perBlankCorrect.length > 0 && perBlankCorrect.every(Boolean),
      textParts: question.textParts,
      userWords,
      correctWords: question.correctWords,
      perBlankCorrect,
    };
  });
};

const readUserIdFromToken = () => {
  const payload = getTokenPayload();
  if (!payload || typeof payload !== 'object') {
    return 'unknown';
  }
  const value = (payload as { user_id?: unknown }).user_id;
  if (typeof value === 'string') {
    return value;
  }
  if (value) {
    return String(value);
  }
  return 'unknown';
};

type QuizHomeProps = {
  onBrowseQuizzes: () => void;
  onCreateQuiz: () => void;
};

function QuizHome({ onBrowseQuizzes, onCreateQuiz }: QuizHomeProps) {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm text-center">
        <h2 className="mb-2 text-slate-900 text-[24px]">Willkommen beim KI-Tutor</h2>
        <p className="text-slate-600 mb-6">
          Erstellen Sie intelligente Quizze mit KI-Unterstützung oder wählen Sie aus Ihren vorhandenen Quizzen
        </p>
        <div className="flex gap-4 justify-center">
          <button
            onClick={onBrowseQuizzes}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Zu meinen Quizzen
          </button>
          <button
            onClick={onCreateQuiz}
            className="px-6 py-3 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
          >
            Neues Quiz erstellen
          </button>
        </div>
      </div>
    </div>
  );
}

function parseQuizId(value?: string) {
  if (typeof value !== 'string') {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function parseAttemptId(value?: string) {
  if (typeof value !== 'string') {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

type QuizDetailStatus = 'loading' | 'loaded' | 'error';
type ShareLinkStatus = 'idle' | 'loading' | 'loaded' | 'error';

type QuizDetailRouteProps = {
  quizzes: Quiz[];
  quizDetailsById: Record<string, QuizDetailResponseApi | null>;
  quizDetailStatusById: Record<string, QuizDetailStatus>;
  quizQuestions: Record<string, Question[]>;
  attemptsByQuizId: Record<string, AttemptListItemApi[]>;
  evaluationByAttemptId: Record<string, EvaluationResponseApi>;
  currentUserId: string;
  loadQuizDetail: (
    quizId: string,
  ) => Promise<{ detail: QuizDetailResponseApi; questions: Question[] } | null>;
  loadAttemptsForQuiz: (quizId: string) => Promise<void>;
  scheduleQuizPoll: (quizId: string) => void;
  clearQuizPoll: (quizId: string) => void;
  handleStartAttempt: (quizId: string) => void;
  handleDeleteQuiz: (quizId: string) => void;
};

function QuizDetailRoute({
  quizzes,
  quizDetailsById,
  quizDetailStatusById,
  quizQuestions,
  attemptsByQuizId,
  evaluationByAttemptId,
  currentUserId,
  loadQuizDetail,
  loadAttemptsForQuiz,
  scheduleQuizPoll,
  clearQuizPoll,
  handleStartAttempt,
  handleDeleteQuiz,
}: QuizDetailRouteProps) {
  const navigate = useNavigate();
  const { quizId } = useParams();
  const id = parseQuizId(quizId);

  useEffect(() => {
    if (!id) return;
    let isActive = true;

    const run = async () => {
      const result = await loadQuizDetail(id);
      if (!isActive || !result) {
        return;
      }
      if (result.detail.status === 'pending' || result.detail.status === 'generating') {
        scheduleQuizPoll(id);
      } else {
        clearQuizPoll(id);
      }
    };

    void run();
    void loadAttemptsForQuiz(id);

    return () => {
      isActive = false;
      clearQuizPoll(id);
    };
  }, [id, loadQuizDetail, loadAttemptsForQuiz, scheduleQuizPoll, clearQuizPoll]);

  const detail = id ? quizDetailsById[id] : null;
  const selectedQuiz = id ? quizzes.find((quiz) => quiz.id === id) : undefined;
  const detailTasks = detail && Array.isArray(detail.tasks) ? detail.tasks : [];
  const questions = id
    ? quizQuestions[id] ?? (detail ? mapTasksToQuestions(detailTasks) : [])
    : [];
  const questionCount =
    questions.length || detailTasks.length || selectedQuiz?.questionCount || 0;

  const questionTypes =
    selectedQuiz?.questionTypes?.length
      ? selectedQuiz.questionTypes
      : detail
        ? Array.from(new Set(detailTasks.map((task) => mapTaskTypeToQuestionType(task.type))))
        : [];

  const viewQuiz: Quiz | undefined = detail
    ? {
        id: detail.quiz_id,
        title: detail.title,
        theme: detail.topic ?? selectedQuiz?.theme ?? detail.title,
        ownerId: selectedQuiz?.ownerId ?? detail.created_by,
        questionCount,
        questionTypes,
        createdAt: new Date(detail.created_at),
        watchers: selectedQuiz?.watchers ?? [],
        editors: selectedQuiz?.editors ?? [],
        status: detail.status,
        state: detail.state,
        role: selectedQuiz?.role,
      }
    : selectedQuiz;

  const canManageShareLinks = Boolean(
    viewQuiz &&
      (viewQuiz.role === 'owner' ||
        viewQuiz.role === 'editor' ||
        viewQuiz.ownerId === currentUserId ||
        viewQuiz.editors.includes(currentUserId)),
  );

  if (id === null) {
    return <Navigate to={routes.quiz.list} replace />;
  }

  if (!viewQuiz) {
    const status = quizDetailStatusById[id];
    if (status === 'error') {
      return <Navigate to={routes.quiz.list} replace />;
    }
    return (
      <div className="max-w-5xl mx-auto text-slate-600">
        Quiz wird geladen...
      </div>
    );
  }

  const rawAttempts = attemptsByQuizId[id] ?? [];
  const quizAttempts = rawAttempts.map((attempt) => {
    const score =
      attempt.total_percentage !== null ? Number(attempt.total_percentage) : null;
    const isComplete = attempt.status === 'evaluated';
    const correctAnswers =
      score !== null && questionCount > 0
        ? Math.round((score / 100) * questionCount)
        : 0;

    return {
      id: attempt.attempt_id,
      quizId: attempt.quiz_id,
      userId: currentUserId,
      startedAt: new Date(attempt.started_at),
      completedAt: attempt.evaluated_at ? new Date(attempt.evaluated_at) : null,
      score,
      correctAnswers: isComplete ? correctAnswers : 0,
      totalQuestions: questionCount,
      isComplete,
    };
  });

  const questionMetaById = questions.reduce<
    Record<string, { order: number; label: string; type: QuestionType }>
  >((acc, question, index) => {
    acc[question.id] = {
      order: index,
      label: `Frage ${index + 1}`,
      type: question.type,
    };
    return acc;
  }, {});

  const latestEvaluatedAttempt = rawAttempts.find(
    (attempt) =>
      attempt.status === 'evaluated' &&
      Boolean(evaluationByAttemptId[attempt.attempt_id]),
  );

  const evaluationPayload = latestEvaluatedAttempt
    ? evaluationByAttemptId[latestEvaluatedAttempt.attempt_id]
    : null;

  const evaluationSummary: EvaluationSummary | null = evaluationPayload
    ? {
        attemptId: evaluationPayload.attempt_id,
        totalPercentage: parsePercentage(evaluationPayload.total_percentage),
        evaluatedAt: new Date(evaluationPayload.evaluated_at),
        answers: (Array.isArray(evaluationPayload.answer_details)
          ? evaluationPayload.answer_details
          : []
        )
          .map((detail) => {
            const meta = questionMetaById[detail.task_id];
            const type = meta?.type ?? mapTaskTypeToQuestionType(detail.type);
            const label = meta?.label ?? 'Frage';
            const order = meta?.order ?? Number.MAX_SAFE_INTEGER;
            return {
              taskId: detail.task_id,
              type,
              label,
              percentage: parsePercentage(detail.percentage_correct),
              order,
            };
          })
          .sort((a, b) => a.order - b.order)
          .map(({ order, ...rest }) => rest),
      }
    : null;

  return (
    <QuizDetailView
      quiz={viewQuiz}
      attempts={quizAttempts}
      currentUserId={currentUserId}
      evaluationSummary={evaluationSummary}
      onBack={() => navigate(routes.quiz.list)}
      onStartAttempt={() => handleStartAttempt(id)}
      onReviewAttempt={(attemptId) => navigate(routes.quiz.attemptReview(id, attemptId))}
      onEditQuiz={() => navigate(routes.quiz.edit(id))}
      onDeleteQuiz={() => handleDeleteQuiz(id)}
      canManageShareLinks={canManageShareLinks}
      onManageShareLinks={() => navigate(routes.quiz.shareLinks(id))}
    />
  );
}

type ShareLinksRouteProps = {
  quizzes: Quiz[];
  quizDetailsById: Record<string, QuizDetailResponseApi | null>;
  quizDetailStatusById: Record<string, QuizDetailStatus>;
  currentUserId: string;
  loadQuizDetail: (
    quizId: string,
  ) => Promise<{ detail: QuizDetailResponseApi; questions: Question[] } | null>;
};

function ShareLinksRoute({
  quizzes,
  quizDetailsById,
  quizDetailStatusById,
  currentUserId,
  loadQuizDetail,
}: ShareLinksRouteProps) {
  const navigate = useNavigate();
  const { quizId } = useParams();
  const id = parseQuizId(quizId);
  const [shareLinks, setShareLinks] = useState<ShareLinkApi[]>([]);
  const [shareLinkStatus, setShareLinkStatus] = useState<ShareLinkStatus>('idle');
  const [shareLinkError, setShareLinkError] = useState<string | null>(null);
  const [isCreatingShareLink, setIsCreatingShareLink] = useState(false);
  const [revokingShareLinkId, setRevokingShareLinkId] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    void loadQuizDetail(id);
  }, [id, loadQuizDetail]);

  const detail = id ? quizDetailsById[id] : null;
  const selectedQuiz = id ? quizzes.find((quiz) => quiz.id === id) : undefined;
  const detailTasks = detail && Array.isArray(detail.tasks) ? detail.tasks : [];
  const questionTypes =
    selectedQuiz?.questionTypes?.length
      ? selectedQuiz.questionTypes
      : detail
        ? Array.from(new Set(detailTasks.map((task) => mapTaskTypeToQuestionType(task.type))))
        : [];
  const questionCount = detailTasks.length || selectedQuiz?.questionCount || 0;

  const viewQuiz: Quiz | undefined = detail
    ? {
        id: detail.quiz_id,
        title: detail.title,
        theme: detail.topic ?? selectedQuiz?.theme ?? detail.title,
        ownerId: selectedQuiz?.ownerId ?? detail.created_by,
        questionCount,
        questionTypes,
        createdAt: new Date(detail.created_at),
        watchers: selectedQuiz?.watchers ?? [],
        editors: selectedQuiz?.editors ?? [],
        status: detail.status,
        state: detail.state,
        role: selectedQuiz?.role,
      }
    : selectedQuiz;

  const canManageShareLinks = Boolean(
    viewQuiz &&
      (viewQuiz.role === 'owner' ||
        viewQuiz.role === 'editor' ||
        viewQuiz.ownerId === currentUserId ||
        viewQuiz.editors.includes(currentUserId)),
  );

  const loadShareLinks = useCallback(async () => {
    if (!id) {
      return;
    }
    setShareLinkStatus('loading');
    setShareLinkError(null);

    try {
      const links = await listShareLinks(id);
      setShareLinks(links);
      setShareLinkStatus('loaded');
    } catch (error) {
      setShareLinkStatus('error');
      if (isApiError(error)) {
        if (error.status === 403) {
          setShareLinkError('Keine Berechtigung fuer Share-Links.');
        } else if (error.status === 404) {
          setShareLinkError('Quiz wurde nicht gefunden.');
        } else {
          setShareLinkError(error.message);
        }
      } else {
        setShareLinkError('Share-Links konnten nicht geladen werden.');
      }
    }
  }, [id]);

  const handleCreateShareLink = useCallback(
    async (payload: { durationSeconds: number | null; maxUses: number | null }) => {
      if (!id) {
        return false;
      }
      setIsCreatingShareLink(true);
      setShareLinkError(null);

      try {
        const body = {
          ...(payload.durationSeconds !== null ? { duration: payload.durationSeconds } : {}),
          ...(payload.maxUses !== null ? { max_uses: payload.maxUses } : {}),
        };
        await createShareLink(id, body);
        await loadShareLinks();
        return true;
      } catch (error) {
        setShareLinkStatus('error');
        if (isApiError(error)) {
          if (error.status === 403) {
            setShareLinkError('Keine Berechtigung fuer Share-Links.');
          } else if (error.status === 404) {
            setShareLinkError('Quiz wurde nicht gefunden.');
          } else {
            setShareLinkError(error.message);
          }
        } else {
          setShareLinkError('Share-Link konnte nicht erstellt werden.');
        }
        return false;
      } finally {
        setIsCreatingShareLink(false);
      }
    },
    [id, loadShareLinks],
  );

  const handleRevokeShareLink = useCallback(
    async (shareLinkId: string) => {
      if (!id) {
        return;
      }
      setRevokingShareLinkId(shareLinkId);
      setShareLinkError(null);

      try {
        await revokeShareLink(id, shareLinkId);
        setShareLinks((prev) =>
          prev.map((link) =>
            link.share_link_id === shareLinkId ? { ...link, is_active: false } : link,
          ),
        );
      } catch (error) {
        setShareLinkStatus('error');
        if (isApiError(error)) {
          if (error.status === 403) {
            setShareLinkError('Keine Berechtigung fuer Share-Links.');
          } else if (error.status === 404) {
            setShareLinkError('Share-Link wurde nicht gefunden.');
          } else {
            setShareLinkError(error.message);
          }
        } else {
          setShareLinkError('Share-Link konnte nicht widerrufen werden.');
        }
      } finally {
        setRevokingShareLinkId(null);
      }
    },
    [id],
  );

  useEffect(() => {
    if (!id || !canManageShareLinks) {
      setShareLinks([]);
      setShareLinkStatus('idle');
      setShareLinkError(null);
      return;
    }
    setShareLinks([]);
    setShareLinkStatus('idle');
    setShareLinkError(null);
  }, [id, canManageShareLinks]);

  if (id === null) {
    return <Navigate to={routes.quiz.list} replace />;
  }

  if (!viewQuiz) {
    const status = quizDetailStatusById[id];
    if (status === 'error') {
      return <Navigate to={routes.quiz.list} replace />;
    }
    return (
      <div className="max-w-5xl mx-auto text-slate-600">
        Quiz wird geladen...
      </div>
    );
  }

  if (!canManageShareLinks) {
    return (
      <div className="max-w-5xl mx-auto space-y-4 text-slate-600">
        <p>Keine Berechtigung fuer Share-Links.</p>
        <Button onClick={() => navigate(routes.quiz.detail(id))} variant="outline">
          Zurueck zum Quiz
        </Button>
      </div>
    );
  }

  return (
    <ShareLinksView
      quizTitle={viewQuiz.title}
      quizTheme={viewQuiz.theme}
      links={shareLinks}
      status={shareLinkStatus}
      error={shareLinkError}
      isCreating={isCreatingShareLink}
      revokingId={revokingShareLinkId}
      onCreate={handleCreateShareLink}
      onRevoke={handleRevokeShareLink}
      onRefresh={loadShareLinks}
      onBack={() => navigate(routes.quiz.detail(id))}
    />
  );
}

type QuizEditRouteProps = {
  quizzes: Quiz[];
  handleSaveQuiz: (
    quizId: string,
    editSessionId: string,
    changes: PendingChanges,
  ) => Promise<void>;
};

function QuizEditRoute({
  quizzes,
  handleSaveQuiz,
}: QuizEditRouteProps) {
  const navigate = useNavigate();
  const { quizId } = useParams();
  const id = parseQuizId(quizId);
  const [editSessionId, setEditSessionId] = useState<string | null>(null);
  const [draftDetail, setDraftDetail] = useState<QuizDetailResponseApi | null>(null);
  const [editSessionStatus, setEditSessionStatus] = useState<
    'idle' | 'loading' | 'loaded' | 'error'
  >('idle');
  const [editSessionError, setEditSessionError] = useState<string | null>(null);
  const sessionFinalizedRef = useRef(false);
  const sessionIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let isActive = true;
    sessionFinalizedRef.current = false;
    sessionIdRef.current = null;
    setEditSessionStatus('loading');
    setEditSessionError(null);
    setDraftDetail(null);
    setEditSessionId(null);

    const startSession = async () => {
      try {
        const response = await requestJson<QuizEditSessionStartResponseApi>(
          buildApiUrl(`/quiz/quizzes/${id}/edit/start`),
          { method: 'POST' },
        );
        if (!isActive) return;
        setEditSessionId(response.edit_session_id);
        sessionIdRef.current = response.edit_session_id;
        setDraftDetail(response.quiz);
        setEditSessionStatus('loaded');
      } catch (error) {
        if (!isActive) return;
        console.error('Failed to start edit session', error);
        const fallback = 'Edit-Session konnte nicht gestartet werden.';
        const message = isApiError(error)
          ? error.detail ?? error.message ?? fallback
          : error instanceof Error
            ? error.message
            : fallback;
        setEditSessionError(message);
        setEditSessionStatus('error');
      }
    };

    void startSession();

    return () => {
      isActive = false;
    };
  }, [id]);

  useEffect(() => {
    return () => {
      if (id === null || sessionFinalizedRef.current) {
        return;
      }
      const activeSessionId = sessionIdRef.current;
      if (!activeSessionId) {
        return;
      }
      void requestJson(buildApiUrl(`/quiz/quizzes/${id}/edit/abort`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ edit_session_id: activeSessionId }),
      }).catch((error) => {
        console.error('Failed to abort edit session on exit', error);
      });
    };
  }, [id]);

  if (id === null) {
    return <Navigate to={routes.quiz.list} replace />;
  }

  const selectedQuiz = quizzes.find((quiz) => quiz.id === id);
  const detailTasks = draftDetail && Array.isArray(draftDetail.tasks) ? draftDetail.tasks : [];
  const questions = draftDetail ? mapTasksToQuestions(detailTasks) : [];

  if (editSessionStatus === 'loading' || editSessionStatus === 'idle') {
    return (
      <div className="max-w-5xl mx-auto text-slate-600">
        Edit-Session wird vorbereitet...
      </div>
    );
  }

  if (editSessionStatus === 'error') {
    return (
      <div className="max-w-5xl mx-auto space-y-4">
        <div className="text-slate-900 text-lg font-semibold">Bearbeitung nicht moeglich</div>
        <p className="text-slate-600">{editSessionError ?? 'Unbekannter Fehler.'}</p>
        <Button onClick={() => navigate(routes.quiz.detail(id))} variant="ghost">
          Zurueck zur Detailansicht
        </Button>
      </div>
    );
  }

  const viewQuiz: Quiz | undefined = draftDetail
    ? {
        id: draftDetail.quiz_id,
        title: draftDetail.title,
        theme: draftDetail.topic ?? selectedQuiz?.theme ?? draftDetail.title,
        ownerId: selectedQuiz?.ownerId ?? draftDetail.created_by,
        questionCount: questions.length,
        questionTypes: selectedQuiz?.questionTypes ?? [],
        createdAt: new Date(draftDetail.created_at),
        watchers: selectedQuiz?.watchers ?? [],
        editors: selectedQuiz?.editors ?? [],
        status: draftDetail.status,
        state: draftDetail.state,
        role: selectedQuiz?.role,
      }
    : selectedQuiz;

  if (!viewQuiz) {
    return (
      <div className="max-w-5xl mx-auto text-slate-600">
        Quiz wird geladen...
      </div>
    );
  }

  if (viewQuiz.status && viewQuiz.status !== 'completed') {
    return <Navigate to={routes.quiz.detail(id)} replace />;
  }

  return (
    <QuizEditView
      quizId={viewQuiz.id}
      quizTitle={viewQuiz.title}
      quizTheme={viewQuiz.theme}
      questions={questions}
      onSave={async (changes) => {
        if (!editSessionId) {
          throw new Error('Edit-Session ist nicht verfuegbar.');
        }
        await handleSaveQuiz(id, editSessionId, changes);
        sessionFinalizedRef.current = true;
        navigate(routes.quiz.detail(id));
      }}
      onBack={async () => {
        let didAbort = false;
        if (editSessionId) {
          try {
            await requestJson(buildApiUrl(`/quiz/quizzes/${id}/edit/abort`), {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ edit_session_id: editSessionId }),
            });
            didAbort = true;
          } catch (error) {
            console.error('Failed to abort edit session', error);
          }
        } else {
          didAbort = true;
        }
        if (didAbort) {
          sessionFinalizedRef.current = true;
        }
        navigate(routes.quiz.detail(id));
      }}
    />
  );
}

type QuizAttemptRouteProps = {
  activeQuizId: string | null;
  currentQuestions: Question[];
  currentQuestionIndex: number;
  isAttemptComplete: boolean;
  answeredQuestionIds: string[];
  handleAnswerQuestion: (answer: QuestionAnswer) => void;
  handleCancelAttempt: () => void;
  handlePreviousQuestion: () => void;
  handleNextQuestion: () => void;
  handleGoToQuestion: (index: number) => void;
  saveTemporaryAnswer: (questionId: string, answer: QuestionAnswer) => void;
  getTemporaryAnswer: (questionId: string) => QuestionAnswer | undefined;
};

function QuizAttemptRoute({
  activeQuizId,
  currentQuestions,
  currentQuestionIndex,
  isAttemptComplete,
  answeredQuestionIds,
  handleAnswerQuestion,
  handleCancelAttempt,
  handlePreviousQuestion,
  handleNextQuestion,
  handleGoToQuestion,
  saveTemporaryAnswer,
  getTemporaryAnswer,
}: QuizAttemptRouteProps) {
  const { quizId } = useParams();
  const id = parseQuizId(quizId);
  if (id === null) {
    return <Navigate to={routes.quiz.list} replace />;
  }

  if (activeQuizId !== id || currentQuestions.length === 0) {
    return <Navigate to={routes.quiz.detail(id)} replace />;
  }

  const currentQuestion = currentQuestions[currentQuestionIndex];
  const isAnswerSaved = answeredQuestionIds.includes(currentQuestion.id);

  const handleQuestionClick = (index: number) => {
    // Navigate directly to the clicked question
    handleGoToQuestion(index);
  };

  return (
    <div className="max-w-5xl mx-auto">
      <QuestionProgressBar
        questions={currentQuestions}
        currentQuestionIndex={currentQuestionIndex}
        answeredQuestionIds={answeredQuestionIds}
        onQuestionClick={handleQuestionClick}
      />
      <QuestionCard
        question={currentQuestion}
        questionNumber={currentQuestionIndex + 1}
        totalQuestions={currentQuestions.length}
        onAnswer={handleAnswerQuestion}
        onCancel={handleCancelAttempt}
        onPrevious={handlePreviousQuestion}
        onNext={handleNextQuestion}
        onSaveTemporary={saveTemporaryAnswer}
        onLoadTemporary={getTemporaryAnswer}
        isAnswerSaved={isAnswerSaved}
        isComplete={isAttemptComplete}
      />
    </div>
  );
}

type AttemptReviewRouteProps = {
  quizzes: Quiz[];
  quizDetailsById: Record<string, QuizDetailResponseApi | null>;
  attemptReviewsById: Record<string, AttemptReviewData>;
  attemptReviewStatusById: Record<string, AttemptReviewStatus>;
  attemptReviewErrorById: Record<string, string | null>;
  loadAttemptReview: (attemptId: string) => Promise<AttemptReviewData | null>;
};

function AttemptReviewRoute({
  quizzes,
  quizDetailsById,
  attemptReviewsById,
  attemptReviewStatusById,
  attemptReviewErrorById,
  loadAttemptReview,
}: AttemptReviewRouteProps) {
  const navigate = useNavigate();
  const { quizId, attemptId } = useParams();
  const id = parseQuizId(quizId);
  const attempt = parseAttemptId(attemptId);

  useEffect(() => {
    if (!attempt) return;
    void loadAttemptReview(attempt);
  }, [attempt, loadAttemptReview]);

  if (id === null || attempt === null) {
    return <Navigate to={routes.quiz.list} replace />;
  }

  const reviewData = attemptReviewsById[attempt];
  const attemptStatus = reviewData
    ? 'loaded'
    : attemptReviewStatusById[attempt] ?? 'idle';
  const attemptError = attemptReviewErrorById[attempt] ?? null;

  const detail = quizDetailsById[id];
  const selectedQuiz = quizzes.find((quiz) => quiz.id === id);
  const questions = reviewData?.questions ?? [];

  const viewQuiz: Quiz | undefined = detail
    ? {
        id: detail.quiz_id,
        title: detail.title,
        theme: detail.topic ?? selectedQuiz?.theme ?? detail.title,
        ownerId: selectedQuiz?.ownerId ?? detail.created_by,
        questionCount: questions.length,
        questionTypes: selectedQuiz?.questionTypes ?? [],
        createdAt: new Date(detail.created_at),
        watchers: selectedQuiz?.watchers ?? [],
        editors: selectedQuiz?.editors ?? [],
        status: detail.status,
        state: detail.state,
        role: selectedQuiz?.role,
      }
    : selectedQuiz;

  if (!viewQuiz) {
    if (quizzes.length === 0) {
      return (
        <div className="max-w-5xl mx-auto text-slate-600">
          Quiz wird geladen...
        </div>
      );
    }
    return (
      <div className="max-w-5xl mx-auto space-y-4 text-slate-600">
        <p>Quiz konnte nicht geladen werden.</p>
        <Button onClick={() => navigate(routes.quiz.list)} variant="outline">
          Zurueck zur Uebersicht
        </Button>
      </div>
    );
  }

  if (attemptStatus === 'error') {
    return (
      <div className="max-w-5xl mx-auto space-y-4 text-slate-600">
        <p>{attemptError ?? 'Versuch konnte nicht geladen werden.'}</p>
        <Button onClick={() => navigate(routes.quiz.detail(id))} variant="outline">
          Zurueck zum Quiz
        </Button>
      </div>
    );
  }

  if (!reviewData || attemptStatus === 'loading' || attemptStatus === 'idle') {
    return (
      <div className="max-w-5xl mx-auto text-slate-600">
        Versuch wird geladen...
      </div>
    );
  }

  const reviewItems = buildAttemptReviewItems(
    questions,
    Array.isArray(reviewData.detail.answers) ? reviewData.detail.answers : [],
  );

  return (
    <AttemptReviewView
      quizTitle={viewQuiz.title}
      quizTheme={viewQuiz.theme}
      startedAt={new Date(reviewData.detail.started_at)}
      evaluatedAt={
        reviewData.detail.evaluated_at
          ? new Date(reviewData.detail.evaluated_at)
          : null
      }
      score={
        reviewData.detail.total_percentage !== null
          ? Number(reviewData.detail.total_percentage)
          : null
      }
      items={reviewItems}
      onBack={() => navigate(routes.quiz.detail(id))}
    />
  );
}

export function QuizRoutes() {
  const navigate = useNavigate();
  const location = useLocation();
  const currentPath = location.pathname;
  const currentUserId = readUserIdFromToken();
  const userEmail = getUserEmail() ?? 'student@example.com';

  const {
    quizzes,
    setQuizzes,
    quizDetailsById,
    setQuizDetailsById,
    quizDetailStatusById,
    quizQuestions,
    setQuizQuestions,
    loadQuizzes,
    loadQuizDetail,
    scheduleQuizPoll,
    clearQuizPoll,
    clearAllQuizPolls,
  } = useQuizzes(currentUserId);

  const {
    attemptsByQuizId,
    evaluationByAttemptId,
    activeQuizId,
    currentQuestions,
    currentQuestionIndex,
    isAttemptComplete,
    answeredQuestionIds,
    loadAttemptsForQuiz,
    handleStartAttempt,
    handleAnswerQuestion,
    handleCancelAttempt,
    handlePreviousQuestion,
    handleNextQuestion,
    handleGoToQuestion,
    saveTemporaryAnswer,
    getTemporaryAnswer,
    resetAttemptSession,
    clearAttemptsForQuiz,
    clearAttemptState,
  } = useAttemptFlow({
    quizzes,
    quizQuestions,
    quizDetailsById,
    loadQuizDetail,
    navigate,
  });

  const {
    attemptReviewsById,
    attemptReviewStatusById,
    attemptReviewErrorById,
    loadAttemptReview,
    clearAttemptReviewCache,
  } = useAttemptReviewCache();

  const handleCreateQuiz = () => {
    navigate(routes.quiz.create);
  };

  const handleSelectQuiz = (quizId: string) => {
    navigate(routes.quiz.detail(quizId));
  };

  const handleGenerateQuiz = async (
    prompt: string,
    types: QuestionType[],
    pdfFile?: File,
  ) => {
    if (!prompt.trim() && !pdfFile) return;
    if (types.length === 0) return;

    try {
      const formData = new FormData();
      if (prompt.trim()) {
        formData.append('user_description', prompt.trim());
      }
      if (pdfFile) {
        formData.append('file', pdfFile);
      }

      const url = new URL(buildApiUrl('/quiz/quizzes'));
      types.map(mapQuestionTypeToTaskType).forEach((type) => {
        url.searchParams.append('types', type);
      });

      const created = await requestJson<QuizCreateResponseApi>(url.toString(), {
        method: 'POST',
        body: formData,
      });

      await loadQuizzes();
      navigate(routes.quiz.detail(created.quiz_id));
    } catch (error) {
      console.error('Failed to create quiz', error);
      alert('Quiz konnte nicht erstellt werden.');
    }
  };

  const handleSaveQuiz = async (
    quizId: string,
    editSessionId: string,
    changes: PendingChanges,
  ) => {
    const { questions, deletedIds, updatedQuestions } = changes;

    try {
      // 1. Alle Loeschungen durchfuehren
      const deletePromises = deletedIds.map((questionId) =>
        requestJson(buildApiUrl(`/quiz/tasks/${questionId}`), {
          method: 'DELETE',
          headers: { 'X-Edit-Session-Id': editSessionId },
        })
      );
      await Promise.all(deletePromises);

      // 2. Alle Updates durchfuehren
      const updatePromises = updatedQuestions.map((question) =>
        requestJson(buildApiUrl(`/quiz/tasks/${question.id}`), {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-Edit-Session-Id': editSessionId,
          },
          body: JSON.stringify(mapQuestionToTaskUpdate(question)),
        })
      );
      await Promise.all(updatePromises);

      // 3. Draft committen
      await requestJson(buildApiUrl(`/quiz/quizzes/${quizId}/edit/commit`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ edit_session_id: editSessionId }),
      });

      // 4. Lokalen State aktualisieren
      const updatedQuestionTypes = Array.from(
        new Set(questions.map((question) => question.type)),
      );

      setQuizQuestions((prev) => ({
        ...prev,
        [quizId]: questions,
      }));

      setQuizDetailsById((prev) => {
        const detail = prev[quizId];
        if (!detail || !Array.isArray(detail.tasks)) {
          return prev;
        }
        return {
          ...prev,
          [quizId]: {
            ...detail,
            tasks: detail.tasks.filter((task) => !deletedIds.includes(task.task_id)),
          },
        };
      });

      setQuizzes((prev) =>
        prev.map((quiz) =>
          quiz.id === quizId
            ? {
                ...quiz,
                questionCount: questions.length,
                questionTypes: updatedQuestionTypes,
              }
            : quiz,
        ),
      );

      alert('Quiz erfolgreich gespeichert!');
    } catch (error) {
      console.error('Failed to save quiz changes', error);
      alert('Aenderungen konnten nicht gespeichert werden.');
      throw error; // Re-throw um den Fehler im QuizEditView zu behandeln
    }
  };

  const handleDeleteQuiz = async (quizId: string) => {
    try {
      await requestJson(buildApiUrl(`/quiz/quizzes/${quizId}`), {
        method: 'DELETE',
      });

      setQuizzes((prev) => prev.filter((quiz) => quiz.id !== quizId));
      setQuizDetailsById((prev) => {
        const { [quizId]: removed, ...rest } = prev;
        return rest;
      });
      setQuizQuestions((prev) => {
        const { [quizId]: removed, ...rest } = prev;
        return rest;
      });
      clearAttemptsForQuiz(quizId);

      if (activeQuizId === quizId) {
        clearAttemptState();
      }

      navigate(routes.quiz.list);
    } catch (error) {
      console.error('Failed to delete quiz', error);
      alert('Quiz konnte nicht geloescht werden.');
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    clearUserEmail();
    clearAllQuizPolls();
    resetAttemptSession();
    clearAttemptReviewCache();
    navigate(routes.root);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />
      <div className="flex">
        <NavigationSidebar
          currentPath={currentPath}
          onNavigate={(path) => navigate(path)}
          userEmail={userEmail}
          onLogout={handleLogout}
        />
        <main className="flex-1 p-8">
          <Routes>
            <Route
              index
              element={
                <QuizHome onBrowseQuizzes={() => navigate(routes.quiz.list)} onCreateQuiz={handleCreateQuiz} />
              }
            />
            <Route
              path="quizzes"
              element={
                <QuizListView
                  quizzes={quizzes}
                  currentUserId={currentUserId}
                  onCreateQuiz={handleCreateQuiz}
                  onSelectQuiz={handleSelectQuiz}
                />
              }
            />
            <Route
              path="quizzes/new"
              element={<QuizGenerateView onGenerate={handleGenerateQuiz} onBack={() => navigate(routes.quiz.list)} />}
            />
            <Route
              path="quizzes/:quizId"
              element={
                <QuizDetailRoute
                  quizzes={quizzes}
                  quizDetailsById={quizDetailsById}
                  quizDetailStatusById={quizDetailStatusById}
                  quizQuestions={quizQuestions}
                  attemptsByQuizId={attemptsByQuizId}
                  evaluationByAttemptId={evaluationByAttemptId}
                  currentUserId={currentUserId}
                  loadQuizDetail={loadQuizDetail}
                  loadAttemptsForQuiz={loadAttemptsForQuiz}
                  scheduleQuizPoll={scheduleQuizPoll}
                  clearQuizPoll={clearQuizPoll}
                  handleStartAttempt={handleStartAttempt}
                  handleDeleteQuiz={handleDeleteQuiz}
                />
              }
            />
            <Route
              path="quizzes/:quizId/share-links"
              element={
                <ShareLinksRoute
                  quizzes={quizzes}
                  quizDetailsById={quizDetailsById}
                  quizDetailStatusById={quizDetailStatusById}
                  currentUserId={currentUserId}
                  loadQuizDetail={loadQuizDetail}
                />
              }
            />
            <Route
              path="quizzes/:quizId/edit"
              element={
                <QuizEditRoute
                  quizzes={quizzes}
                  handleSaveQuiz={handleSaveQuiz}
                />
              }
            />
            <Route
              path="quizzes/:quizId/attempt"
              element={
                <QuizAttemptRoute
                  activeQuizId={activeQuizId}
                  currentQuestions={currentQuestions}
                  currentQuestionIndex={currentQuestionIndex}
                  isAttemptComplete={isAttemptComplete}
                  answeredQuestionIds={answeredQuestionIds}
                  handleAnswerQuestion={handleAnswerQuestion}
                  handleCancelAttempt={handleCancelAttempt}
                  handlePreviousQuestion={handlePreviousQuestion}
                  handleNextQuestion={handleNextQuestion}
                  handleGoToQuestion={handleGoToQuestion}
                  saveTemporaryAnswer={saveTemporaryAnswer}
                  getTemporaryAnswer={getTemporaryAnswer}
                />
              }
            />
            <Route
              path="quizzes/:quizId/attempts/:attemptId"
              element={
                <AttemptReviewRoute
                  quizzes={quizzes}
                  quizDetailsById={quizDetailsById}
                  attemptReviewsById={attemptReviewsById}
                  attemptReviewStatusById={attemptReviewStatusById}
                  attemptReviewErrorById={attemptReviewErrorById}
                  loadAttemptReview={loadAttemptReview}
                />
              }
            />
            <Route path="*" element={<Navigate to={routes.quiz.root} replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
