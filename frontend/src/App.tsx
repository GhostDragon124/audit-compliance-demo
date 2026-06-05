import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { FileText, Loader2, Play, UploadCloud } from "lucide-react";
import { AnalyzeResponse, analyzeFiles } from "./api";

const defaultQuestion = "请初步判断上传材料是否存在审计合规风险，并列出需要人工复核的重点。";

function App() {
  const [files, setFiles] = useState<File[]>([]);
  const [question, setQuestion] = useState(defaultQuestion);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const fileNames = useMemo(() => files.map((file) => file.name).join(", "), [files]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFiles(Array.from(event.target.files ?? []));
    setResult(null);
    setError("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!question.trim()) {
      setError("请输入审核问题。");
      return;
    }

    if (files.length === 0) {
      setError("请至少选择一个文件。");
      return;
    }

    setLoading(true);
    try {
      const response = await analyzeFiles(files, question.trim());
      setResult(response);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "分析请求失败。");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="input-panel">
          <div className="brand-row">
            <div className="brand-mark">AC</div>
            <div>
              <h1>审计合规智能分析</h1>
              <p>M0+ Demo</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="analysis-form">
            <label className="field-label" htmlFor="files">
              上传材料
            </label>
            <div className="file-input-wrap">
              <UploadCloud size={24} aria-hidden="true" />
              <input
                id="files"
                type="file"
                multiple
                accept=".txt,.md,.csv"
                onChange={handleFileChange}
              />
              <span>{files.length > 0 ? `${files.length} 个文件已选择` : "选择 txt / md / csv 文件"}</span>
            </div>
            {files.length > 0 && <p className="file-names">{fileNames}</p>}

            <label className="field-label" htmlFor="question">
              审核问题
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={8}
            />

            {error && <div className="error-box">{error}</div>}

            <button type="submit" disabled={loading} className="primary-button">
              {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Play size={18} aria-hidden="true" />}
              {loading ? "正在分析..." : "开始分析"}
            </button>
          </form>
        </aside>

        <section className="result-panel">
          <div className="result-section answer-section">
            <div className="section-heading">
              <FileText size={18} aria-hidden="true" />
              <h2>AI 初步审核意见</h2>
            </div>
            {result ? (
              <pre className="answer-text">{result.answer_text}</pre>
            ) : (
              <div className="empty-state">等待分析结果</div>
            )}
          </div>

          <div className="result-grid">
            <div className="result-section">
              <h2>文件解析状态</h2>
              {result?.parsed_files.length ? (
                <div className="file-list">
                  {result.parsed_files.map((file) => (
                    <article className="file-card" key={file.filename}>
                      <div className="file-card-header">
                        <strong>{file.filename}</strong>
                        <span className={`status-pill status-${file.status}`}>{file.status}</span>
                      </div>
                      {file.error && <p className="file-error">{file.error}</p>}
                      <p className="preview-text">{file.preview || "暂无可用预览"}</p>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-state compact">暂无解析结果</div>
              )}
            </div>

            <div className="result-section">
              <h2>制度引用片段</h2>
              {result?.retrieved_regulations.length ? (
                <div className="file-list">
                  {result.retrieved_regulations.map((chunk) => (
                    <article className="file-card" key={chunk.chunk_id}>
                      <strong>{chunk.source_file}</strong>
                      <p className="preview-text">{chunk.content}</p>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="empty-state compact">未检索到相关制度</div>
              )}
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

export default App;
