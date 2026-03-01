import type { TaskTypeApi } from '../../quiz/model/types';

export type AttemptStatusApi = 'in_progress' | 'evaluated';

export type AttemptListItemApi = {
  attempt_id: string;
  quiz_id: string;
  status: AttemptStatusApi;
  started_at: string;
  evaluated_at: string | null;
  total_percentage: number | null;
};

export type AnswerDetailApi = {
  task_id: string;
  type: TaskTypeApi;
  percentage_correct: number | string;
};

export type EvaluationResponseApi = {
  attempt_id: string;
  quiz_id: string;
  total_percentage: number | string;
  evaluated_at: string;
  answer_details: AnswerDetailApi[];
};

export type ExistingMultipleChoiceAnswerApi = {
  task_id: string;
  type: 'multiple_choice';
  data: { selected_option_ids: string[] };
  percentage_correct?: number | string | null;
};

export type ExistingFreeTextAnswerApi = {
  task_id: string;
  type: 'free_text';
  data: { text_response: string };
  percentage_correct?: number | string | null;
};

export type ExistingClozeAnswerApi = {
  task_id: string;
  type: 'cloze';
  data: { provided_values: { blank_id: string; value: string }[] };
  percentage_correct?: number | string | null;
};

export type ExistingAnswerApi =
  | ExistingMultipleChoiceAnswerApi
  | ExistingFreeTextAnswerApi
  | ExistingClozeAnswerApi;

export type AttemptLinksApi = {
  tasks: string;
};

export type AttemptSummaryApi = {
  attempt_id: string;
  quiz_id: string;
  status: AttemptStatusApi;
  started_at: string;
  existing_answers: ExistingAnswerApi[];
};

export type AttemptDetailApi = {
  attempt_id: string;
  quiz_id: string;
  status: AttemptStatusApi;
  started_at: string;
  evaluated_at: string | null;
  total_percentage: number | null;
  answers: ExistingAnswerApi[];
  _links?: AttemptLinksApi | null;
};

export type AnswerUpsertRequest =
  | {
      type: 'multiple_choice';
      data: { selected_option_ids: string[] };
    }
  | {
      type: 'free_text';
      data: { text_response: string };
    }
  | {
      type: 'cloze';
      data: { provided_values: { blank_id: string; value: string }[] };
    };
