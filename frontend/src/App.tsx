import { useEffect, useState } from "react";
import { checkBackendHealth } from "./services/api";
import "./App.css";
function App() {
  const [status, setStatus] = useState("Checking backend...");
  const [error, setError] = useState("");
useEffect(() => {
checkBackendHealth()
.then((result) => {
setStatus($DIL0: $DIL1);
setError("");
})
.catch((err: unknown) => {
setStatus("Backend connection failed");
setError(err instanceof Error ? err.message : "Unknown error");
});
}, []);
return (
    <main style={{ maxWidth: 900, margin: "60px auto", padding: 24 }}>
      <h1>Tender Intelligence</h1>
      <p>PQR-based tender eligibility and decision platform</p>
<section>
        <h2>Backend connection</h2>
        <p>{status}</p>
        {error && <p role="alert">{error}</p>}
      </section>
    </main>
  );
}
export default App;
