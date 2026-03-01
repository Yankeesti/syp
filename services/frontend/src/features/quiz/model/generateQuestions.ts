import type { Question, QuestionType } from '../entities/question/types';

export function generateQuestions(
  theme: string,
  types: QuestionType[],
  count: number = 10,
): Question[] {
  const questions: Question[] = [];

  // Distribute questions evenly across types
  const questionsPerType = Math.floor(count / types.length);
  const remainder = count % types.length;

  let questionId = 1;

  types.forEach((type, typeIndex) => {
    // Add extra question to first types if there's a remainder
    const questionsForThisType = questionsPerType + (typeIndex < remainder ? 1 : 0);

    for (let i = 0; i < questionsForThisType; i += 1) {
      if (type === 'multiple-choice') {
        questions.push({
          type: 'multiple-choice',
          id: String(questionId++),
          theme,
          question: `Frage ${questionId - 1}: Was ist die richtige Aussage über ${theme}?`,
          options: [
            `${theme} ist eine wichtige Technologie für moderne Webentwicklung`,
            `${theme} wurde in den 1990er Jahren entwickelt`,
            `${theme} wird hauptsächlich für mobile Apps verwendet`,
            `${theme} ist eine Programmiersprache`,
          ],
          correctAnswers: [0],
        });
      } else if (type === 'freitext') {
        questions.push({
          type: 'freitext',
          id: String(questionId++),
          theme,
          question: `Frage ${questionId - 1}: Erkläre die wichtigsten Konzepte von ${theme}.`,
          solution: `${theme} umfasst verschiedene wichtige Konzepte, die für die Entwicklung essentiell sind. Es bietet Lösungen für häufige Probleme und ermöglicht effizientes Arbeiten.`,
        });
      } else if (type === 'lueckentext') {
        const words = ['Komponenten', 'Zustand', 'Props', 'Hooks', 'JSX'];
        const shuffled = [...words].sort(() => Math.random() - 0.5);
        questions.push({
          type: 'lueckentext',
          id: String(questionId++),
          theme,
          textParts: [
            `${theme} verwendet `,
            ' um die Benutzeroberfläche zu strukturieren. Der ',
            ' wird mit ',
            ' verwaltet, und Daten werden über ',
            ' weitergegeben. Modern entwickelt man mit ',
            '.',
          ],
          words: shuffled,
          correctWords: words,
        });
      }
    }
  });

  // Shuffle the questions to mix types
  return questions.sort(() => Math.random() - 0.5);
}
