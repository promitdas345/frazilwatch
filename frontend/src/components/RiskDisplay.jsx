export function RiskDisplay({ risk }) {
  if (!risk) return null
  const { risk_score, risk_level, contributing_factors, scoring_breakdown } = risk
  const maxes = { temperature: 40, wind: 30, water_temperature: 20, turbulence: 10 }

  return (
    <div className="risk-display">
      <div className={`risk-score-circle ${risk_level}`}>
        <div className="risk-score-num">{risk_score}</div>
        <div className="risk-score-label">/ 100</div>
      </div>

      <div className="risk-info">
        <div className={`risk-level-badge ${risk_level}`}>{risk_level} RISK</div>
        <div className="risk-factors">
          {contributing_factors?.map(f => (
            <div className="factor-row" key={f.factor}>
              <div className={`factor-dot ${f.triggered ? 'triggered' : 'ok'}`} />
              <span className="factor-label">{f.factor}:</span>
              <span className="factor-value">{f.value}</span>
              <span className="factor-threshold">threshold {f.threshold}</span>
            </div>
          ))}
        </div>
      </div>

      {scoring_breakdown && (
        <div>
          <div className="section-title" style={{ marginBottom: 10 }}>Score Breakdown</div>
          <div className="scoring-breakdown">
            {Object.entries(scoring_breakdown).map(([key, val]) => (
              <div className="score-bar-item" key={key}>
                <div className="score-bar-label">{key.replace('_', ' ')}</div>
                <div className="score-bar">
                  <div
                    className="score-bar-fill"
                    style={{ width: `${(val / maxes[key]) * 100}%` }}
                  />
                </div>
                <div className="score-bar-val">{val} / {maxes[key]}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
