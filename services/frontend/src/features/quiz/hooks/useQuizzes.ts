import { useCallback, useEffect, useRef, useState } from 'react';
import type { Question, QuestionType } from '../entities/question/types';
import type { Quiz } from '../entities/quiz/types';
import { buildApiUrl, requestJson } from '../../../shared/api/client';
import { mapTaskTypeToQuestionType, mapTasksToQuestions } from '../model/mappers';
import type { QuizDetailResponseApi, QuizListItemApi } from '../model/types';

type QuizDetailStatus = 'loading' | 'loaded' | 'error';

export const useQuizzes = (currentUserId: string) => {
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [quizDetailsById, setQuizDetailsById] = useState<
    Record<string, QuizDetailResponseApi | null>
  >({});
  const [quizDetailStatusById, setQuizDetailStatusById] = useState<
    Record<string, QuizDetailStatus>
  >({});
  const [quizQuestions, setQuizQuestions] = useState<Record<string, Question[]>>({});
  const quizPollTimeouts = useRef<Record<string, number>>({});

  const loadQuizzes = useCallback(async () => {
    try {
      const items = await requestJson<QuizListItemApi[]>(buildApiUrl('/quiz/quizzes'));
      const mapped = items.map((item) => {
        const isOwner = item.role === 'owner';
        const isEditor = item.role === 'editor';
        const questionTypes = Array.isArray(item.question_types)
          ? Array.from(new Set(item.question_types.map(mapTaskTypeToQuestionType)))
          : [];

        return {
          id: item.quiz_id,
          title: item.title,
          theme: item.topic ?? item.title,
          ownerId: isOwner ? currentUserId : 'unknown-owner',
          questionCount: typeof item.question_count === 'number' ? item.question_count : 0,
          questionTypes,
          createdAt: new Date(item.created_at),
          watchers: [],
          editors: isEditor ? [currentUserId] : [],
          status: item.status,
          state: item.state,
          role: item.role,
        };
      });

      setQuizzes(mapped);
    } catch (error) {
      console.error('Failed to load quizzes', error);
    }
  }, [currentUserId]);

  const loadQuizDetail = useCallback(async (quizId: string) => {
    setQuizDetailStatusById((prev) => ({ ...prev, [quizId]: 'loading' }));

    try {
      const detail = await requestJson<QuizDetailResponseApi>(
        buildApiUrl(`/quiz/quizzes/${quizId}`),
      );
      const tasks = Array.isArray(detail.tasks) ? detail.tasks : [];
      if (!Array.isArray(detail.tasks)) {
        console.warn('Quiz detail response without tasks array', detail);
      }
      const questions = mapTasksToQuestions(tasks);
      const questionTypes = Array.from(
        new Set(tasks.map((task) => mapTaskTypeToQuestionType(task.type))),
      ) as QuestionType[];

      setQuizDetailsById((prev) => ({ ...prev, [quizId]: detail }));
      setQuizQuestions((prev) => ({ ...prev, [quizId]: questions }));
      setQuizzes((prev) => {
        const existing = prev.find((quiz) => quiz.id === quizId);
        if (existing) {
          return prev.map((quiz) =>
            quiz.id === quizId
              ? {
                  ...quiz,
                  title: detail.title,
                  theme: detail.topic ?? quiz.theme,
                  questionCount: questions.length,
                  questionTypes,
                  status: detail.status,
                  state: detail.state,
                }
              : quiz,
          );
        }

        return [
          ...prev,
          {
            id: detail.quiz_id,
            title: detail.title,
            theme: detail.topic ?? detail.title,
            ownerId: detail.created_by,
            questionCount: questions.length,
            questionTypes,
            createdAt: new Date(detail.created_at),
            watchers: [],
            editors: [],
            status: detail.status,
            state: detail.state,
          },
        ];
      });

      setQuizDetailStatusById((prev) => ({ ...prev, [quizId]: 'loaded' }));
      return { detail, questions };
    } catch (error) {
      setQuizDetailStatusById((prev) => ({ ...prev, [quizId]: 'error' }));
      console.error('Failed to load quiz detail', error);
      return null;
    }
  }, []);

  const clearQuizPoll = useCallback((quizId: string) => {
    const timeoutId = quizPollTimeouts.current[quizId];
    if (timeoutId) {
      window.clearTimeout(timeoutId);
      delete quizPollTimeouts.current[quizId];
    }
  }, []);

  const scheduleQuizPoll = useCallback(
    (quizId: string) => {
      clearQuizPoll(quizId);
      quizPollTimeouts.current[quizId] = window.setTimeout(async () => {
        const result = await loadQuizDetail(quizId);
        if (!result) {
          return;
        }
        if (result.detail.status === 'pending' || result.detail.status === 'generating') {
          scheduleQuizPoll(quizId);
        } else {
          clearQuizPoll(quizId);
        }
      }, 3000);
    },
    [clearQuizPoll, loadQuizDetail],
  );

  const clearAllQuizPolls = useCallback(() => {
    Object.values(quizPollTimeouts.current).forEach((timeoutId) => {
      window.clearTimeout(timeoutId);
    });
    quizPollTimeouts.current = {};
  }, []);

  useEffect(() => {
    return () => {
      clearAllQuizPolls();
    };
  }, [clearAllQuizPolls]);

  useEffect(() => {
    void loadQuizzes();
  }, [loadQuizzes]);

  useEffect(() => {
    const shouldPoll = quizzes.some(
      (quiz) => quiz.status === 'pending' || quiz.status === 'generating',
    );
    if (!shouldPoll) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      void loadQuizzes();
    }, 4000);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [quizzes, loadQuizzes]);

  return {
    quizzes,
    setQuizzes,
    quizDetailsById,
    setQuizDetailsById,
    quizDetailStatusById,
    setQuizDetailStatusById,
    quizQuestions,
    setQuizQuestions,
    loadQuizzes,
    loadQuizDetail,
    scheduleQuizPoll,
    clearQuizPoll,
    clearAllQuizPolls,
  };
};
