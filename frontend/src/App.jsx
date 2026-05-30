import { useState } from 'react'
import { Header } from './components/Header.jsx'
import { RiskDisplay } from './components/RiskDisplay.jsx'
import { AgentTimeline } from './components/AgentTimeline.jsx'
import { DataCards } from './components/DataCards.jsx'
import { GridMap } from './components/GridMap.jsx'
import { Recommendations } from './components/Recommendations.jsx'
import { Report } from './components/Report.jsx'
import { OrchestratePanel } from './components/OrchestratePanel.jsx'

const API = 'http://localhost:8000'

export default function App() {
  const [lat, setLat] = useState(47.93)
  const [lon, setLon] = useState(-55.75)
  const [locationName, setLocationName] = useState("Bay d'Espoir, NL")
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [orchestrateData, setOrchestrateData] = useState(null)
  const [orchestrateLoading, setOrchestrateLoading] = useState(false)

  const analyze = async (demoMode = false) => {
    setLoading(true)
    setOrchestrateLoading(true)
    setError(null)
    setResults(null)
    setOrchestrateData(null)

    // Call both endpoints in parallel
    const pipeline = fetch(`${API}/analyze-risk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat, lon, location_name: locationName, demo_mode: demoMode }),
    })

    const orchestrate = fetch(`${API}/orchestrate-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ demo_mode: demoMode, message: '' }),
    })

    try {
      const res = await pipeline
      if (!res.ok) throw new Error(`API returned ${res.status}`)
      setResults(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }

    try {
      const oRes = await orchestrate
      setOrchestrateData(await oRes.json())
    } catch (e) {
      setOrchestrateData({ error: e.message, response: null })
    } finally {
      setOrchestrateLoading(false)
    }
  }

  return (
    <div className="app">
      <Header />

      <main className="main">
        {/* Input panel */}
        <section className="input-panel">
          <div className="input-row">
            <div className="field">
              <label>Location</label>
              <input
                value={locationName}
                onChange={e => setLocationName(e.target.value)}
                placeholder="Location name"
              />
            </div>
            <div className="field field-sm">
              <label>Latitude</label>
              <input type="number" value={lat} onChange={e => setLat(+e.target.value)} step="0.01" />
            </div>
            <div className="field field-sm">
              <label>Longitude</label>
              <input type="number" value={lon} onChange={e => setLon(+e.target.value)} step="0.01" />
            </div>
          </div>
          <div className="btn-row">
            <button className="btn-primary" onClick={() => analyze(false)} disabled={loading}>
              {loading ? 'Analyzing…' : 'Analyze Live Conditions'}
            </button>
            <button className="btn-demo" onClick={() => analyze(true)} disabled={loading}>
              Demo Scenario (Jan 2026)
            </button>
          </div>
          <p className="input-hint">
            <strong>Demo Scenario</strong> uses the reference conditions from the January 2026 frazil ice event
            that shut Bay d'Espoir down for the first time since 1967.
          </p>
        </section>

        {/* Error */}
        {error && (
          <div className="error-banner">
            <strong>Error:</strong> {error} — is the backend running on port 8000?
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="loading-panel">
            <div className="spinner" />
            <p>IBM watsonx Orchestrate agents are running…</p>
            <p className="loading-sub">Weather Agent → Marine Agent → Risk Agent → Advisor → Report</p>
          </div>
        )}

        {/* Results */}
        {results && !loading && (
          <>
            {results.demo_mode && (
              <div className="demo-banner">
                Demo Scenario — January 2026 reference conditions (not live data)
              </div>
            )}
            <AgentTimeline />
            <RiskDisplay risk={results.risk} />
            <DataCards weather={results.weather} marine={results.marine} />
            <GridMap cells={results.risk?.grid_cells} gridState={results.risk?.grid_state} />
            <Recommendations data={results.recommendations} />
            <OrchestratePanel data={orchestrateData} loading={orchestrateLoading} demoMode={results.demo_mode} pipelineResults={results} />
            <Report data={results.report} />
          </>
        )}
      </main>

      <footer className="footer">
        <span>FrazilWatch · Team Namles · IBM × MUN watsonx Hackathon 2026</span>
        <span>Powered by IBM watsonx Orchestrate + Llama 3.3 70B Instruct</span>
      </footer>
    </div>
  )
}
