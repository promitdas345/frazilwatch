export function Report({ data }) {
  if (!data) return null
  const { narrative, ai_enhanced, ai_source, generated_at, risk_level, risk_score, protocol } = data

  return (
    <div className="report-section">
      <div className="section-title" style={{ marginBottom: 12 }}>
        Situation Report — Llama 3.3 70B Instruct
        <span
          className={`ai-badge ${ai_enhanced ? 'enhanced' : 'template'}`}
          style={{ marginLeft: 10 }}
        >
          {ai_enhanced ? '✓ watsonx.ai' : 'local template'}
        </span>
      </div>

      <div className="report-narrative">{narrative}</div>

      <div className="report-meta">
        <div className="report-meta-item"><strong>Risk Level:</strong> {risk_level}</div>
        <div className="report-meta-item"><strong>Score:</strong> {risk_score}/100</div>
        <div className="report-meta-item"><strong>Protocol:</strong> {protocol}</div>
        <div className="report-meta-item">
          <strong>Generated:</strong> {generated_at ? new Date(generated_at).toLocaleString() : '—'}
        </div>
        <div className="report-meta-item"><strong>AI Source:</strong> {ai_source}</div>
      </div>
    </div>
  )
}
