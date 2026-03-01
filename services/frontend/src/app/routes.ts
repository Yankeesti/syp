export const routes = {
  root: '/',
  legacyHome: '/home',
  auth: {
    login: '/login',
    register: '/register',
    privacy: '/privacy',
    verify: '/auth/verify',
  },
  quiz: {
    root: '/quiz',
    list: '/quiz/quizzes',
    create: '/quiz/quizzes/new',
    detail: (quizId: number | string = ':quizId') => `/quiz/quizzes/${quizId}`,
    shareLinks: (quizId: number | string = ':quizId') =>
      `/quiz/quizzes/${quizId}/share-links`,
    edit: (quizId: number | string = ':quizId') => `/quiz/quizzes/${quizId}/edit`,
    attempt: (quizId: number | string = ':quizId') => `/quiz/quizzes/${quizId}/attempt`,
    attemptReview: (
      quizId: number | string = ':quizId',
      attemptId: number | string = ':attemptId',
    ) => `/quiz/quizzes/${quizId}/attempts/${attemptId}`,
  },
  share: {
    redeem: (token: number | string = ':token') => `/share/${token}`,
  },
};
