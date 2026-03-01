import { config } from '../../../config/env';
import { requestJson } from '../../../shared/api/client';
import { setAuthToken } from './tokenStorage';

export type MagicLinkResponse = {
  message: string;
  expires_in: number;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type ReportErrorResponse = {
  message: string;
};

export const requestMagicLink = (email: string) =>
  requestJson<MagicLinkResponse>(
    config.apiUrls.auth.magicLink,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    },
    { includeAuth: false },
  );

export const registerUser = (email: string) =>
  requestJson<MagicLinkResponse>(
    config.apiUrls.auth.register,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    },
    { includeAuth: false },
  );

export const verifyMagicLink = async (token: string) => {
  const url = new URL(config.apiUrls.auth.verify);
  url.searchParams.set('token', token);

  const data = await requestJson<TokenResponse>(url.toString(), undefined, {
    includeAuth: false,
  });
  if (!data.access_token) {
    throw new Error('Missing access token in response.');
  }
  setAuthToken(data.access_token, data.token_type);
  return data;
};

export const deleteAccount = () =>
  requestJson<void>(config.apiUrls.auth.deleteAccount, {
    method: 'DELETE',
  });

export const reportError = (message: string, contactEmail?: string) =>
  requestJson<ReportErrorResponse>(config.apiUrls.auth.report, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      // Backend erwartet `contact_email` (siehe ReportRequest-Schema)
      contact_email: contactEmail ?? undefined,
    }),
  });
