import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
    UI_TEXT,
    formatLeadStatus,
    getLeadStatusTone,
    translateErrorMessage
} from "../i18n.js";
import StatusBadge from "../components/StatusBadge.jsx";
import ErrorAlert from "../components/ErrorAlert.jsx";

function InboxPage({ apiBase }) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const load = async () => {
            try {
                setLoading(true);
                const response = await fetch(`${apiBase}/inbox/conversations`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                const data = await response.json();
                setItems(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [apiBase]);

    return (
        <div>
            <h3>{UI_TEXT.NAV_INBOX}</h3>
            {loading && <div>Загрузка диалогов…</div>}
            {error && (
                <ErrorAlert
                    title={UI_TEXT.TABLE_ERROR_TITLE}
                    message={translateErrorMessage(error)}
                />
            )}
            {!loading && !error && items.length === 0 && (
                <div>{UI_TEXT.TABLE_EMPTY}</div>
            )}
            {!loading && !error && items.length > 0 && (
                <div style={{ overflowX: "auto" }}>
                    <table
                        style={{
                            width: "100%",
                            borderCollapse: "collapse",
                            fontSize: "13px",
                            marginTop: "8px"
                        }}
                    >
                        <thead>
                            <tr
                                style={{
                                    textAlign: "left",
                                    backgroundColor: "#f9fafb"
                                }}
                            >
                                <th
                                    style={{
                                        padding: "8px",
                                        borderBottom: "1px solid #e5e7eb"
                                    }}
                                >
                                    Лид
                                </th>
                                <th
                                    style={{
                                        padding: "8px",
                                        borderBottom: "1px solid #e5e7eb"
                                    }}
                                >
                                    Канал
                                </th>
                                <th
                                    style={{
                                        padding: "8px",
                                        borderBottom: "1px solid #e5e7eb"
                                    }}
                                >
                                    Последнее сообщение
                                </th>
                                <th
                                    style={{
                                        padding: "8px",
                                        borderBottom: "1px solid #e5e7eb"
                                    }}
                                >
                                    Статус лида
                                </th>
                                <th
                                    style={{
                                        padding: "8px",
                                        borderBottom: "1px solid #e5e7eb"
                                    }}
                                >
                                    Действия
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {items.map((item) => (
                                <tr
                                    key={item.id}
                                    style={{
                                        borderBottom: "1px solid #f3f4f6"
                                    }}
                                >
                                    <td style={{ padding: "8px" }}>
                                        <div
                                            style={{
                                                fontWeight: 600,
                                                marginBottom: "2px"
                                            }}
                                        >
                                            {item.lead.display_name}
                                        </div>
                                        <div
                                            style={{
                                                fontSize: "11px",
                                                color: "#6b7280"
                                            }}
                                        >
                                            #{item.lead.id}
                                        </div>
                                    </td>
                                    <td
                                        style={{
                                            padding: "8px",
                                            fontSize: "12px",
                                            color: "#374151"
                                        }}
                                    >
                                        {item.channel}
                                    </td>
                                    <td
                                        style={{
                                            padding: "8px",
                                            fontSize: "12px",
                                            color: "#111827"
                                        }}
                                    >
                                        {item.last_message_text ||
                                            "Нет сообщений"}
                                    </td>
                                    <td style={{ padding: "8px" }}>
                                        <StatusBadge
                                            label={formatLeadStatus(
                                                item.lead.status
                                            )}
                                            tone={getLeadStatusTone(
                                                item.lead.status
                                            )}
                                        />
                                    </td>
                                    <td style={{ padding: "8px" }}>
                                        <Link
                                            to={`/lead/${item.id}`}
                                            style={{
                                                fontSize: "12px",
                                                textDecoration: "none",
                                                color: "#2563eb"
                                            }}
                                        >
                                            Открыть диалог
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

export default InboxPage;

