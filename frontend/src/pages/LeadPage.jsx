import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

function LeadPage({ apiBase }) {
    const { id } = useParams();
    const [conversation, setConversation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [text, setText] = useState("");
    const [sending, setSending] = useState(false);

    const load = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${apiBase}/conversations/${id}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            setConversation(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, [apiBase, id]);

    const sendMessage = async (event) => {
        event.preventDefault();
        if (!text.trim()) {
            return;
        }
        try {
            setSending(true);
            const response = await fetch(
                `${apiBase}/conversations/${id}/messages`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ text })
                }
            );
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            setText("");
            await load();
        } catch (err) {
            setError(err.message);
        } finally {
            setSending(false);
        }
    };

    if (loading) {
        return <div>Загрузка диалога…</div>;
    }

    if (error) {
        return <div style={{ color: "red" }}>{error}</div>;
    }

    if (!conversation) {
        return <div>Диалог не найден.</div>;
    }

    return (
        <div>
            <h3>Диалог с {conversation.lead.display_name}</h3>
            <div style={{ marginBottom: "8px", fontSize: "12px", color: "#555" }}>
                Статус лида: {conversation.lead.status} | Канал:{" "}
                {conversation.channel}
            </div>
            <div
                style={{
                    border: "1px solid #eee",
                    borderRadius: "8px",
                    padding: "8px",
                    marginBottom: "8px",
                    maxHeight: "400px",
                    overflowY: "auto"
                }}
            >
                {conversation.messages.map((msg) => (
                    <div
                        key={msg.id}
                        style={{
                            textAlign: msg.direction === "outbound" ? "right" : "left",
                            marginBottom: "6px"
                        }}
                    >
                        <div
                            style={{
                                display: "inline-block",
                                padding: "6px 10px",
                                borderRadius: "12px",
                                backgroundColor:
                                    msg.direction === "outbound" ? "#e3f2fd" : "#f5f5f5"
                            }}
                        >
                            <div style={{ fontSize: "12px" }}>{msg.text}</div>
                            <div
                                style={{
                                    fontSize: "10px",
                                    color: "#777",
                                    marginTop: "2px"
                                }}
                            >
                                {msg.delivery_status}
                                {msg.delivery_error
                                    ? ` (${msg.delivery_error.slice(0, 40)}...)`
                                    : ""}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
            <form onSubmit={sendMessage}>
                <textarea
                    rows={3}
                    style={{ width: "100%", resize: "vertical" }}
                    placeholder="Ответ для клиента…"
                    value={text}
                    onChange={(event) => setText(event.target.value)}
                />
                <button type="submit" disabled={sending}>
                    {sending ? "Отправка…" : "Отправить"}
                </button>
            </form>
        </div>
    );
}

export default LeadPage;

