import { useCallback, useState } from 'react';
import { buildApiUrl, requestJson } from '../../../shared/api/client';
import type { Quiz } from '../../quiz/entities/quiz/types';
import type { Question } from '../../quiz/entities/question/types';
import type { QuestionAnswer } from '../components/QuestionCard';
import type { QuizDetailResponseApi } from '../../quiz/model/types';
import type {
  AnswerUpsertRequest,
  AttemptListItemApi,
  AttemptSummaryApi,
  EvaluationResponseApi,
} from '../model/types';
import { routes } from '../../../app/routes';

const findNextUnansweredIndex = (
  questions: Question[],
  startIndex: number,
  answeredIds: Set<string>,
) => {
  for (let index = startIndex; index < questions.length; index += 1) {
    if (!answeredIds.has(questions[index].id)) {
      return index;
    }
  }
  return -1;
};

type UseAttemptFlowOptions = {
  quizzes: Quiz[];
  quizQuestions: Record<string, Question[]>;
  quizDetailsById: Record<string, QuizDetailResponseApi | null>;
  loadQuizDetail: (
    quizId: string,
  ) => Promise<{ detail: QuizDetailResponseApi; questions: Question[] } | null>;
  navigate: (path: string) => void;
};

export const useAttemptFlow = ({
  quizzes,
  quizQuestions,
  quizDetailsById,
  loadQuizDetail,
  navigate,
}: UseAttemptFlowOptions) => {
  const [attemptsByQuizId, setAttemptsByQuizId] = useState<
    Record<string, AttemptListItemApi[]>
  >({});
  const [currentAttemptId, setCurrentAttemptId] = useState<string | null>(null);
  const [activeQuizId, setActiveQuizId] = useState<string | null>(null);
  const [currentQuestions, setCurrentQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isAttemptComplete, setIsAttemptComplete] = useState(false);
  const [answeredQuestionIds, setAnsweredQuestionIds] = useState<string[]>([]);
  const [temporaryAnswers, setTemporaryAnswers] = useState<
    Record<string, QuestionAnswer>
  >({});
  const [evaluationByAttemptId, setEvaluationByAttemptId] = useState<
    Record<string, EvaluationResponseApi>
  >({});

  const loadAttemptsForQuiz = useCallback(async (quizId: string) => {
    try {
      const url = new URL(buildApiUrl('/learning/attempts'));
      url.searchParams.set('quiz_id', quizId);
      const attempts = await requestJson<AttemptListItemApi[]>(url.toString());
      setAttemptsByQuizId((prev) => ({ ...prev, [quizId]: attempts }));
    } catch (error) {
      console.error('Failed to load attempts', error);
    }
  }, []);

  const saveAnswerForQuestion = useCallback(
    async (attemptId: string, question: Question, answer: QuestionAnswer) => {
      let payload: AnswerUpsertRequest;

      if (answer.type === 'multiple-choice') {
        if (!question.optionIds || question.optionIds.length === 0) {
          throw new Error('Missing option IDs for multiple choice answer.');
        }

        const selectedOptionIds = answer.selectedOptionIndexes
          .map((index) => question.optionIds[index])
          .filter((optionId): optionId is string => Boolean(optionId));

        payload = {
          type: 'multiple_choice',
          data: { selected_option_ids: selectedOptionIds },
        };
      } else if (answer.type === 'freitext') {
        payload = {
          type: 'free_text',
          data: { text_response: answer.textResponse },
        };
      } else {
        if (!question.blankIds || question.blankIds.length === 0) {
          throw new Error('Missing blank IDs for cloze answer.');
        }
        if (question.blankIds.length !== answer.filledWords.length) {
          throw new Error('Cloze answer length mismatch.');
        }

        payload = {
          type: 'cloze',
          data: {
            provided_values: answer.filledWords.map((value, index) => ({
              blank_id: question.blankIds[index],
              value,
            })),
          },
        };
      }

      await requestJson(
        buildApiUrl(`/learning/attempts/${attemptId}/answers/${question.id}`),
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        },
      );

      if (answer.type === 'freitext') {
        await requestJson(
          buildApiUrl(
            `/learning/attempts/${attemptId}/answers/${question.id}/free-text-correctness`,
          ),
          {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_correct: answer.isCorrect }),
          },
        );
      }
    },
    [],
  );

  const clearAttemptState = useCallback(() => {
    setCurrentAttemptId(null);
    setActiveQuizId(null);
    setCurrentQuestions([]);
    setCurrentQuestionIndex(0);
    setIsAttemptComplete(false);
    setAnsweredQuestionIds([]);
    setTemporaryAnswers({});
  }, []);

  const finalizeAttempt = useCallback(
    async (attemptId: string, quizId: string) => {
      try {
        const evaluation = await requestJson<EvaluationResponseApi>(
          buildApiUrl(`/learning/attempts/${attemptId}/evaluation`),
          {
            method: 'POST',
          },
        );
        setEvaluationByAttemptId((prev) => ({ ...prev, [attemptId]: evaluation }));

        await loadAttemptsForQuiz(quizId);
        setIsAttemptComplete(true);

        setTimeout(() => {
          clearAttemptState();
          navigate(routes.quiz.detail(quizId));
        }, 2000);
      } catch (error) {
        console.error('Failed to finalize attempt', error);
        alert('Auswertung konnte nicht abgeschlossen werden.');
      }
    },
    [clearAttemptState, loadAttemptsForQuiz, navigate],
  );

  const handleStartAttempt = useCallback(
    async (quizId: string) => {
      const quizStatus =
        quizDetailsById[quizId]?.status ??
        quizzes.find((quiz) => quiz.id === quizId)?.status;
      if (quizStatus && quizStatus !== 'completed') {
        alert('Quiz wird noch generiert. Bitte spaeter erneut versuchen.');
        return;
      }

      const cachedQuestions = quizQuestions[quizId] ?? [];
      const questions = cachedQuestions.length
        ? cachedQuestions
        : (await loadQuizDetail(quizId))?.questions ?? [];

      if (questions.length === 0) {
        alert('Quiz ist noch in Bearbeitung oder hat keine Fragen.');
        return;
      }

      try {
        const attempt = await requestJson<AttemptSummaryApi>(
          buildApiUrl(`/learning/quizzes/${quizId}/attempts`),
          { method: 'POST' },
        );

        const existingAnswerIds = Array.isArray(attempt.existing_answers)
          ? attempt.existing_answers
              .map((answer) => answer.task_id)
              .filter((taskId): taskId is string => typeof taskId === 'string')
          : [];
        const answeredSet = new Set(existingAnswerIds);
        const firstUnansweredIndex = findNextUnansweredIndex(questions, 0, answeredSet);

        setCurrentAttemptId(attempt.attempt_id);
        setActiveQuizId(quizId);
        setCurrentQuestions(questions);
        setCurrentQuestionIndex(firstUnansweredIndex === -1 ? 0 : firstUnansweredIndex);
        setIsAttemptComplete(false);
        setAnsweredQuestionIds(existingAnswerIds);

        if (firstUnansweredIndex === -1) {
          alert('Alle Fragen wurden bereits beantwortet. Auswertung wird abgeschlossen.');
          await finalizeAttempt(attempt.attempt_id, quizId);
          return;
        }

        navigate(routes.quiz.attempt(quizId));
      } catch (error) {
        console.error('Failed to start attempt', error);
        alert('Versuch konnte nicht gestartet werden.');
      }
    },
    [finalizeAttempt, loadQuizDetail, navigate, quizDetailsById, quizQuestions, quizzes],
  );

  const handleAnswerQuestion = useCallback(
    async (answer: QuestionAnswer, autoAdvance: boolean = true) => {
      if (!currentAttemptId || activeQuizId === null) return;

      const question = currentQuestions[currentQuestionIndex];
      if (!question) return;

      try {
        await saveAnswerForQuestion(currentAttemptId, question, answer);
      } catch (error) {
        console.error('Failed to save answer', error);
        alert('Antwort konnte nicht gespeichert werden.');
        return;
      }

      const updatedAnswered = new Set<string>(answeredQuestionIds);
      updatedAnswered.add(question.id);
      setAnsweredQuestionIds(Array.from(updatedAnswered));

      // Only auto-advance if autoAdvance is true
      if (autoAdvance) {
        const nextIndex = findNextUnansweredIndex(
          currentQuestions,
          currentQuestionIndex + 1,
          updatedAnswered,
        );

        if (nextIndex === -1) {
          await finalizeAttempt(currentAttemptId, activeQuizId);
        } else {
          setCurrentQuestionIndex(nextIndex);
        }
      }
    },
    [
      activeQuizId,
      answeredQuestionIds,
      currentAttemptId,
      currentQuestionIndex,
      currentQuestions,
      finalizeAttempt,
      saveAnswerForQuestion,
    ],
  );

  const handleCancelAttempt = useCallback(async () => {
    if (!currentAttemptId || activeQuizId === null) return;
    await finalizeAttempt(currentAttemptId, activeQuizId);
  }, [activeQuizId, currentAttemptId, finalizeAttempt]);

  const saveTemporaryAnswer = useCallback(
    (questionId: string, answer: QuestionAnswer) => {
      setTemporaryAnswers((prev) => ({ ...prev, [questionId]: answer }));
    },
    [],
  );

  const getTemporaryAnswer = useCallback(
    (questionId: string): QuestionAnswer | undefined => {
      return temporaryAnswers[questionId];
    },
    [temporaryAnswers],
  );

  const handlePreviousQuestion = useCallback(() => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  }, [currentQuestionIndex]);

  const handleNextQuestion = useCallback(() => {
    if (currentQuestionIndex < currentQuestions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  }, [currentQuestionIndex, currentQuestions.length]);

  const handleGoToQuestion = useCallback((index: number) => {
    if (index >= 0 && index < currentQuestions.length) {
      setCurrentQuestionIndex(index);
    }
  }, [currentQuestions.length]);

  const clearAttemptsForQuiz = useCallback(
    (quizId: string) => {
      setAttemptsByQuizId((prev) => {
        const { [quizId]: removed, ...rest } = prev;
        return rest;
      });
      setEvaluationByAttemptId((prev) => {
        const attempts = attemptsByQuizId[quizId];
        if (!attempts || attempts.length === 0) {
          return prev;
        }
        const updated = { ...prev };
        attempts.forEach((attempt) => {
          delete updated[attempt.attempt_id];
        });
        return updated;
      });
    },
    [attemptsByQuizId],
  );

  const resetAttemptSession = useCallback(() => {
    clearAttemptState();
    setAttemptsByQuizId({});
    setEvaluationByAttemptId({});
  }, [clearAttemptState]);

  return {
    attemptsByQuizId,
    evaluationByAttemptId,
    currentAttemptId,
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
  };
};
