import { buildApiUrl, requestJson } from '../../../shared/api/client';
import type { ShareLinkApi, ShareLinkCreateRequest, ShareLinkInfoApi } from './types';

export const listShareLinks = (quizId: string) =>
  requestJson<ShareLinkApi[]>(buildApiUrl(`/quiz/quizzes/${quizId}/share-links`));

export const createShareLink = (quizId: string, payload: ShareLinkCreateRequest) =>
  requestJson<ShareLinkApi>(buildApiUrl(`/quiz/quizzes/${quizId}/share-links`), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

export const revokeShareLink = (quizId: string, shareLinkId: string) =>
  requestJson<void>(buildApiUrl(`/quiz/quizzes/${quizId}/share-links/${shareLinkId}`), {
    method: 'DELETE',
  });

export const validateShareLink = (token: string) =>
  requestJson<ShareLinkInfoApi>(buildApiUrl(`/quiz/share/${token}`), undefined, {
    includeAuth: false,
  });

export const redeemShareLink = (token: string) =>
  requestJson<void>(buildApiUrl(`/quiz/share/${token}/redeem`), {
    method: 'POST',
  });
