import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";

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
            <h3>Inbox</h3>
            {loading && <div>Загрузка диалогов…</div>}
            {error && <div style={{ color: "red" }}>{error}</div>}
            {!loading && !error && items.length === 0 && (
                <div>Пока нет диалогов.</div>
            )}
            <ul style={{ listStyle: "none", padding: 0 }}>
                {items.map((item) => (
                    <li
                        key={item.id}
                        style={{
                            border: "1px solid #ddd",
                            borderRadius: "8px",
                            padding: "8px",
                            marginBottom: "8px"
                        }}
                    >
                        <div style={{ fontWeight: 600 }}>
                            {item.lead.display_name} ({item.lead.status})
                        </div>
                        <div style={{ fontSize: "12px", color: "#555" }}>
                            Канал: {item.channel}
                        </div>
                        <div style={{ marginTop: "4px" }}>
                            {item.last_message_text || "Нет сообщений"}
                        </div>
                        <div style={{ marginTop: "4px" }}>
                            <Link to={`/lead/${item.id}`}>Открыть диалог</Link>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default InboxPage;

