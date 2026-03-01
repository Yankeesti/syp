import { useEffect } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate, useSearchParams } from 'react-router-dom';
import { routes } from './routes';
import {
  LoginScreen,
  PrivacyPolicyScreen,
  RegisterScreen,
  WelcomeScreen,
  useAuthVerifyToken,
} from '../features/auth';
import { RedirectIfAuthenticated } from './guards';
import { getPendingShareToken } from '../features/quiz/model/shareLinkStorage';

function WelcomeRoute() {
  const navigate = useNavigate();
  return <WelcomeScreen onLogin={() => navigate(routes.auth.login)} onRegister={() => navigate(routes.auth.register)} />;
}

function LoginRoute() {
  const navigate = useNavigate();
  return <LoginScreen onBack={() => navigate(routes.root)} />;
}

function RegisterRoute() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <RegisterScreen
      onBack={() => navigate(routes.root)}
      onPrivacyPolicy={() => navigate(routes.auth.privacy, { state: { from: location.pathname } })}
    />
  );
}

function PrivacyRoute() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as { from?: string } | null;
  const backPath = typeof state?.from === 'string' ? state.from : routes.auth.register;

  return <PrivacyPolicyScreen onBack={() => navigate(backPath)} />;
}

function VerifyRoute() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const { status } = useAuthVerifyToken(token);

  useEffect(() => {
    if (status === 'success') {
      const pendingShareToken = getPendingShareToken();
      if (pendingShareToken) {
        navigate(routes.share.redeem(pendingShareToken), { replace: true });
      } else {
        navigate(routes.quiz.root, { replace: true });
      }
    } else if (status === 'error') {
      navigate(routes.auth.login, { replace: true });
    }
  }, [status, navigate]);

  return null;
}

export function AuthRoutes() {
  return (
    <Routes>
      <Route
        path={routes.root}
        element={
          <RedirectIfAuthenticated>
            <WelcomeRoute />
          </RedirectIfAuthenticated>
        }
      />
      <Route
        path={routes.auth.login}
        element={
          <RedirectIfAuthenticated>
            <LoginRoute />
          </RedirectIfAuthenticated>
        }
      />
      <Route
        path={routes.auth.register}
        element={
          <RedirectIfAuthenticated>
            <RegisterRoute />
          </RedirectIfAuthenticated>
        }
      />
      <Route path={routes.auth.privacy} element={<PrivacyRoute />} />
      <Route path={routes.auth.verify} element={<VerifyRoute />} />
      <Route path="*" element={<Navigate to={routes.root} replace />} />
    </Routes>
  );
}
