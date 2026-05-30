export function AgentTimeline({ workflow }) {
  if (!workflow) return null
  return (
    <div className="agent-timeline">
      <div className="section-title">IBM watsonx Orchestrate — Agent Workflow</div>
      <div className="timeline-steps">
        {workflow.map((step, i) => (
          <div className="timeline-step" key={step.agent}>
            <div className="timeline-step-inner">
              <div className="timeline-dot">{i + 1}</div>
              <div className="timeline-info">
                <div className="timeline-agent">{step.agent}</div>
                <div className="timeline-endpoint">{step.tool_endpoint}</div>
                <div className="timeline-desc">{step.description}</div>
              </div>
            </div>
            {i < workflow.length - 1 && <div className="timeline-connector" />}
          </div>
        ))}
      </div>
      <div className="orchestrate-note">
        <strong>IBM watsonx Orchestrate</strong> coordinates the agents above.
        Each agent calls its designated backend tool endpoint. The supervisor resolves conflicts using deterministic rules.
      </div>
    </div>
  )
}
