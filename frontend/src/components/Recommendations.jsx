export function Recommendations({ data }) {
  if (!data) return null
  const { protocol, obvious_fix_blocked, blocked_reason, actions, approval_text, summary } = data

  return (
    <div className="recommendations-section">
      <div className="section-title">Operations Advisor — Recommended Actions</div>
      <div className={`protocol-badge ${protocol}`}>{protocol.replace(/_/g, ' ')}</div>

      {obvious_fix_blocked && (
        <div className="blocked-banner">
          <div className="blocked-icon">🚫</div>
          <div className="blocked-text">
            <strong>Obvious Fix Blocked: Increase LIL Transfer</strong>
            <span>{blocked_reason}</span>
          </div>
        </div>
      )}

      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 14 }}>{summary}</p>

      <div className="action-list">
        {actions.map((action, i) => (
          <div className="action-item" key={action.id}>
            <div className={`action-num ${action.urgency}`}>{i + 1}</div>
            <div className="action-body">
              <div className="action-title">{action.action}</div>
              <div className="action-detail">{action.detail}</div>
              <div className="action-urgency">{action.urgency?.replace(/_/g, ' ')}</div>
            </div>
          </div>
        ))}
      </div>

      {approval_text && (
        <div className="approval-box">
          <strong>Human Approval Required: </strong>{approval_text}
        </div>
      )}
    </div>
  )
}
