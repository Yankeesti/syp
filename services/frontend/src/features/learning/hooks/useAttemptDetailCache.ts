import { useCallback, useRef, useState } from 'react';
import { isApiError } from '../../../shared/api/client';
import { getAttemptDetail } from '../model/attemptApi';
import type { AttemptDetailApi } from '../model/types';

export type AttemptDetailStatus = 'idle' | 'loading' | 'loaded' | 'error';

type AttemptDetailCache = Record<string, AttemptDetailApi>;
type AttemptDetailStatusMap = Record<string, AttemptDetailStatus>;
type AttemptDetailErrorMap = Record<string, string | null>;

export const useAttemptDetailCache = () => {
  const cacheRef = useRef<AttemptDetailCache>({});
  const inFlightRef = useRef<Record<string, Promise<AttemptDetailApi | null>>>({});
  const [attemptDetailsById, setAttemptDetailsById] = useState<AttemptDetailCache>({});
  const [attemptDetailStatusById, setAttemptDetailStatusById] =
    useState<AttemptDetailStatusMap>({});
  const [attemptDetailErrorById, setAttemptDetailErrorById] =
    useState<AttemptDetailErrorMap>({});

  const loadAttemptDetail = useCallback(async (attemptId: string) => {
    const cached = cacheRef.current[attemptId];
    if (cached) {
      setAttemptDetailStatusById((prev) => ({ ...prev, [attemptId]: 'loaded' }));
      return cached;
    }

    const inFlight = inFlightRef.current[attemptId];
    if (inFlight) {
      return inFlight;
    }

    setAttemptDetailStatusById((prev) => ({ ...prev, [attemptId]: 'loading' }));
    setAttemptDetailErrorById((prev) => ({ ...prev, [attemptId]: null }));

    const promise = (async () => {
      try {
        const detail = await getAttemptDetail(attemptId);
        cacheRef.current[attemptId] = detail;
        setAttemptDetailsById((prev) => ({ ...prev, [attemptId]: detail }));
        setAttemptDetailStatusById((prev) => ({ ...prev, [attemptId]: 'loaded' }));
        return detail;
      } catch (error) {
        setAttemptDetailStatusById((prev) => ({ ...prev, [attemptId]: 'error' }));
        const fallback = 'Versuch konnte nicht geladen werden.';
        const message = isApiError(error)
          ? error.detail ?? error.message ?? fallback
          : error instanceof Error
            ? error.message
            : fallback;
        setAttemptDetailErrorById((prev) => ({ ...prev, [attemptId]: message }));
        return null;
      } finally {
        delete inFlightRef.current[attemptId];
      }
    })();

    inFlightRef.current[attemptId] = promise;
    return promise;
  }, []);

  const clearAttemptDetailCache = useCallback(() => {
    cacheRef.current = {};
    inFlightRef.current = {};
    setAttemptDetailsById({});
    setAttemptDetailStatusById({});
    setAttemptDetailErrorById({});
  }, []);

  return {
    attemptDetailsById,
    attemptDetailStatusById,
    attemptDetailErrorById,
    loadAttemptDetail,
    clearAttemptDetailCache,
  };
};
