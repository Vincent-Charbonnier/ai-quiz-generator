import express from "express";
import cors from "cors";

const app = express();
app.use(cors());
app.use(express.json());

// Health check endpoint for K8s probes
app.get("/health", (req, res) => {
  res.status(200).json({ status: "ok" });
});

app.post("/api/generate", async (req, res) => {
  const {
    endpoint,
    apiKey,
    model,
    systemPrompt,
    userPrompt,
    pdfUrl,
    pdfPath,
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

    const body = {
      model: llmModel || model || "default",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
      rag: {
        pdf_url: pdfUrl || process.env.RAG_PDF_URL || "",
        pdf_path: pdfPath || process.env.RAG_PDF_PATH || "",
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
        chunk_size: chunkSize,
        chunk_overlap: chunkOverlap,
        top_k: topK,
      },
    };

    const response = await fetch(ragUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const text = await response.text();
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
