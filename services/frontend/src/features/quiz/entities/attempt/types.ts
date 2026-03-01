export interface QuizAttempt {
  id: string;
  quizId: string;
  userId: string;
  startedAt: Date;
  completedAt: Date | null;
  score: number | null;
  correctAnswers: number;
  totalQuestions: number;
  isComplete: boolean;
}
