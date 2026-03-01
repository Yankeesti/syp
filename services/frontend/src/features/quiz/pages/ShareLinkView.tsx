import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '../../../shared/ui/button';
import { Badge } from '../../../shared/ui/badge';
import { isApiError } from '../../../shared/api/client';
import { routes } from '../../../app/routes';
import { isAuthenticated } from '../../auth/model/tokenStorage';
import {
  clearPendingShareToken,
  getPendingShareToken,
  setPendingShareToken,
} from '../model/shareLinkStorage';
import type { ShareLinkInfoApi } from '../model/types';
import { redeemShareLink, validateShareLink } from '../model/shareLinkApi';

type ShareLinkStatus = 'loading' | 'ready' | 'invalid' | 'error';
type RedeemStatus = 'idle' | 'redeeming' | 'success' | 'already' | 'error';

export function ShareLinkView() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<ShareLinkStatus>('loading');
  const [info, setInfo] = useState<ShareLinkInfoApi | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [redeemStatus, setRedeemStatus] = useState<RedeemStatus>('idle');
  const [redeemMessage, setRedeemMessage] = useState<string | null>(null);
  const [autoRedeemTriggered, setAutoRedeemTriggered] = useState(false);

  const isAuthed = isAuthenticated();
  const quizRoute = info?.quiz_id ? routes.quiz.detail(info.quiz_id) : routes.quiz.list;

  useEffect(() => {
    if (!token) {
      return;
    }
    const pending = getPendingShareToken();
    if (pending && pending !== token) {
      clearPendingShareToken();
    }
  }, [token]);

  useEffect(() => {
    let isActive = true;

    if (!token) {
      setStatus('invalid');
      setErrorMessage('Der Freigabelink ist unvollstaendig.');
      setInfo(null);
      return () => {};
    }

    const run = async () => {
      try {
        setStatus('loading');
        setErrorMessage(null);
        setRedeemStatus('idle');
        setRedeemMessage(null);
        setAutoRedeemTriggered(false);
        setInfo(null);
        const response = await validateShareLink(token);

        if (!isActive) {
          return;
        }

        setInfo(response);
        if (response.is_valid) {
          setStatus('ready');
        } else {
          setStatus('invalid');
          setErrorMessage(response.error_message ?? 'Der Freigabelink ist nicht gueltig.');
        }
      } catch (error) {
        if (!isActive) {
          return;
        }
        setStatus('error');
        setErrorMessage(
          error instanceof Error
            ? error.message
            : 'Der Freigabelink konnte nicht geladen werden.',
        );
      }
    };

    run();

    return () => {
      isActive = false;
    };
  }, [token]);

  const handleRedeem = useCallback(async () => {
    if (!token) return;
    setRedeemStatus('redeeming');
    setRedeemMessage(null);

    try {
      await redeemShareLink(token);
      clearPendingShareToken();
      setRedeemStatus('success');
      navigate(quizRoute, { replace: true });
    } catch (error) {
      const fallback = 'Freischaltung fehlgeschlagen. Bitte versuche es erneut.';
      const message = error instanceof Error ? error.message : fallback;
      const normalized = message.toLowerCase();
      clearPendingShareToken();
      if (isApiError(error)) {
        if (error.status === 400) {
          setRedeemStatus('already');
          setRedeemMessage(null);
          return;
        }
        if (error.status === 410) {
          setRedeemStatus('error');
          setRedeemMessage(
            error.message || 'Der Freigabelink ist abgelaufen oder ungueltig.',
          );
          return;
        }
      }
      if (normalized.includes('already have access')) {
        setRedeemStatus('already');
        setRedeemMessage(null);
      } else {
        setRedeemStatus('error');
        setRedeemMessage(message || fallback);
      }
    }
  }, [navigate, quizRoute, token]);

  useEffect(() => {
    if (!isAuthed || status !== 'ready' || !token || autoRedeemTriggered) {
      return;
    }
    const pending = getPendingShareToken();
    if (pending && pending === token) {
      setAutoRedeemTriggered(true);
      void handleRedeem();
    }
  }, [autoRedeemTriggered, handleRedeem, isAuthed, status, token]);

  const handleNavigateAuth = (path: string) => {
    if (token) {
      setPendingShareToken(token);
    }
    navigate(path);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-xl bg-white rounded-xl border border-slate-200 p-8 shadow-sm space-y-6">
        <div>
          <h1 className="text-slate-900 text-[24px] mb-1">Quiz-Freigabe</h1>
          <p className="text-slate-600 text-sm">
            Mit diesem Link kannst du Zugriff auf ein Quiz erhalten.
          </p>
        </div>

        {status === 'loading' && (
          <div className="text-slate-600">Link wird ueberprueft...</div>
        )}

        {status === 'error' && (
          <div className="text-red-600">{errorMessage}</div>
        )}

        {status === 'invalid' && (
          <div className="space-y-3">
            <Badge className="bg-red-50 text-red-700 border-red-200">Ungueltig</Badge>
            <p className="text-slate-700">
              {errorMessage ?? 'Dieser Link ist nicht mehr gueltig oder wurde widerrufen.'}
            </p>
            <Button
              variant="outline"
              onClick={() => navigate(routes.root)}
              className="border-slate-300"
            >
              Zur Startseite
            </Button>
          </div>
        )}

        {status === 'ready' && info && (
          <div className="space-y-5">
            <div className="space-y-2">
              <Badge className="bg-green-50 text-green-700 border-green-200">Gueltig</Badge>
              <div>
                <h2 className="text-slate-900 text-[20px]">{info.quiz_title}</h2>
                {info.quiz_topic && (
                  <p className="text-slate-600">{info.quiz_topic}</p>
                )}
              </div>
            </div>

            {redeemMessage && (
              <div className="text-sm text-slate-700 bg-slate-50 border border-slate-200 rounded-lg p-3">
                {redeemMessage}
              </div>
            )}

            {redeemStatus === 'redeeming' && (
              <div className="text-sm text-slate-700 bg-slate-50 border border-slate-200 rounded-lg p-3">
                Zugriff wird gewaehrt...
              </div>
            )}

            {redeemStatus === 'already' && (
              <div className="space-y-3">
                <p className="text-slate-700 text-sm">
                  Du hast bereits Zugriff auf dieses Quiz.
                </p>
                <Button onClick={() => navigate(quizRoute)}>Zum Quiz</Button>
              </div>
            )}

            {!isAuthed && redeemStatus !== 'already' && (
              <div className="space-y-3">
                <p className="text-slate-700 text-sm">
                  Bitte melde dich an, um Zugriff zu erhalten.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button onClick={() => handleNavigateAuth(routes.auth.login)}>
                    Anmelden um zuzugreifen
                  </Button>
                </div>
              </div>
            )}

            {isAuthed && redeemStatus !== 'already' && (
              <div className="space-y-3">
                <p className="text-slate-700 text-sm">
                  Du bist angemeldet. Klicke auf \"Zum Quiz\", um Zugriff zu erhalten.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button onClick={handleRedeem} disabled={redeemStatus === 'redeeming'}>
                    {redeemStatus === 'redeeming' ? 'Zugriff wird gewaehrt...' : 'Zum Quiz'}
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
