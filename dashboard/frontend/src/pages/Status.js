import { useEffect, useState } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000";

export default function Status() {
  const [status, setStatus] = useState(null);
  const [error, setError]   = useState(null);

  useEffect(() => {
    axios.get(`${API}/status`)
      .then(r => setStatus(r.data))
      .catch(() => setError("Backend offline — start uvicorn first"));

    const interval = setInterval(() => {
      axios.get(`${API}/status`)
        .then(r => setStatus(r.data))
        .catch(() => {});
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  if (error)  return <p className="error">{error}</p>;
  if (!status) return <p className="empty">Connecting to backend...</p>;

  return (
    <>
      <p className="page-title">System Status</p>
      <div className="stat-grid">
        <div className="stat">
          <h3 style={{ color: "#00e676" }}>ONLINE</h3>
          <p>System</p>
        </div>
        <div className="stat">
          <h3>{status.personnel_count}</h3>
          <p>Enrolled Personnel</p>
        </div>
        <div className="stat">
          <h3 style={{ fontSize: "16px", paddingTop: "8px" }}>{status.timestamp}</h3>
          <p>Last Updated</p>
        </div>
      </div>
      <div className="card">
        <p style={{ color: "#888", fontSize: "13px" }}>Deployment</p>
        <p style={{ fontSize: "18px", marginTop: "8px" }}>{status.deployment}</p>
      </div>
    </>
  );
}