import { buildApiUrl, requestJson } from '../../../shared/api/client';
import type { AttemptDetailApi } from './types';

export const getAttemptDetail = (attemptId: string) =>
  requestJson<AttemptDetailApi>(buildApiUrl(`/learning/attempts/${attemptId}`));
