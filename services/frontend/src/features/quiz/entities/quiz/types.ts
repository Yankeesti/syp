import type { QuestionType } from '../question/types';

export interface Quiz {
  id: string;
  title: string;
  theme: string;
  ownerId: string;
  questionCount: number;
  questionTypes: QuestionType[];
  createdAt: Date;
  watchers: string[];
  editors: string[];
  status?: 'pending' | 'generating' | 'completed' | 'failed';
  state?: 'private' | 'protected' | 'public';
  role?: 'owner' | 'editor' | 'viewer';
}
