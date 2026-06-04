export type ParsedFileSummary = {
  filename: string;
  status: string;
  preview: string;
  error: string | null;
};

export type RegulationChunk = {
  chunk_id: string;
  source_file: string;
  content: string;
  score: number | null;
  metadata: Record<string, unknown>;
};

export type AnalyzeResponse = {
  answer_text: string;
  parsed_files: ParsedFileSummary[];
  retrieved_regulations: RegulationChunk[];
};

export async function analyzeFiles(files: File[], question: string): Promise<AnalyzeResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  formData.append("question", question);

  const response = await fetch("/api/analyze", {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Analyze request failed with ${response.status}`);
  }

  return response.json();
}
