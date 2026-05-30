function SourceBadge({ quality }) {
  return <span className={`source-badge ${quality}`}>{quality}</span>
}

export function DataCards({ weather, marine }) {
  return (
    <div className="data-cards">
      <WeatherCard data={weather} />
      <MarineCard data={marine} />
    </div>
  )
}

function WeatherCard({ data }) {
  if (!data) return null
  const q = data.data_quality
  return (
    <div className="data-card">
      <div className="data-card-title"><span>🌡️</span> Weather Conditions <SourceBadge quality={q} /></div>
      <div className="data-field">
        <span className="data-field-label">Air Temperature</span>
        <span className="data-field-value">{data.air_temp_c}°C</span>
      </div>
      <div className="data-field">
        <span className="data-field-label">Wind Speed</span>
        <span className="data-field-value">{data.wind_speed_kmh} km/h {data.wind_direction}</span>
      </div>
      <div className="data-field">
        <span className="data-field-label">Conditions</span>
        <span className="data-field-value" style={{ fontSize: 12 }}>{data.forecast_summary}</span>
      </div>
      <div className="data-field">
        <span className="data-field-label">Observation Time</span>
        <span className="data-field-value" style={{ fontSize: 12 }}>
          {data.timestamp ? new Date(data.timestamp).toLocaleString() : '—'}
        </span>
      </div>
      <div className="data-source-line">Source: {data.source}</div>
    </div>
  )
}

function MarineCard({ data }) {
  if (!data) return null
  const q = data.data_quality
  return (
    <div className="data-card">
      <div className="data-card-title"><span>🌊</span> Marine Conditions <SourceBadge quality={q} /></div>
      <div className="data-field">
        <span className="data-field-label">Water Temperature</span>
        <span className="data-field-value">{data.water_temp_c}°C</span>
      </div>
      <div className="data-field">
        <span className="data-field-label">Wave Height</span>
        <span className="data-field-value">{data.wave_height_m} m</span>
      </div>
      <div className="data-field">
        <span className="data-field-label">Current Speed</span>
        <span className="data-field-value">{data.current_speed_mps} m/s</span>
      </div>
      <div className="data-field">
        <span className="data-field-label">Salinity</span>
        <span className="data-field-value">{data.salinity_ppt} ppt</span>
      </div>
      <div className="data-field">
        <span className="data-field-label">Summary</span>
        <span className="data-field-value" style={{ fontSize: 12 }}>{data.marine_summary}</span>
      </div>
      <div className="data-source-line">Source: {data.source}</div>
    </div>
  )
}
