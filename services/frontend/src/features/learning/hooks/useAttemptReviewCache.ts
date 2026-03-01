import { useCallback, useRef, useState } from 'react';
import type { Question } from '../../quiz/entities/question/types';
import { mapTasksToQuestions } from '../../quiz/model/mappers';
import type { AttemptDetailApi } from '../model/types';
import { useAttemptDetailCache } from './useAttemptDetailCache';
import { useTasksByLinkCache } from './useTasksByLinkCache';

export type AttemptReviewData = {
  detail: AttemptDetailApi;
  questions: Question[];
};

export type AttemptReviewStatus = 'idle' | 'loading' | 'loaded' | 'error';

type AttemptReviewCache = Record<string, AttemptReviewData>;
type AttemptReviewStatusMap = Record<string, AttemptReviewStatus>;
type AttemptReviewErrorMap = Record<string, string | null>;

export const useAttemptReviewCache = () => {
  const { loadAttemptDetail, clearAttemptDetailCache } = useAttemptDetailCache();
  const { loadTasksByLink, clearTasksByLinkCache } = useTasksByLinkCache();

  const cacheRef = useRef<AttemptReviewCache>({});
  const inFlightRef = useRef<Record<string, Promise<AttemptReviewData | null>>>({});
  const [attemptReviewsById, setAttemptReviewsById] = useState<AttemptReviewCache>({});
  const [attemptReviewStatusById, setAttemptReviewStatusById] =
    useState<AttemptReviewStatusMap>({});
  const [attemptReviewErrorById, setAttemptReviewErrorById] =
    useState<AttemptReviewErrorMap>({});

  const loadAttemptReview = useCallback(
    async (attemptId: string) => {
      const cached = cacheRef.current[attemptId];
      if (cached) {
        setAttemptReviewStatusById((prev) => ({ ...prev, [attemptId]: 'loaded' }));
        return cached;
      }

      const inFlight = inFlightRef.current[attemptId];
      if (inFlight) {
        return inFlight;
      }

      setAttemptReviewStatusById((prev) => ({ ...prev, [attemptId]: 'loading' }));
      setAttemptReviewErrorById((prev) => ({ ...prev, [attemptId]: null }));

      const promise = (async () => {
        try {
          const detail = await loadAttemptDetail(attemptId);
          if (!detail) {
            throw new Error('Versuch konnte nicht geladen werden.');
          }

          const hasAnswers = Array.isArray(detail.answers) && detail.answers.length > 0;
          const tasksLink = detail._links?.tasks ?? null;

          if (hasAnswers && !tasksLink) {
            throw new Error('Fragen fuer den Versuch konnten nicht geladen werden.');
          }

          let questions: Question[] = [];
          if (tasksLink) {
            const tasks = await loadTasksByLink(tasksLink);
            if (!tasks) {
              throw new Error('Fragen fuer den Versuch konnten nicht geladen werden.');
            }
            questions = mapTasksToQuestions(tasks);
          }

          if (hasAnswers && questions.length === 0) {
            throw new Error('Fragen fuer den Versuch konnten nicht geladen werden.');
          }

          const data = { detail, questions };
          cacheRef.current[attemptId] = data;
          setAttemptReviewsById((prev) => ({ ...prev, [attemptId]: data }));
          setAttemptReviewStatusById((prev) => ({ ...prev, [attemptId]: 'loaded' }));
          return data;
        } catch (error) {
          setAttemptReviewStatusById((prev) => ({ ...prev, [attemptId]: 'error' }));
          const fallback = 'Versuch konnte nicht geladen werden.';
          const message = error instanceof Error ? error.message || fallback : fallback;
          setAttemptReviewErrorById((prev) => ({ ...prev, [attemptId]: message }));
          return null;
        } finally {
          delete inFlightRef.current[attemptId];
        }
      })();

      inFlightRef.current[attemptId] = promise;
      return promise;
    },
    [loadAttemptDetail, loadTasksByLink],
  );

  const clearAttemptReviewCache = useCallback(() => {
    cacheRef.current = {};
    inFlightRef.current = {};
    setAttemptReviewsById({});
    setAttemptReviewStatusById({});
    setAttemptReviewErrorById({});
    clearAttemptDetailCache();
    clearTasksByLinkCache();
  }, [clearAttemptDetailCache, clearTasksByLinkCache]);

  return {
    attemptReviewsById,
    attemptReviewStatusById,
    attemptReviewErrorById,
    loadAttemptReview,
    clearAttemptReviewCache,
  };
};
