import React, { useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import InboxPage from "./pages/InboxPage.jsx";
import LeadPage from "./pages/LeadPage.jsx";
import WebFormPage from "./pages/WebFormPage.jsx";
import SlotsPage from "./pages/SlotsPage.jsx";
import BookingsPage from "./pages/BookingsPage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";
import ServicesPage from "./pages/ServicesPage.jsx";
import AnalyticsPage from "./pages/AnalyticsPage.jsx";
import { UI_TEXT, translateErrorMessage } from "./i18n.js";
import StatusBadge from "./components/StatusBadge.jsx";
import ErrorAlert from "./components/ErrorAlert.jsx";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

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

    const navLinkStyle = ({ isActive }) => ({
        padding: "6px 10px",
        borderRadius: "999px",
        fontSize: "13px",
        textDecoration: "none",
        color: isActive ? "#0b4f6c" : "#374151",
        backgroundColor: isActive ? "#e0f2fe" : "transparent",
        border: isActive ? "1px solid #7dd3fc" : "1px solid transparent"
    });

    return (
        <div
            style={{
                fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
                padding: "16px",
                backgroundColor: "#f3f4f6",
                minHeight: "100vh",
                boxSizing: "border-box"
            }}
        >
            <header
                style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: "16px"
                }}
            >
                <div>
                    <h2 style={{ margin: 0 }}>{UI_TEXT.APP_TITLE}</h2>
                    <nav
                        style={{
                            marginTop: "8px",
                            display: "flex",
                            flexWrap: "wrap",
                            gap: "8px"
                        }}
                    >
                        <NavLink to="/" style={navLinkStyle} end>
                            {UI_TEXT.NAV_INBOX}
                        </NavLink>
                        <NavLink to="/bookings" style={navLinkStyle}>
                            {UI_TEXT.NAV_BOOKINGS}
                        </NavLink>
                        <NavLink to="/slots" style={navLinkStyle}>
                            {UI_TEXT.NAV_SLOTS}
                        </NavLink>
                        <NavLink to="/web" style={navLinkStyle}>
                            {UI_TEXT.NAV_WEB_FORM}
                        </NavLink>
                        <NavLink to="/services" style={navLinkStyle}>
                            {UI_TEXT.NAV_SERVICES}
                        </NavLink>
                        <NavLink to="/analytics" style={navLinkStyle}>
                            {UI_TEXT.NAV_ANALYTICS}
                        </NavLink>
                        <NavLink to="/settings" style={navLinkStyle}>
                            {UI_TEXT.NAV_SETTINGS}
                        </NavLink>
                    </nav>
                </div>
                <div style={{ textAlign: "right" }}>
                    <button
                        type="button"
                        onClick={checkApi}
                        style={{
                            padding: "6px 10px",
                            borderRadius: "6px",
                            border: "1px solid #d1d5db",
                            backgroundColor: "#ffffff",
                            cursor: "pointer",
                            fontSize: "13px"
                        }}
                    >
                        {UI_TEXT.CHECK_API}
                    </button>
                    {healthStatus && (
                        <div style={{ marginTop: "4px" }}>
                            <StatusBadge
                                label={UI_TEXT.CHECK_API_OK}
                                tone="success"
                            />
                        </div>
                    )}
                    {healthError && (
                        <div style={{ marginTop: "4px", maxWidth: "260px" }}>
                            <ErrorAlert
                                title={UI_TEXT.CHECK_API_ERROR}
                                message={translateErrorMessage(healthError)}
                            />
                        </div>
                    )}
                </div>
            </header>
            <main
                style={{
                    backgroundColor: "#ffffff",
                    borderRadius: "12px",
                    padding: "16px",
                    boxShadow: "0 10px 15px -3px rgba(15, 23, 42, 0.12)",
                    border: "1px solid #e5e7eb"
                }}
            >
                <Routes>
                    <Route path="/" element={<InboxPage apiBase={API_BASE} />} />
                    <Route path="/bookings" element={<BookingsPage apiBase={API_BASE} />} />
                    <Route path="/lead/:id" element={<LeadPage apiBase={API_BASE} />} />
                    <Route path="/slots" element={<SlotsPage apiBase={API_BASE} />} />
                    <Route path="/web" element={<WebFormPage apiBase={API_BASE} />} />
                    <Route path="/settings" element={<SettingsPage />} />
                    <Route path="/services" element={<ServicesPage />} />
                    <Route path="/analytics" element={<AnalyticsPage />} />
                </Routes>
            </main>
        </div>
    );
}

export default App;

