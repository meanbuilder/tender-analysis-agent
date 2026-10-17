import { useEffect, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type Health = { status: string; service: string; version?: string };
type NavKey =
  | "Dashboard"
  | "New Tender"
  | "My Tenders"
  | "PQR Checklist"
  | "Bid Decision"
  | "Evidence Bank"
  | "Reports (Excel)";

const navItems: { label: NavKey; icon: string }[] = [
  { label: "Dashboard", icon: "🖥️" },
  { label: "New Tender", icon: "📁" },
  { label: "My Tenders", icon: "🗂️" },
  { label: "PQR Checklist", icon: "📋" },
  { label: "Bid Decision", icon: "⚖️" },
  { label: "Evidence Bank", icon: "🗄️" },
  { label: "Reports (Excel)", icon: "📊" },
];

function App() {
  const [activeNav, setActiveNav] = useState<NavKey>("Dashboard");
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API_URL}/api/health`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<Health>;
      })
      .then((data) => {
        setHealth(data);
        setHealthError("");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setHealth(null);
        setHealthError(error instanceof Error ? error.message : "Connection failed");
      });
    return () => controller.abort();
  }, []);

  function navigate(page: NavKey) {
    setActiveNav(page);
    setMobileNavOpen(false);
  }

  function openNewTender() {
    navigate("New Tender");
  }

  return (
    <div className="xp-app-shell">
      <header className="xp-titlebar">
        <span className="titlebar-appicon" aria-hidden="true">▣</span>
        <strong className="titlebar-title">Tender Intelligence – TPP Boilers</strong>
        <div className="window-controls" aria-label="Window controls">
          <button type="button" title="Minimize" aria-label="Minimize">_</button>
          <button type="button" title="Maximize" aria-label="Maximize">□</button>
          <button type="button" className="close" title="Close" aria-label="Close">×</button>
        </div>
      </header>

      <nav className="menu-bar" aria-label="Application menu">
        {["File", "Edit", "View", "Tools", "Actions", "Help"].map((item) => (
          <button type="button" key={item} onClick={() => item === "File" && openNewTender()}>{item}</button>
        ))}
      </nav>

      <nav className="toolbar" aria-label="Quick toolbar">
        <button type="button" onClick={() => navigate("Dashboard")}><span>🏠</span> Home</button>
        <button type="button" onClick={openNewTender}><span>📂</span> New Tender</button>
        <button type="button" onClick={() => navigate("My Tenders")}><span>🔎</span> Search</button>
        <button type="button" onClick={() => navigate("Reports (Excel)")}><span>📑</span> Reports</button>
        <button type="button" onClick={() => navigate("Evidence Bank")}><span>🗄️</span> Evidence Bank</button>
      </nav>

      <section className="brand-strip">
        <div className="brand-mark" aria-label="TPP Boilers"><b>TPP</b><span>BOILERS</span></div>
        <div className="brand-divider" />
        <div className="brand-copy">
          <h1>TENDER INTELLIGENCE</h1>
          <p>PQR-BASED ELIGIBILITY ANALYSIS AND BID DECISION MANAGEMENT</p>
        </div>
        <div className="user-box">
          <span>User: <b>Not Signed In</b></span>
          <button type="button" className="xp-button" onClick={() => window.alert("Firebase Authentication will be connected in the next phase.")}>🔑 Sign In</button>
        </div>
      </section>

      <div className="mobile-nav-bar">
        <button type="button" className="xp-button mobile-menu-button" aria-expanded={mobileNavOpen} onClick={() => setMobileNavOpen((open) => !open)}>
          ☰ {mobileNavOpen ? "Hide navigation" : "Navigation"}
        </button>
        <span>{activeNav}</span>
      </div>

      <div className="workspace">
        <aside className={`sidebar ${mobileNavOpen ? "sidebar-open" : ""}`} aria-label="Main navigation">
          <div className="panel-title">Navigation <span aria-hidden="true">⌃</span></div>
          {navItems.map((item) => (
            <button type="button" key={item.label} className={`nav-item ${activeNav === item.label ? "selected" : ""}`}
              aria-current={activeNav === item.label ? "page" : undefined} onClick={() => navigate(item.label)}>
              <span className="nav-icon" aria-hidden="true">{item.icon}</span><span>{item.label}</span>
            </button>
          ))}
        </aside>

        <main className="main-area">
          {activeNav === "Dashboard" ? (
            <>
              <div className="top-panels">
                <section className="xp-panel welcome-panel">
                  <div className="panel-title">Welcome</div>
                  <div className="welcome-content">
                    <div className="welcome-icon" aria-hidden="true">🖥️</div>
                    <div>
                      <h2>Welcome to Tender Intelligence</h2>
                      <p>Upload tender documents, extract PQR eligibility criteria, validate against company evidence, and get GO / NO-GO / HOLD recommendations with source references.</p>
                    </div>
                  </div>
                </section>
                <section className="xp-panel status-panel">
                  <div className="panel-title">System Status</div>
                  <div className="status-body">
                    <div className="status-line">
                      <span className={`led ${health ? "online" : "offline"}`} />
                      <b>Backend API</b>
                      <strong className={health ? "good" : "bad"}>{health ? "Connected" : "Disconnected"}</strong>
                    </div>
                    <hr />
                    <dl>
                      <dt>Service</dt><dd>{health?.service ?? "tender-intelligence-api"}</dd>
                      <dt>Version</dt><dd>{health?.version ?? "0.1.0"}</dd>
                    </dl>
                    {healthError && <p className="error-text">Connection error: {healthError}</p>}
                  </div>
                </section>
              </div>

              <div className="workflow-grid">
                <section className="xp-panel workflow-panel">
                  <div className="panel-title">1. New Tender</div>
                  <div className="workflow-content">
                    <div className="workflow-head"><span className="large-icon" aria-hidden="true">📂</span><h2>Upload Tender Documents</h2></div>
                    <ul><li>Upload PDF tender documents</li><li>Extract PQR and eligibility criteria</li><li>Capture key dates and details</li></ul>
                    <button type="button" className="xp-button action-button" onClick={openNewTender}>📄 Upload Tender</button>
                  </div>
                </section>
                <section className="xp-panel workflow-panel">
                  <div className="panel-title">2. PQR Checklist</div>
                  <div className="workflow-content">
                    <div className="workflow-head"><span className="large-icon" aria-hidden="true">📋</span><h2>Review Eligibility Criteria</h2></div>
                    <ul><li>AI-extracted PQR requirements</li><li>Match with company evidence</li><li>View page references and sources</li></ul>
                    <button type="button" className="xp-button action-button" onClick={() => navigate("PQR Checklist")}>📑 Open Checklist</button>
                  </div>
                </section>
                <section className="xp-panel workflow-panel">
                  <div className="panel-title">3. Bid Decision</div>
                  <div className="workflow-content">
                    <div className="workflow-head"><span className="large-icon" aria-hidden="true">⚖️</span><h2>Get Bid Recommendation</h2></div>
                    <ul><li>GO / NO-GO / HOLD decision</li><li>Evidence-backed reasoning</li><li>Download Excel report</li></ul>
                    <button type="button" className="xp-button action-button" onClick={() => navigate("Bid Decision")}>📊 View Decision</button>
                  </div>
                </section>
              </div>

              <div className="bottom-panels">
                <section className="xp-panel recent-panel">
                  <div className="panel-title">Recent Tenders</div>
                  <div className="table-wrap">
                    <table>
                      <thead><tr><th>#</th><th>Tender Title</th><th>Authority</th><th>Due Date</th><th>Status</th><th>Decision</th></tr></thead>
                      <tbody>{[1, 2, 3].map((n) => <tr key={n}><td>{n}</td><td>—</td><td>—</td><td>—</td><td>Not started</td><td>—</td></tr>)}</tbody>
                    </table>
                  </div>
                </section>
                <section className="xp-panel quick-panel">
                  <div className="panel-title">Quick Actions</div>
                  <button type="button" onClick={openNewTender}>📄 Upload New Tender</button>
                  <button type="button" onClick={() => navigate("My Tenders")}>🔎 Search Existing Tenders</button>
                  <button type="button" onClick={() => navigate("Reports (Excel)")}>📊 View Excel Reports</button>
                  <button type="button" onClick={() => navigate("Evidence Bank")}>🗄️ Manage Evidence Bank</button>
                </section>
              </div>
            </>
          ) : (
            <section className="xp-panel page-panel">
              <div className="panel-title">{activeNav}</div>
              {activeNav === "New Tender" ? (
                <div className="form-content">
                  <h2>New Tender Registration</h2>
                  <p>Select a PDF tender document to prepare it for processing.</p>
                  <label className="field-label" htmlFor="tender-file">Tender document (PDF)</label>
                  <input id="tender-file" type="file" accept=".pdf,application/pdf" onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} />
                  {selectedFile && <p className="selected-file">Selected: <b>{selectedFile.name}</b> ({Math.ceil(selectedFile.size / 1024)} KB)</p>}
                  <div className="form-actions"><button type="button" className="xp-button" onClick={() => window.alert(selectedFile ? `Selected ${selectedFile.name}. Upload API wiring is the next step.` : "Please select a PDF first.")}>Continue to Processing</button></div>
                  <p className="notice">Current stage: local file selection only; the file is not uploaded or saved yet.</p>
                </div>
              ) : (
                <div className="placeholder-page">
                  <span className="large-icon" aria-hidden="true">{navItems.find((item) => item.label === activeNav)?.icon ?? "📄"}</span>
                  <h2>{activeNav}</h2>
                  <p>This workspace will be connected to the backend in the next implementation step.</p>
                  {activeNav === "PQR Checklist" && <p>Planned columns: requirement, mandatory status, company evidence, source document/page, evaluation and notes.</p>}
                  {activeNav === "Bid Decision" && <p>Mandatory failure → NO-GO. Unresolved mandatory criteria → HOLD. GO only when all mandatory criteria pass.</p>}
                </div>
              )}
            </section>
          )}
        </main>
      </div>
      <footer className="status-bar"><span>Ready</span><span>Tender Intelligence | React + FastAPI | Development</span></footer>
    </div>
  );
}

export default App;
