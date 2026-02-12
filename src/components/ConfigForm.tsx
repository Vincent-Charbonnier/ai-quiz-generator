import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { QuizConfig } from "@/types/quiz";
import { Settings2, Zap } from "lucide-react";

interface ConfigFormProps {
  onGenerate: (config: QuizConfig) => void;
  loading: boolean;
}

const ConfigForm = ({ onGenerate, loading }: ConfigFormProps) => {
  const [endpoint, setEndpoint] = useState("http://localhost:11434/v1/chat/completions");
  const [numQuestions, setNumQuestions] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onGenerate({ endpoint, apiKey: "", model: "default", numQuestions });
  };

  return (
    <Card className="w-full max-w-lg border-2">
      <CardHeader className="space-y-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            <CardTitle className="text-2xl font-bold">Quiz Generator</CardTitle>
          </div>
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Settings2 className="h-4 w-4" />
              </Button>
            </PopoverTrigger>
            <PopoverContent align="end" className="w-80">
              <div className="space-y-2">
                <Label htmlFor="endpoint">API Endpoint</Label>
                <Input
                  id="endpoint"
                  placeholder="http://localhost:11434/v1/chat/completions"
                  value={endpoint}
                  onChange={(e) => setEndpoint(e.target.value)}
                />
              </div>
            </PopoverContent>
          </Popover>
        </div>
        <CardDescription>
          Generate a quiz from your RAG agent
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
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
