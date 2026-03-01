import { config } from '../../config/env';
import { getAuthHeader } from '../../features/auth/model/tokenStorage';

type ErrorResponse = {
  detail?: string;
  message?: string;
};

export type ApiError = Error & {
  status: number;
  detail?: string;
};

export const isApiError = (error: unknown): error is ApiError =>
  typeof error === 'object' &&
  error !== null &&
  'status' in error &&
  typeof (error as { status?: unknown }).status === 'number';

export const buildApiUrl = (path: string) =>
  `${config.apiBaseUrl}${path.startsWith('/') ? '' : '/'}${path}`;

export const requestJson = async <T,>(
  input: RequestInfo,
  init?: RequestInit,
  options?: { includeAuth?: boolean },
): Promise<T> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), config.apiTimeoutMs);
  const includeAuth = options?.includeAuth ?? true;

  try {
    const headers = new Headers(init?.headers ?? {});
    if (includeAuth) {
      const authHeader = getAuthHeader();
      Object.entries(authHeader).forEach(([key, value]) => {
        headers.set(key, value);
      });
    }

    const response = await fetch(input, { ...init, headers, signal: controller.signal });
    const contentType = response.headers.get('content-type') ?? '';
    const isJson = contentType.includes('application/json');
    const data = (isJson ? await response.json().catch(() => ({})) : {}) as T;

    if (!response.ok) {
      const errorBody = data as ErrorResponse;
      const message =
        errorBody.detail ?? errorBody.message ?? `Request failed (${response.status})`;
      const error = new Error(message) as ApiError;
      error.status = response.status;
      error.detail = errorBody.detail ?? errorBody.message;
      throw error;
    }

    return data;
  } finally {
    clearTimeout(timeoutId);
  }
};
