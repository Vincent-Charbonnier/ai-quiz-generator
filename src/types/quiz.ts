export interface QuizConfig {
  endpoint?: string;
  apiKey?: string;
  model?: string;
  numQuestions: number;
  pdfFiles?: File[];
  embeddingEndpoint?: string;
  embeddingToken?: string;
  embeddingModel?: string;
  llmEndpoint?: string;
  llmToken?: string;
  llmModel?: string;
  chunkSize?: number;
  chunkOverlap?: number;
  topK?: number;
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
