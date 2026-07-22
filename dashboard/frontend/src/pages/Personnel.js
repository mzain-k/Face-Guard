import { useEffect, useState } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000";

export default function Personnel() {
  const [people, setPeople] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    axios.get(`${API}/personnel`)
      .then(r => { setPeople(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const remove = (name) => {
    if (!window.confirm(`Remove ${name}?`)) return;
    axios.delete(`${API}/personnel/${encodeURIComponent(name)}`)
      .then(() => load())
      .catch(e => alert("Failed: " + e.message));
  };

  if (loading) return <p className="empty">Loading...</p>;

  return (
    <>
      <p className="page-title">Personnel ({people.length})</p>
      {people.length === 0 && (
        <p className="empty">No personnel enrolled. Run enroll.py to add people.</p>
      )}
      {people.map(p => (
        <div className="person-card" key={p.name}>
          <div className="person-info">
            <h4>{p.name}</h4>
            <p>{p.role} &nbsp;|&nbsp;
              <span className={`badge ${p.access}`}>{p.access}</span>
            </p>
          </div>
          <button className="btn btn-danger" onClick={() => remove(p.name)}>
            Remove
          </button>
        </div>
      ))}
    </>
  );
}