import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { QuizQuestion } from "@/types/quiz";
import { CheckCircle2, XCircle, RotateCcw } from "lucide-react";
import { cn } from "@/lib/utils";

interface QuizViewProps {
  questions: QuizQuestion[];
  onReset: () => void;
}

const QuizView = ({ questions, onReset }: QuizViewProps) => {
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [submitted, setSubmitted] = useState(false);

  const selectAnswer = (questionId: number, optionIndex: number) => {
    if (submitted) return;
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));
  };

  const score = questions.filter((q) => answers[q.id] === q.correctIndex).length;
  const allAnswered = questions.every((q) => answers[q.id] !== undefined);

  return (
    <div className="w-full max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">
          Quiz <Badge variant="secondary" className="ml-2 text-base">{questions.length} questions</Badge>
        </h2>
        <Button variant="outline" size="sm" onClick={onReset} className="gap-1">
          <RotateCcw className="h-4 w-4" /> New Quiz
        </Button>
      </div>

      {submitted && (
        <Card className="border-2 border-primary/30 bg-accent/50">
          <CardContent className="py-4 text-center">
            <p className="text-lg font-semibold">
              Score: {score} / {questions.length} ({Math.round((score / questions.length) * 100)}%)
            </p>
          </CardContent>
        </Card>
      )}

      {questions.map((q, qi) => (
        <Card key={q.id} className="border">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium">
              <span className="text-primary mr-2">{qi + 1}.</span>
              {q.question}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {q.options.map((opt, oi) => {
              const selected = answers[q.id] === oi;
              const isCorrect = q.correctIndex === oi;
              let variant = "outline" as const;

              return (
                <button
                  key={oi}
                  onClick={() => selectAnswer(q.id, oi)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg border px-4 py-3 text-left text-sm transition-colors",
                    !submitted && selected && "border-primary bg-accent",
                    !submitted && !selected && "hover:border-muted-foreground/30 hover:bg-muted/50",
                    submitted && isCorrect && "border-success bg-success/10",
                    submitted && selected && !isCorrect && "border-destructive bg-destructive/10",
                  )}
                >
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-medium">
                    {String.fromCharCode(65 + oi)}
                  </span>
                  <span className="flex-1">{opt}</span>
                  {submitted && isCorrect && <CheckCircle2 className="h-5 w-5 text-success" />}
                  {submitted && selected && !isCorrect && <XCircle className="h-5 w-5 text-destructive" />}
                </button>
              );
            })}
          </CardContent>
        </Card>
      ))}

      {!submitted && (
        <Button
          className="w-full"
          size="lg"
          disabled={!allAnswered}
          onClick={() => setSubmitted(true)}
        >
          Submit Answers
        </Button>
      )}
    </div>
  );
};

export default QuizView;
