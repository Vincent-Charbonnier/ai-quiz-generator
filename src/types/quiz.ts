export interface QuizConfig {
  endpoint: string;
  apiKey: string;
  model: string;
  numQuestions: number;
}

export interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
  correctIndex: number;
}

export interface QuizState {
  questions: QuizQuestion[];
  answers: Record<number, number>;
  submitted: boolean;
}
