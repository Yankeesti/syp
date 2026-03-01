import type { Question, QuestionType } from '../entities/question/types';
import type {
  TaskApi,
  TaskTypeApi,
  TaskUpdateApi,
  MultipleChoiceTaskUpdateApi,
  FreeTextTaskUpdateApi,
  ClozeTaskUpdateApi,
} from './types';

const shuffleArray = <T,>(items: T[]) => [...items].sort(() => Math.random() - 0.5);

const splitClozeTemplate = (templateText: string, blanksCount: number) => {
  const parts = templateText.split(/{{\s*blank_\d+\s*}}/g);
  if (parts.length < blanksCount + 1) {
    return [
      ...parts,
      ...Array.from({ length: blanksCount + 1 - parts.length }, () => ''),
    ];
  }
  if (parts.length > blanksCount + 1) {
    return parts.slice(0, blanksCount + 1);
  }
  return parts;
};

export const mapTaskTypeToQuestionType = (type: TaskTypeApi): QuestionType => {
  switch (type) {
    case 'multiple_choice':
      return 'multiple-choice';
    case 'free_text':
      return 'freitext';
    case 'cloze':
      return 'lueckentext';
    default:
      return 'multiple-choice';
  }
};

export const mapQuestionTypeToTaskType = (type: QuestionType): TaskTypeApi => {
  switch (type) {
    case 'multiple-choice':
      return 'multiple_choice';
    case 'freitext':
      return 'free_text';
    case 'lueckentext':
      return 'cloze';
    default:
      return 'multiple_choice';
  }
};

export const mapTasksToQuestions = (tasks: TaskApi[] | null | undefined): Question[] => {
  if (!Array.isArray(tasks) || tasks.length === 0) {
    return [];
  }

  const sorted = [...tasks].sort((a, b) => a.order_index - b.order_index);

  return sorted.map((task) => {
    if (task.type === 'multiple_choice') {
      const options = task.options.map((option) => option.text);
      const correctAnswers = task.options.reduce<number[]>((acc, option, index) => {
        if (option.is_correct) {
          acc.push(index);
        }
        return acc;
      }, []);

      return {
        type: 'multiple-choice',
        id: task.task_id,
        theme: task.topic_detail,
        question: task.prompt,
        options,
        correctAnswers,
        optionIds: task.options.map((option) => option.option_id),
      };
    }

    if (task.type === 'free_text') {
      return {
        type: 'freitext',
        id: task.task_id,
        theme: task.topic_detail,
        question: task.prompt,
        solution: task.reference_answer,
      };
    }

    const blanks = [...task.blanks].sort((a, b) => a.position - b.position);
    const correctWords = blanks.map((blank) => blank.expected_value);
    const blankIds = blanks.map((blank) => blank.blank_id);
    const textParts = splitClozeTemplate(task.template_text, blanks.length);

    return {
      type: 'lueckentext',
      id: task.task_id,
      theme: task.topic_detail,
      textParts,
      words: shuffleArray([...correctWords]),
      correctWords,
      blankIds,
    };
  });
};

// =============================================================================
// Question to TaskUpdate Mappers (Frontend → Backend)
// =============================================================================

/**
 * Rekonstruiert das Cloze-Template aus textParts.
 * textParts: ["Die ", " scheint am ", "."]
 * → "Die {{blank_0}} scheint am {{blank_1}}."
 */
const reconstructClozeTemplate = (textParts: string[]): string => {
  return textParts.reduce((acc, part, index) => {
    if (index === textParts.length - 1) {
      return acc + part;
    }
    return acc + part + `{{blank_${index}}}`;
  }, '');
};

/**
 * Mappt eine Frontend-Question zu einem Backend TaskUpdateApi DTO.
 */
export const mapQuestionToTaskUpdate = (question: Question): TaskUpdateApi => {
  if (question.type === 'multiple-choice') {
    const update: MultipleChoiceTaskUpdateApi = {
      type: 'multiple_choice',
      prompt: question.question,
      topic_detail: question.theme,
      options: question.options.map((text, index) => ({
        option_id: question.optionIds?.[index],
        text,
        is_correct: question.correctAnswers.includes(index),
      })),
    };
    return update;
  }

  if (question.type === 'freitext') {
    const update: FreeTextTaskUpdateApi = {
      type: 'free_text',
      prompt: question.question,
      topic_detail: question.theme,
      reference_answer: question.solution,
    };
    return update;
  }

  // type === 'lueckentext'
  const update: ClozeTaskUpdateApi = {
    type: 'cloze',
    prompt: question.textParts.join(' ___ '), // Simplified prompt representation
    topic_detail: question.theme,
    template_text: reconstructClozeTemplate(question.textParts),
    blanks: question.correctWords.map((word, index) => ({
      blank_id: question.blankIds?.[index],
      position: index,
      expected_value: word,
    })),
  };
  return update;
};
