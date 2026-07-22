import { useState } from "react";
import Status from "./pages/Status";
import Personnel from "./pages/Personnel";
import Events from "./pages/Events";

export default function App() {
  const [page, setPage] = useState("status");

  return (
    <>
      <nav>
        <h1>FACEGUARD</h1>
        <a href="#" className={page === "status"    ? "active" : ""} onClick={() => setPage("status")}>Status</a>
        <a href="#" className={page === "personnel" ? "active" : ""} onClick={() => setPage("personnel")}>Personnel</a>
        <a href="#" className={page === "events"    ? "active" : ""} onClick={() => setPage("events")}>Events</a>
      </nav>
      <div className="page">
        {page === "status"    && <Status />}
        {page === "personnel" && <Personnel />}
        {page === "events"    && <Events />}
      </div>
    </>
  );
}