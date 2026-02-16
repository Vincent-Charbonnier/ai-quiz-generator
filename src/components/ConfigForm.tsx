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
  const [pdfFiles, setPdfFiles] = useState<File[]>([]);
  const [embeddingEndpoint, setEmbeddingEndpoint] = useState("");
  const [embeddingToken, setEmbeddingToken] = useState("");
  const [embeddingModel, setEmbeddingModel] = useState("nvidia/nv-embedqa-e5-v5");
  const [llmEndpoint, setLlmEndpoint] = useState("");
  const [llmToken, setLlmToken] = useState("");
  const [llmModel, setLlmModel] = useState("openai/gpt-oss-120b");
  const [chunkSize, setChunkSize] = useState(512);
  const [chunkOverlap, setChunkOverlap] = useState(64);
  const [topK, setTopK] = useState(6);
  const [numQuestions, setNumQuestions] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onGenerate({
      endpoint: llmEndpoint,
      apiKey: llmToken,
      model: llmModel,
      numQuestions,
      pdfFiles,
      embeddingEndpoint,
      embeddingToken,
      embeddingModel,
      llmEndpoint,
      llmToken,
      llmModel,
      chunkSize,
      chunkOverlap,
      topK,
    });
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
                <Label htmlFor="pdfFiles">Upload file(s)</Label>
                <Input
                  id="pdfFiles"
                  type="file"
                  multiple
                  accept="application/pdf"
                  onChange={(e) => setPdfFiles(Array.from(e.target.files || []))}
                />
                <Label htmlFor="embeddingEndpoint">Embedding Endpoint</Label>
                <Input
                  id="embeddingEndpoint"
                  placeholder="https://.../v1"
                  value={embeddingEndpoint}
                  onChange={(e) => setEmbeddingEndpoint(e.target.value)}
                />
                <Label htmlFor="embeddingToken">Embedding Token</Label>
                <Input
                  id="embeddingToken"
                  type="password"
                  placeholder="token"
                  value={embeddingToken}
                  onChange={(e) => setEmbeddingToken(e.target.value)}
                />
                <Label htmlFor="embeddingModel">Embedding Model</Label>
                <Input
                  id="embeddingModel"
                  placeholder="nvidia/nv-embedqa-e5-v5"
                  value={embeddingModel}
                  onChange={(e) => setEmbeddingModel(e.target.value)}
                />
                <Label htmlFor="llmEndpoint">LLM Endpoint</Label>
                <Input
                  id="llmEndpoint"
                  placeholder="https://.../v1"
                  value={llmEndpoint}
                  onChange={(e) => setLlmEndpoint(e.target.value)}
                />
                <Label htmlFor="llmToken">LLM Token</Label>
                <Input
                  id="llmToken"
                  type="password"
                  placeholder="token"
                  value={llmToken}
                  onChange={(e) => setLlmToken(e.target.value)}
                />
                <Label htmlFor="llmModel">LLM Model</Label>
                <Input
                  id="llmModel"
                  placeholder="openai/gpt-oss-120b"
                  value={llmModel}
                  onChange={(e) => setLlmModel(e.target.value)}
                />
                <Label htmlFor="chunkSize">Chunk Size</Label>
                <Input
                  id="chunkSize"
                  type="number"
                  value={chunkSize}
                  onChange={(e) => setChunkSize(Number(e.target.value))}
                />
                <Label htmlFor="chunkOverlap">Chunk Overlap</Label>
                <Input
                  id="chunkOverlap"
                  type="number"
                  value={chunkOverlap}
                  onChange={(e) => setChunkOverlap(Number(e.target.value))}
                />
                <Label htmlFor="topK">Top K</Label>
                <Input
                  id="topK"
                  type="number"
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
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
