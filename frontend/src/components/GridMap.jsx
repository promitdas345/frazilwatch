export function GridMap({ cells, gridState }) {
  if (!cells) return null

  const rows = [0, 1, 2, 3].map(r => cells.filter(c => c.row === r).sort((a, b) => a.col - b.col))
  const gs = gridState || {}
  const headroom = (gs.lil_ceiling_mw || 785) - (gs.lil_load_mw || 781)
  const isMaxed = gs.lil_is_maxed

  return (
    <div className="grid-map-section">
      <div className="section-title">Bay d'Espoir Risk Grid</div>
      <div className="grid-layout">
        <div className="grid-cells">
          {rows.flat().map(cell => (
            <div
              key={`${cell.row}-${cell.col}`}
              className={`grid-cell ${cell.risk_level}${cell.is_intake ? ' intake' : ''}`}
              title={`${cell.label}: ${cell.risk_score}/100 (${cell.risk_level})`}
            >
              <span className="cell-label">{cell.label}</span>
              <span className="cell-score">{cell.risk_score}</span>
              {cell.is_intake && <span className="intake-tag">INTAKE</span>}
            </div>
          ))}
        </div>

        <div className="grid-sidebar">
          <div className="grid-legend">
            {['LOW', 'ELEVATED', 'HIGH'].map(l => (
              <div className="legend-item" key={l}>
                <div className={`legend-dot ${l}`} />
                <span>{l}</span>
              </div>
            ))}
          </div>

          {gs.lil_load_mw && (
            <div className="grid-state">
              <div className="grid-state-title">Grid State</div>
              <div className="grid-state-row">
                <span className="label">LIL Load</span>
                <span className={`value ${isMaxed ? 'maxed' : 'ok-val'}`}>
                  {gs.lil_load_mw}/{gs.lil_ceiling_mw} MW
                </span>
              </div>
              <div className="grid-state-row">
                <span className="label">Headroom</span>
                <span className={`value ${isMaxed ? 'maxed' : 'ok-val'}`}>
                  {headroom} MW {isMaxed ? '⚠ MAXED' : ''}
                </span>
              </div>
              <div className="grid-state-row">
                <span className="label">Island Demand</span>
                <span className="value">{gs.island_demand_mw} MW</span>
              </div>
              <div className="grid-state-row">
                <span className="label">BdE at Risk</span>
                <span className="value">{gs.bde_capacity_mw} MW</span>
              </div>
              <div className="grid-state-row">
                <span className="label">Maritime Headroom</span>
                <span className="value ok-val">{gs.maritime_headroom_mw} MW</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
