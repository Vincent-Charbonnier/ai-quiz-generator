export interface QuizConfig {
  endpoint?: string;
  apiKey?: string;
  model?: string;
  numQuestions: number;
  pdfUrl?: string;
  pdfPath?: string;
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
