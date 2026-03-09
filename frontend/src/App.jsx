import React, { useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import InboxPage from "./pages/InboxPage.jsx";
import LeadPage from "./pages/LeadPage.jsx";
import WebFormPage from "./pages/WebFormPage.jsx";
import SlotsPage from "./pages/SlotsPage.jsx";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

function App() {
    const [healthStatus, setHealthStatus] = useState(null);
    const [healthError, setHealthError] = useState(null);

    const checkApi = async () => {
        setHealthError(null);
        try {
            const response = await fetch(`${API_BASE}/health`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            setHealthStatus(JSON.stringify(data));
        } catch (error) {
            setHealthStatus(null);
            setHealthError(error.message);
        }
    };

    return (
        <div style={{ fontFamily: "system-ui, sans-serif", padding: "16px" }}>
            <header
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "16px"
                }}
            >
                <div>
                    <h2 style={{ margin: 0 }}>Neuro-Salesman Inbox</h2>
                    <nav style={{ marginTop: "8px", display: "flex", gap: "12px" }}>
                        <Link to="/">Inbox</Link>
                        <Link to="/slots">Слоты</Link>
                        <Link to="/web">Web форма</Link>
                    </nav>
                </div>
                <div>
                    <button type="button" onClick={checkApi}>
                        Check API
                    </button>
                    {healthStatus && (
                        <div style={{ fontSize: "12px", marginTop: "4px" }}>
                            {healthStatus}
                        </div>
                    )}
                    {healthError && (
                        <div style={{ fontSize: "12px", marginTop: "4px", color: "red" }}>
                            {healthError}
                        </div>
                    )}
                </div>
            </header>
            <main>
                <Routes>
                    <Route path="/" element={<InboxPage apiBase={API_BASE} />} />
                    <Route path="/lead/:id" element={<LeadPage apiBase={API_BASE} />} />
                    <Route path="/slots" element={<SlotsPage apiBase={API_BASE} />} />
                    <Route path="/web" element={<WebFormPage apiBase={API_BASE} />} />
                </Routes>
            </main>
        </div>
    );
}

export default App;

