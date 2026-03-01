export type QuizStateApi = 'private' | 'protected' | 'public';
export type QuizStatusApi = 'pending' | 'generating' | 'completed' | 'failed';
export type OwnershipRoleApi = 'owner' | 'editor' | 'viewer';
export type TaskTypeApi = 'multiple_choice' | 'free_text' | 'cloze';

export type QuizListItemApi = {
  quiz_id: string;
  title: string;
  topic: string | null;
  state: QuizStateApi;
  status: QuizStatusApi;
  role: OwnershipRoleApi;
  created_at: string;
  question_count: number;
  question_types: TaskTypeApi[];
};

export type MultipleChoiceOptionApi = {
  option_id: string;
  text: string;
  is_correct: boolean;
  explanation?: string | null;
};

export type MultipleChoiceTaskApi = {
  type: 'multiple_choice';
  task_id: string;
  quiz_id: string;
  prompt: string;
  topic_detail: string;
  order_index: number;
  options: MultipleChoiceOptionApi[];
};

export type FreeTextTaskApi = {
  type: 'free_text';
  task_id: string;
  quiz_id: string;
  prompt: string;
  topic_detail: string;
  order_index: number;
  reference_answer: string;
};

export type ClozeBlankApi = {
  blank_id: string;
  position: number;
  expected_value: string;
};

export type ClozeTaskApi = {
  type: 'cloze';
  task_id: string;
  quiz_id: string;
  prompt: string;
  topic_detail: string;
  order_index: number;
  template_text: string;
  blanks: ClozeBlankApi[];
};

export type TaskApi = MultipleChoiceTaskApi | FreeTextTaskApi | ClozeTaskApi;

export type QuizDetailResponseApi = {
  quiz_id: string;
  title: string;
  topic: string | null;
  status: QuizStatusApi;
  state: QuizStateApi;
  created_by: string;
  created_at: string;
  tasks: TaskApi[];
};

export type QuizCreateResponseApi = {
  quiz_id: string;
  status: QuizStatusApi;
};

export type QuizEditSessionStartResponseApi = {
  edit_session_id: string;
  quiz: QuizDetailResponseApi;
};

// =============================================================================
// Task Update Types (Request DTOs)
// =============================================================================

export type MultipleChoiceOptionUpdateApi = {
  option_id?: string;
  text: string;
  is_correct: boolean;
  explanation?: string | null;
};

export type MultipleChoiceTaskUpdateApi = {
  type: 'multiple_choice';
  prompt?: string;
  topic_detail?: string;
  options?: MultipleChoiceOptionUpdateApi[];
};

export type FreeTextTaskUpdateApi = {
  type: 'free_text';
  prompt?: string;
  topic_detail?: string;
  reference_answer?: string;
};

export type ClozeBlankUpdateApi = {
  blank_id?: string;
  position: number;
  expected_value: string;
};

export type ClozeTaskUpdateApi = {
  type: 'cloze';
  prompt?: string;
  topic_detail?: string;
  template_text?: string;
  blanks?: ClozeBlankUpdateApi[];
};

export type TaskUpdateApi =
  | MultipleChoiceTaskUpdateApi
  | FreeTextTaskUpdateApi
  | ClozeTaskUpdateApi;

// =============================================================================
// Share Link Types
// =============================================================================

export type ShareLinkApi = {
  share_link_id: string;
  quiz_id: string;
  token: string;
  url: string;
  created_at: string;
  expires_at: string | null;
  max_uses: number | null;
  current_uses: number;
  is_active: boolean;
};

export type ShareLinkCreateRequest = {
  duration?: number | string;
  max_uses?: number;
};

export type ShareLinkInfoApi = {
  quiz_id: string | null;
  quiz_title: string;
  quiz_topic: string;
  is_valid: boolean;
  error_message: string | null;
};
