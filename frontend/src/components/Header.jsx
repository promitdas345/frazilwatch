export function Header() {
  return (
    <header className="header">
      <div className="header-brand">
        <div className="header-logo">Frazil<span>Watch</span></div>
        <div className="header-tag">LIVE</div>
      </div>
      <div className="header-right">
        <span className="header-ibm">
          Powered by <strong>IBM watsonx Orchestrate</strong> + Llama 3.3 70B Instruct
        </span>
      </div>
    </header>
  )
}
