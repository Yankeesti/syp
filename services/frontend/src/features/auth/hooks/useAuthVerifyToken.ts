import { useEffect, useState } from 'react';
import { verifyMagicLink } from '../model/authApi';

export type VerifyStatus = 'loading' | 'success' | 'error';

const DEFAULT_MESSAGE = 'Verifiziere Token...';

export const useAuthVerifyToken = (token: string | null) => {
  const [status, setStatus] = useState<VerifyStatus>('loading');
  const [message, setMessage] = useState(DEFAULT_MESSAGE);

  useEffect(() => {
    let isActive = true;

    if (!token) {
      setStatus('error');
      setMessage('Token fehlt im Link.');
      return () => {};
    }

    const run = async () => {
      try {
        setStatus('loading');
        setMessage(DEFAULT_MESSAGE);
        await verifyMagicLink(token);
        if (!isActive) {
          return;
        }
        setStatus('success');
        setMessage('Token gespeichert. Du kannst fortfahren.');
      } catch (error) {
        if (!isActive) {
          return;
        }
        const fallback = 'Verifizierung fehlgeschlagen. Bitte pruefe den Link.';
        setStatus('error');
        setMessage(error instanceof Error ? error.message : fallback);
      }
    };

    run();

    return () => {
      isActive = false;
    };
  }, [token]);

  return { status, message };
};
