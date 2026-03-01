export type JwtPayload = {
  exp?: number;
  iat?: number;
  sub?: string;
  [key: string]: unknown;
};

const ACCESS_TOKEN_KEY = 'syp.auth.access_token';
const TOKEN_TYPE_KEY = 'syp.auth.token_type';
const USER_EMAIL_KEY = 'syp.auth.user_email';
const DEFAULT_TOKEN_TYPE = 'bearer';

const isBrowser = typeof window !== 'undefined';

const storage = {
  getItem(key: string) {
    if (!isBrowser) {
      return null;
    }
    try {
      return window.localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  setItem(key: string, value: string) {
    if (!isBrowser) {
      return;
    }
    try {
      window.localStorage.setItem(key, value);
    } catch {
      // Ignore storage write errors (e.g. privacy mode).
    }
  },
  removeItem(key: string) {
    if (!isBrowser) {
      return;
    }
    try {
      window.localStorage.removeItem(key);
    } catch {
      // Ignore storage removal errors.
    }
  },
};

const decodeBase64Url = (value: string): string | null => {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padding = (4 - (normalized.length % 4)) % 4;
  const padded = normalized + '='.repeat(padding);
  try {
    return atob(padded);
  } catch {
    return null;
  }
};

export const setAuthToken = (accessToken: string, tokenType: string = DEFAULT_TOKEN_TYPE) => {
  if (!accessToken) {
    clearAuthToken();
    return;
  }
  storage.setItem(ACCESS_TOKEN_KEY, accessToken);
  storage.setItem(TOKEN_TYPE_KEY, tokenType);
};

export const getAccessToken = () => storage.getItem(ACCESS_TOKEN_KEY);

export const getTokenType = () => storage.getItem(TOKEN_TYPE_KEY) ?? DEFAULT_TOKEN_TYPE;

export const clearAuthToken = () => {
  storage.removeItem(ACCESS_TOKEN_KEY);
  storage.removeItem(TOKEN_TYPE_KEY);
};

export const setUserEmail = (email: string) => {
  const trimmed = email.trim();
  if (!trimmed) {
    storage.removeItem(USER_EMAIL_KEY);
    return;
  }
  storage.setItem(USER_EMAIL_KEY, trimmed);
};

export const getUserEmail = () => storage.getItem(USER_EMAIL_KEY);

export const clearUserEmail = () => {
  storage.removeItem(USER_EMAIL_KEY);
};

export const getTokenPayload = (token?: string): JwtPayload | null => {
  const value = token ?? getAccessToken();
  if (!value) {
    return null;
  }
  const parts = value.split('.');
  if (parts.length !== 3) {
    return null;
  }
  const decoded = decodeBase64Url(parts[1]);
  if (!decoded) {
    return null;
  }
  try {
    return JSON.parse(decoded) as JwtPayload;
  } catch {
    return null;
  }
};

export const isTokenExpired = (token?: string, clockSkewSeconds: number = 30) => {
  const payload = getTokenPayload(token);
  if (!payload?.exp) {
    return false;
  }
  const now = Math.floor(Date.now() / 1000);
  return payload.exp <= now + clockSkewSeconds;
};

export const getValidAccessToken = () => {
  const token = getAccessToken();
  if (!token) {
    return null;
  }
  if (isTokenExpired(token)) {
    clearAuthToken();
    return null;
  }
  return token;
};

export const getAuthHeader = () => {
  const token = getValidAccessToken();
  if (!token) {
    return {};
  }
  return { Authorization: `${getTokenType()} ${token}` };
};

export const isAuthenticated = () => Boolean(getValidAccessToken());
