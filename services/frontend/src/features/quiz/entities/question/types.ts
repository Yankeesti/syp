export type QuestionType = 'multiple-choice' | 'freitext' | 'lueckentext';

export interface MultipleChoiceQuestion {
  type: 'multiple-choice';
  id: string;
  theme: string;
  question: string;
  options: string[];
  correctAnswers: number[];
  optionIds?: string[];
}

export interface FreitextQuestion {
  type: 'freitext';
  id: string;
  theme: string;
  question: string;
  solution: string;
}

export interface LueckentextQuestion {
  type: 'lueckentext';
  id: string;
  theme: string;
  textParts: string[];
  words: string[];
  correctWords: string[];
  blankIds?: string[];
}

export type Question = MultipleChoiceQuestion | FreitextQuestion | LueckentextQuestion;
