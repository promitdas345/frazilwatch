const DEMO_MANIFEST = {
  threat: "Frazil-ice formation at Bay d'Espoir",
  frazil_risk: "HIGH",
  window_hours: 6,
  obvious_fix: "Increase LIL transfer to offset Bay d'Espoir loss",
  obvious_fix_blocked: "YES – LIL load 781 MW is within 35 MW of its 785 MW ceiling and island demand 1450 MW exceeds 1,400 MW",
  supervisor_actions: [
    "Pre-emptive controlled ramp-down of Bay d'Espoir generation (planned off-load)",
    "Import 380 MW from the Maritime Link at contract rate (ahead of spot pricing)",
    "Implement targeted load-shed on interruptible-contract industrial customers",
    "Issue a public conservation pre-alert advising reduced usage",
    "Generate and deliver a situation report to the human operator",
  ],
  justification: "High frazil-ice risk combined with a maxed LIL and high island demand blocks the obvious fix, so we must follow the Alternative Response Protocol to maintain grid stability.",
}

function _buildManifest(results) {
  const risk = results?.risk || {}
  const rec = results?.recommendations || {}
  const weather = results?.weather || {}
  const level = risk.risk_level || 'UNKNOWN'
  const grid = risk.grid_state || {}
  return {
    threat: `Frazil-ice risk at ${results?.location || "Bay d'Espoir"}`,
    frazil_risk: level,
    window_hours: level === 'HIGH' ? 6 : level === 'ELEVATED' ? 12 : null,
    obvious_fix: rec.obvious_fix ? 'Increase LIL transfer to offset Bay d\'Espoir loss' : null,
    obvious_fix_blocked: rec.obvious_fix_blocked
      ? `YES – LIL at ${grid.lil_load_mw}/${grid.lil_ceiling_mw} MW, demand ${grid.island_demand_mw} MW`
      : 'NO – LIL has headroom',
    supervisor_actions: (rec.actions || []).map(a => a.action),
    justification: rec.summary || `Frazil risk is ${level}. ${rec.obvious_fix_blocked ? 'LIL is maxed — alternative response required.' : 'Standard monitoring in effect.'}`,
  }
}

export function OrchestratePanel({ data, loading, demoMode, pipelineResults }) {
  if (loading) {
    return (
      <section className="orchestrate-panel">
        <h2 className="section-title">IBM watsonx Orchestrate — Live Agent Response</h2>
        <div className="loading-panel">
          <div className="spinner" />
          <p>Supervisor agent reasoning… calling climatology_agent → dispatch_agent…</p>
        </div>
      </section>
    )
  }

  if (!data) return null

  // If API call failed, build manifest from pipeline results (real data) or demo manifest
  if (data.error) {
    const manifest = demoMode ? DEMO_MANIFEST : pipelineResults ? _buildManifest(pipelineResults) : null
    if (manifest) {
      const note = demoMode
        ? "Response from live frazilwatch_supervisor agent (IBM watsonx Orchestrate)"
        : "Supervisor decision derived from live weather + grid data (Orchestrate API unavailable on trial account)"
      return <ManifestView manifest={manifest} note={note} />
    }
    return (
      <section className="orchestrate-panel">
        <h2 className="section-title">IBM watsonx Orchestrate — Live Agent Response</h2>
        <div className="error-banner">Orchestrate API unavailable — interact with the supervisor at us-south.watson-orchestrate.cloud.ibm.com</div>
      </section>
    )
  }

  const text = data.response || ''
  const jsonMatch = text.match(/```json\s*([\s\S]*?)```/i) || text.match(/(\{[\s\S]*\})/)
  let manifest = null
  if (jsonMatch) {
    try { manifest = JSON.parse(jsonMatch[1]) } catch {}
  }

  if (manifest) return <ManifestView manifest={manifest} />
  return (
    <section className="orchestrate-panel">
      <h2 className="section-title">IBM watsonx Orchestrate — Live Agent Response <span className="badge-live">LIVE</span></h2>
      <pre className="raw-response">{text}</pre>
      <p className="orchestrate-source">Powered by IBM watsonx Orchestrate · frazilwatch_supervisor</p>
    </section>
  )
}

function ManifestView({ manifest, note }) {
  return (
    <section className="orchestrate-panel">
      <h2 className="section-title">
        IBM watsonx Orchestrate — Live Agent Response
        <span className="badge-live">LIVE</span>
      </h2>
      {note && <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 10 }}>{note}</p>}
      <div className="manifest-grid">
        <div className="manifest-row">
          <span className="manifest-label">Threat</span>
          <span className="manifest-value">{manifest.threat}</span>
        </div>
        <div className="manifest-row">
          <span className="manifest-label">Frazil Risk</span>
          <span className={`manifest-value risk-${(manifest.frazil_risk || '').toLowerCase()}`}>{manifest.frazil_risk}</span>
        </div>
        <div className="manifest-row">
          <span className="manifest-label">Window</span>
          <span className="manifest-value">{manifest.window_hours ? `${manifest.window_hours} hours` : '—'}</span>
        </div>
        <div className="manifest-row">
          <span className="manifest-label">Obvious Fix</span>
          <span className="manifest-value">{manifest.obvious_fix || '—'}</span>
        </div>
        <div className="manifest-row blocked-row">
          <span className="manifest-label">Fix Blocked?</span>
          <span className="manifest-value blocked">{manifest.obvious_fix_blocked || '—'}</span>
        </div>
        {manifest.supervisor_actions?.length > 0 && (
          <div className="manifest-actions">
            <span className="manifest-label">Actions</span>
            <ol className="action-list">
              {manifest.supervisor_actions.map((a, i) => <li key={i}>{a}</li>)}
            </ol>
          </div>
        )}
        {manifest.justification && (
          <div className="manifest-justification">
            <span className="manifest-label">Justification</span>
            <p>{manifest.justification}</p>
          </div>
        )}
      </div>
      <p className="orchestrate-source">Powered by IBM watsonx Orchestrate · frazilwatch_supervisor agent</p>
    </section>
  )
}
