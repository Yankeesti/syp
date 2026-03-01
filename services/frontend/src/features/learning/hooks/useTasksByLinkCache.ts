import { useCallback, useRef, useState } from 'react';
import { isApiError, requestJson } from '../../../shared/api/client';
import type { TaskApi } from '../../quiz/model/types';

export type TasksByLinkStatus = 'idle' | 'loading' | 'loaded' | 'error';

type TasksByLinkCache = Record<string, TaskApi[]>;
type TasksByLinkStatusMap = Record<string, TasksByLinkStatus>;
type TasksByLinkErrorMap = Record<string, string | null>;

export const useTasksByLinkCache = () => {
  const cacheRef = useRef<TasksByLinkCache>({});
  const inFlightRef = useRef<Record<string, Promise<TaskApi[] | null>>>({});
  const [tasksByLink, setTasksByLink] = useState<TasksByLinkCache>({});
  const [tasksByLinkStatusByUrl, setTasksByLinkStatusByUrl] =
    useState<TasksByLinkStatusMap>({});
  const [tasksByLinkErrorByUrl, setTasksByLinkErrorByUrl] =
    useState<TasksByLinkErrorMap>({});

  const loadTasksByLink = useCallback(async (tasksLink: string) => {
    if (!tasksLink) {
      return null;
    }

    const cached = cacheRef.current[tasksLink];
    if (cached) {
      setTasksByLinkStatusByUrl((prev) => ({ ...prev, [tasksLink]: 'loaded' }));
      return cached;
    }

    const inFlight = inFlightRef.current[tasksLink];
    if (inFlight) {
      return inFlight;
    }

    setTasksByLinkStatusByUrl((prev) => ({ ...prev, [tasksLink]: 'loading' }));
    setTasksByLinkErrorByUrl((prev) => ({ ...prev, [tasksLink]: null }));

    const promise = (async () => {
      try {
        const response = await requestJson<TaskApi[]>(tasksLink);
        if (!Array.isArray(response)) {
          throw new Error('Fragen fuer den Versuch konnten nicht geladen werden.');
        }
        cacheRef.current[tasksLink] = response;
        setTasksByLink((prev) => ({ ...prev, [tasksLink]: response }));
        setTasksByLinkStatusByUrl((prev) => ({ ...prev, [tasksLink]: 'loaded' }));
        return response;
      } catch (error) {
        setTasksByLinkStatusByUrl((prev) => ({ ...prev, [tasksLink]: 'error' }));
        const fallback = 'Fragen fuer den Versuch konnten nicht geladen werden.';
        const message = isApiError(error)
          ? error.detail ?? error.message ?? fallback
          : error instanceof Error
            ? error.message
            : fallback;
        setTasksByLinkErrorByUrl((prev) => ({ ...prev, [tasksLink]: message }));
        return null;
      } finally {
        delete inFlightRef.current[tasksLink];
      }
    })();

    inFlightRef.current[tasksLink] = promise;
    return promise;
  }, []);

  const clearTasksByLinkCache = useCallback(() => {
    cacheRef.current = {};
    inFlightRef.current = {};
    setTasksByLink({});
    setTasksByLinkStatusByUrl({});
    setTasksByLinkErrorByUrl({});
  }, []);

  return {
    tasksByLink,
    tasksByLinkStatusByUrl,
    tasksByLinkErrorByUrl,
    loadTasksByLink,
    clearTasksByLinkCache,
  };
};
