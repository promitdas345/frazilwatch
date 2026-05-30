const ORCHESTRATE_WORKFLOW = [
  {
    agent: "climatology_agent",
    tool_endpoint: "get_frazil_risk",
    description: "Fetches live Environment Canada weather data and assesses frazil ice formation risk at Bay d'Espoir.",
  },
  {
    agent: "dispatch_agent",
    tool_endpoint: "get_lil_load · get_maritime_headroom · get_bde_unit_status",
    description: "Reads simulated grid telemetry to assess Labrador-Island Link headroom and Bay d'Espoir unit capacity.",
  },
  {
    agent: "frazilwatch_supervisor",
    tool_endpoint: "coordinates climatology_agent + dispatch_agent",
    description: "Applies deterministic conflict-resolution rules and issues the final JSON action manifest with justification.",
  },
]

export function AgentTimeline() {
  const workflow = ORCHESTRATE_WORKFLOW
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
        <strong>IBM watsonx Orchestrate</strong> coordinates the three agents above using{" "}
        <strong>llama-3-3-70b-instruct</strong>. The supervisor applies deterministic rules to resolve
        conflicts between frazil risk and grid-capacity limits.
      </div>
    </div>
  )
}
