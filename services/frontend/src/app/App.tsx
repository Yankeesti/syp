import { Navigate, Route, Routes } from 'react-router-dom';
import { routes } from './routes';
import { RequireAuth } from './guards';
import { QuizRoutes } from './QuizRoutes';
import { AuthRoutes } from './AuthRoutes';
import { ShareLinkView } from '../features/quiz/pages/ShareLinkView';

export default function App() {
  return (
    <Routes>
      <Route path={routes.share.redeem()} element={<ShareLinkView />} />
      <Route
        path={`${routes.quiz.root}/*`}
        element={
          <RequireAuth>
            <QuizRoutes />
          </RequireAuth>
        }
      />
      <Route path={routes.legacyHome} element={<Navigate to={routes.quiz.root} replace />} />
      <Route path="*" element={<AuthRoutes />} />
    </Routes>
  );
}
