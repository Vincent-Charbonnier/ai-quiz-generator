import { useState } from "react";
import ConfigForm from "@/components/ConfigForm";
import QuizView from "@/components/QuizView";
import type { QuizConfig, QuizQuestion } from "@/types/quiz";
import { toast } from "@/hooks/use-toast";

const SYSTEM_PROMPT = `You are a quiz generator. Given a number of questions, generate a multiple-choice quiz based on the knowledge you have from the documents.
Return ONLY valid JSON in this exact format, no markdown, no explanation:
[{"id":1,"question":"...","options":["A","B","C","D"],"correctIndex":0}, ...]
Each question must have exactly 4 options. correctIndex is 0-based.`;

const Index = () => {
  const [questions, setQuestions] = useState<QuizQuestion[] | null>(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async (config: QuizConfig) => {
    setLoading(true);
    try {
      const backendUrl = import.meta.env.PROD
        ? "/api/generate"
        : "http://localhost:3001/api/generate";

      const res = await fetch(backendUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          endpoint: config.endpoint,
          apiKey: config.apiKey,
          model: config.model,
          systemPrompt: SYSTEM_PROMPT,
          userPrompt: `Generate exactly ${config.numQuestions} multiple-choice questions.`,
          pdfUrl: config.pdfUrl,
          pdfPath: config.pdfPath,
          embeddingEndpoint: config.embeddingEndpoint,
          embeddingToken: config.embeddingToken,
          embeddingModel: config.embeddingModel,
          llmEndpoint: config.llmEndpoint,
          llmToken: config.llmToken,
          llmModel: config.llmModel,
          chunkSize: config.chunkSize,
          chunkOverlap: config.chunkOverlap,
          topK: config.topK,
        }),
      });

      if (!res.ok) {
        const err = await res.text();
        throw new Error(err || "Failed to generate quiz");
      }

      const data = await res.json();
      setQuestions(data.questions);
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message || "Something went wrong",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6">
      {questions ? (
        <QuizView questions={questions} onReset={() => setQuestions(null)} />
      ) : (
        <ConfigForm onGenerate={handleGenerate} loading={loading} />
      )}
    </div>
  );
};

export default Index;
