const PENDING_SHARE_TOKEN_KEY = 'syp.share.pending_token';

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

export const setPendingShareToken = (token: string | null) => {
  const trimmed = token?.trim() ?? '';
  if (!trimmed) {
    storage.removeItem(PENDING_SHARE_TOKEN_KEY);
    return;
  }
  storage.setItem(PENDING_SHARE_TOKEN_KEY, trimmed);
};

export const getPendingShareToken = () => storage.getItem(PENDING_SHARE_TOKEN_KEY);

export const clearPendingShareToken = () => storage.removeItem(PENDING_SHARE_TOKEN_KEY);
