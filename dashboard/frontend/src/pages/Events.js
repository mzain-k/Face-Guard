import { useEffect, useState } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000";

export default function Events() {
  const [events, setEvents]   = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    axios.get(`${API}/events?limit=100`)
      .then(r => { setEvents(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <p className="empty">Loading...</p>;

  return (
    <>
      <p className="page-title">Event Log</p>
      {events.length === 0 && (
        <p className="empty">No events yet — run main.py to start detecting.</p>
      )}
      {events.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Camera</th>
                <th>Name</th>
                <th>Access</th>
                <th>Confidence</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {events.map(e => (
                <tr key={e.id}>
                  <td style={{ color: "#888", fontSize: "12px" }}>{e.timestamp}</td>
                  <td>{e.camera_id}</td>
                  <td>{e.name}</td>
                  <td><span className={`badge ${e.access}`}>{e.access}</span></td>
                  <td>{(e.confidence * 100).toFixed(1)}%</td>
                  <td style={{ textTransform: "capitalize" }}>{e.action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}