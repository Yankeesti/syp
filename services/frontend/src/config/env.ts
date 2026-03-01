const DEFAULT_API_BASE_URL = 'http://localhost:8000';
const DEFAULT_API_TIMEOUT_MS = 10000;
const DEFAULT_APP_NAME = 'KI Tutor';
const DEFAULT_APP_VERSION = '0.1.0';
const DEFAULT_MAGIC_LINK_EXP_MINUTES = 5;
const DEFAULT_JWT_EXP_HOURS = 5;
const DEFAULT_USE_MOCKS = true;

const normalizeBaseUrl = (value: string) => value.replace(/\/+$/, '');

const toNumber = (value: string | undefined, fallback: number) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const toBoolean = (value: string | undefined, fallback: boolean) => {
  if (value === undefined) {
    return fallback;
  }
  return value.toLowerCase() === 'true';
};

const apiBaseUrl = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL);
const buildApiUrl = (path: string) => `${apiBaseUrl}${path.startsWith('/') ? '' : '/'}${path}`;

export type ApiUrls = {
  health: string;
  docs: string;
  auth: {
    magicLink: string;
    register: string;
    verify: string;
    deleteAccount: string;
    report: string;
  };
  quiz: {
    health: string;
    tasksHealth: string;
  };
  learning: {
    attemptsHealth: string;
    statsHealth: string;
  };
  llm: {
    health: string;
  };
};

export type AppConfig = {
  appName: string;
  appVersion: string;
  appEnv: string;
  isDev: boolean;
  isProd: boolean;
  apiBaseUrl: string;
  apiTimeoutMs: number;
  authMagicLinkExpirationMinutes: number;
  authJwtExpirationHours: number;
  useMocks: boolean;
  apiUrls: ApiUrls;
};

export const config: AppConfig = {
  appName: import.meta.env.VITE_APP_NAME ?? DEFAULT_APP_NAME,
  appVersion: import.meta.env.VITE_APP_VERSION ?? DEFAULT_APP_VERSION,
  appEnv: import.meta.env.MODE,
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
  apiBaseUrl,
  apiTimeoutMs: toNumber(import.meta.env.VITE_API_TIMEOUT_MS, DEFAULT_API_TIMEOUT_MS),
  authMagicLinkExpirationMinutes: toNumber(
    import.meta.env.VITE_AUTH_MAGIC_LINK_EXP_MINUTES,
    DEFAULT_MAGIC_LINK_EXP_MINUTES,
  ),
  authJwtExpirationHours: toNumber(import.meta.env.VITE_AUTH_JWT_EXP_HOURS, DEFAULT_JWT_EXP_HOURS),
  useMocks: toBoolean(import.meta.env.VITE_USE_MOCKS, DEFAULT_USE_MOCKS),
  apiUrls: {
    health: buildApiUrl('/health'),
    docs: buildApiUrl('/docs'),
    auth: {
      magicLink: buildApiUrl('/auth/magic-link'),
      register: buildApiUrl('/auth/register'),
      verify: buildApiUrl('/auth/verify'),
      deleteAccount: buildApiUrl('/auth/account'),
      report: buildApiUrl('/auth/report'),
    },
    quiz: {
      health: buildApiUrl('/quizzes/health'),
      tasksHealth: buildApiUrl('/tasks/health'),
    },
    learning: {
      attemptsHealth: buildApiUrl('/attempts/health'),
      statsHealth: buildApiUrl('/learning/health'),
    },
    llm: {
      health: buildApiUrl('/llm/health'),
    },
  },
};
