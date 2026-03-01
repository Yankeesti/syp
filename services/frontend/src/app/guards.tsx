import type { ReactElement } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { routes } from './routes';
import { isAuthenticated } from '../features/auth/model/tokenStorage';

type GuardProps = {
  children: ReactElement;
};

export function RequireAuth({ children }: GuardProps) {
  const location = useLocation();
  if (!isAuthenticated()) {
    return (
      <Navigate
        to={routes.auth.login}
        replace
        state={{ from: location.pathname }}
      />
    );
  }
  return children;
}

export function RedirectIfAuthenticated({ children }: GuardProps) {
  const location = useLocation();
  if (isAuthenticated()) {
    return (
      <Navigate
        to={routes.quiz.root}
        replace
        state={{ from: location.pathname }}
      />
    );
  }
  return children;
}
