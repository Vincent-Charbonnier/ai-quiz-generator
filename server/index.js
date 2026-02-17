import express from "express";
import cors from "cors";
import multer from "multer";
import { promises as fs } from "fs";
import path from "path";

const app = express();
app.use(cors());
app.use(express.json());
const upload = multer({ storage: multer.memoryStorage() });
const CONFIG_PATH = process.env.CONFIG_PATH || "/data/quiz-config.json";

const ensureConfigDir = async () => {
  const dir = path.dirname(CONFIG_PATH);
  await fs.mkdir(dir, { recursive: true });
};

// Health check endpoint for K8s probes
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok" });
});

app.get("/api/config", async (req, res) => {
  try {
    const raw = await fs.readFile(CONFIG_PATH, "utf8");
    return res.json(JSON.parse(raw));
  } catch (err) {
    if (err.code === "ENOENT") {
      return res.status(204).end();
    }
    console.error("Config read error:", err);
    return res.status(500).json({ error: "Failed to read config" });
  }
});

app.post("/api/config", async (req, res) => {
  try {
    await ensureConfigDir();
    const body = req.body || {};
    await fs.writeFile(CONFIG_PATH, JSON.stringify(body, null, 2), "utf8");
    return res.json({ ok: true });
  } catch (err) {
    console.error("Config write error:", err);
    return res.status(500).json({ error: "Failed to save config" });
  }
});

app.post("/api/generate", upload.array("files"), async (req, res) => {
  const {
    endpoint,
    apiKey,
    model,
    systemPrompt,
    userPrompt,
    pdfUrl,
    embeddingEndpoint,
    embeddingToken,
    embeddingModel,
    llmEndpoint,
    llmToken,
    llmModel,
    chunkSize,
    chunkOverlap,
    topK,
  } = req.body;

  try {
    const ragUrl = process.env.RAG_URL || "http://rag:8000/chat/completions";

    const files = Array.isArray(req.files) ? req.files : [];
    const pdfs = files.map((file) => ({
      name: file.originalname,
      content_b64: file.buffer.toString("base64"),
    }));

    const toNumber = (value) => {
      if (value === undefined || value === null || value === "") return undefined;
      const n = Number(value);
      return Number.isNaN(n) ? undefined : n;
    };

    const body = {
      model: llmModel || model || "default",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      rag: {
        pdf_url: pdfUrl || process.env.RAG_PDF_URL || "",
        pdfs,
        embedding: {
          endpoint: embeddingEndpoint || process.env.RAG_EMBEDDING_ENDPOINT || "",
          token: embeddingToken || process.env.RAG_EMBEDDING_TOKEN || "",
          model: embeddingModel || process.env.RAG_EMBEDDING_MODEL || "",
        },
        llm: {
          endpoint: llmEndpoint || endpoint || process.env.RAG_LLM_ENDPOINT || "",
          token: llmToken || apiKey || process.env.RAG_LLM_TOKEN || "",
          model: llmModel || model || process.env.RAG_LLM_MODEL || "default",
        },
        chunk_size: toNumber(chunkSize),
        chunk_overlap: toNumber(chunkOverlap),
        top_k: toNumber(topK),
      },
    };

    const response = await fetch(ragUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const text = await response.text();
      console.error("RAG error:", response.status, text);
      return res.status(response.status).json({ error: text });
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || "";

    // Parse the JSON from the AI response
    const jsonMatch = content.match(/\[[\s\S]*\]/);
    if (!jsonMatch) {
      return res.status(500).json({ error: "AI did not return valid quiz JSON", raw: content });
    }

    const questions = JSON.parse(jsonMatch[0]);
    return res.json({ questions });
  } catch (err) {
    console.error("Generate error:", err);
    return res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Backend running on port ${PORT}`));
