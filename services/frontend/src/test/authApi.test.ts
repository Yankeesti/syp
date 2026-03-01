import { beforeEach, describe, expect, it, vi } from 'vitest';

const requestJsonMock = vi.hoisted(() => vi.fn());
const setAuthTokenMock = vi.hoisted(() => vi.fn());

vi.mock('../config/env', () => ({
  config: {
    apiUrls: {
      auth: {
        magicLink: 'https://api.example.test/auth/magic-link',
        register: 'https://api.example.test/auth/register',
        verify: 'https://api.example.test/auth/verify',
        deleteAccount: 'https://api.example.test/auth/account',
      },
    },
  },
}));

vi.mock('../shared/api/client', () => ({
  requestJson: (...args: unknown[]) => requestJsonMock(...args),
}));

vi.mock('../features/auth/model/tokenStorage', () => ({
  setAuthToken: (...args: unknown[]) => setAuthTokenMock(...args),
}));

import {
  deleteAccount,
  registerUser,
  requestMagicLink,
  verifyMagicLink,
} from '../features/auth/model/authApi';

describe('authApi', () => {
  beforeEach(() => {
    requestJsonMock.mockReset();
    setAuthTokenMock.mockReset();
  });

  it('requestMagicLink posts the email without auth headers', async () => {
    const response = { message: 'ok', expires_in: 300 };
    requestJsonMock.mockResolvedValue(response);

    const result = await requestMagicLink('test@example.com');

    expect(result).toEqual(response);
    expect(requestJsonMock).toHaveBeenCalledWith(
      'https://api.example.test/auth/magic-link',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@example.com' }),
      },
      { includeAuth: false },
    );
  });

  it('registerUser posts the email without auth headers', async () => {
    const response = { message: 'ok', expires_in: 300 };
    requestJsonMock.mockResolvedValue(response);

    const result = await registerUser('new@example.com');

    expect(result).toEqual(response);
    expect(requestJsonMock).toHaveBeenCalledWith(
      'https://api.example.test/auth/register',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'new@example.com' }),
      },
      { includeAuth: false },
    );
  });

  it('verifyMagicLink stores tokens when response contains an access token', async () => {
    const response = { access_token: 'token-123', token_type: 'bearer' };
    requestJsonMock.mockResolvedValue(response);

    const result = await verifyMagicLink('magic-token');

    expect(result).toEqual(response);
    expect(requestJsonMock).toHaveBeenCalledTimes(1);
    const [url, init, options] = requestJsonMock.mock.calls[0];
    expect(new URL(String(url)).searchParams.get('token')).toBe('magic-token');
    expect(init).toBeUndefined();
    expect(options).toEqual({ includeAuth: false });
    expect(setAuthTokenMock).toHaveBeenCalledWith('token-123', 'bearer');
  });

  it('verifyMagicLink throws when access token is missing', async () => {
    requestJsonMock.mockResolvedValue({ access_token: '', token_type: 'bearer' });

    await expect(verifyMagicLink('missing-token')).rejects.toThrow(
      'Missing access token in response.',
    );
    expect(setAuthTokenMock).not.toHaveBeenCalled();
  });

  it('deleteAccount sends a delete request', async () => {
    requestJsonMock.mockResolvedValue(undefined);

    await deleteAccount();

    expect(requestJsonMock).toHaveBeenCalledWith(
      'https://api.example.test/auth/account',
      { method: 'DELETE' },
    );
  });
});
