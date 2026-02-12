import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import type { QuizConfig } from "@/types/quiz";
import { Settings2, Zap } from "lucide-react";

interface ConfigFormProps {
  onGenerate: (config: QuizConfig) => void;
  loading: boolean;
}

const ConfigForm = ({ onGenerate, loading }: ConfigFormProps) => {
  const [endpoint, setEndpoint] = useState("http://localhost:11434/v1/chat/completions");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("default");
  const [numQuestions, setNumQuestions] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onGenerate({ endpoint, apiKey, model, numQuestions });
  };

  return (
    <Card className="w-full max-w-lg border-2">
      <CardHeader className="space-y-1">
        <div className="flex items-center gap-2">
          <Settings2 className="h-5 w-5 text-primary" />
          <CardTitle className="text-2xl font-bold">Quiz Generator</CardTitle>
        </div>
        <CardDescription>
          Connect to your RAG agent and generate a quiz
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="endpoint">API Endpoint</Label>
            <Input
              id="endpoint"
              placeholder="http://localhost:11434/v1/chat/completions"
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="apiKey">API Key (optional)</Label>
            <Input
              id="apiKey"
              type="password"
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="model">Model</Label>
            <Input
              id="model"
              placeholder="default"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Number of Questions</Label>
              <span className="text-sm font-semibold text-primary tabular-nums">
                {numQuestions}
              </span>
            </div>
            <Slider
              value={[numQuestions]}
              onValueChange={(v) => setNumQuestions(v[0])}
              min={1}
              max={20}
              step={1}
            />
          </div>

          <Button type="submit" className="w-full gap-2" size="lg" disabled={loading}>
            <Zap className="h-4 w-4" />
            {loading ? "Generating..." : "Generate Quiz"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default ConfigForm;
