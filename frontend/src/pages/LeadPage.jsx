import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

function LeadPage({ apiBase }) {
    const { id } = useParams();
    const [conversation, setConversation] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [text, setText] = useState("");
    const [sending, setSending] = useState(false);

    const [bookings, setBookings] = useState([]);
    const [bookingError, setBookingError] = useState(null);
    const [updatingBooking, setUpdatingBooking] = useState(false);

    const [lostReasons, setLostReasons] = useState([]);
    const [lostReasonCode, setLostReasonCode] = useState("");
    const [lostNote, setLostNote] = useState("");
    const [lostSaving, setLostSaving] = useState(false);
    const [lostError, setLostError] = useState(null);

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

    const loadBookings = async (leadId) => {
        try {
            setBookingError(null);
            const response = await fetch(
                `${apiBase}/leads/${leadId}/bookings`
            );
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            setBookings(data);
        } catch (err) {
            setBookingError(err.message);
        }
    };

    const loadLostReasons = async () => {
        try {
            const response = await fetch(`${apiBase}/lost_reasons`);
            if (!response.ok) {
                return;
            }
            const data = await response.json();
            setLostReasons(data);
            if (data.length > 0) {
                setLostReasonCode(data[0].code);
            }
        } catch {
            // ignore
        }
    };

    useEffect(() => {
        const init = async () => {
            await load();
        };
        init();
    }, [apiBase, id]);

    useEffect(() => {
        if (conversation && conversation.lead && conversation.lead.id) {
            loadBookings(conversation.lead.id);
            loadLostReasons();
        }
    }, [conversation]);

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

    const updateBookingStatus = async (bookingId, status) => {
        setUpdatingBooking(true);
        try {
            const response = await fetch(`${apiBase}/bookings/${bookingId}`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ status })
            });
            if (!response.ok) {
                const data = await response.json().catch(() => null);
                const detail = data && data.detail ? data.detail : `HTTP ${response.status}`;
                throw new Error(detail);
            }
            if (conversation && conversation.lead) {
                await loadBookings(conversation.lead.id);
            }
        } catch (err) {
            setBookingError(err.message);
        } finally {
            setUpdatingBooking(false);
        }
    };

    const markLost = async () => {
        if (!conversation || !conversation.lead) {
            return;
        }
        setLostError(null);
        try {
            setLostSaving(true);
            const response = await fetch(
                `${apiBase}/leads/${conversation.lead.id}/lost`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        reason_code: lostReasonCode,
                        note: lostNote || null
                    })
                }
            );
            if (!response.ok) {
                const data = await response.json().catch(() => null);
                const detail = data && data.detail ? data.detail : `HTTP ${response.status}`;
                throw new Error(detail);
            }
            setLostNote("");
            await load();
        } catch (err) {
            setLostError(err.message);
        } finally {
            setLostSaving(false);
        }
    };

    const renderBookings = () => {
        if (bookings.length === 0) {
            return <div>Записей пока нет.</div>;
        }
        return (
            <ul style={{ listStyle: "none", padding: 0 }}>
                {bookings.map((b) => (
                    <li
                        key={b.id}
                        style={{
                            border: "1px solid #ddd",
                            borderRadius: "8px",
                            padding: "8px",
                            marginBottom: "8px"
                        }}
                    >
                        <div style={{ fontSize: "12px" }}>
                            Статус: <strong>{b.status}</strong>
                        </div>
                        {b.scheduled_at && (
                            <div style={{ fontSize: "12px" }}>
                                Время:{" "}
                                {new Date(b.scheduled_at).toLocaleString()}
                            </div>
                        )}
                        <div style={{ marginTop: "4px" }}>
                            <button
                                type="button"
                                onClick={() =>
                                    updateBookingStatus(b.id, "confirmed")
                                }
                                disabled={updatingBooking}
                                style={{ marginRight: "4px" }}
                            >
                                Confirm
                            </button>
                            <button
                                type="button"
                                onClick={() =>
                                    updateBookingStatus(b.id, "cancelled")
                                }
                                disabled={updatingBooking}
                                style={{ marginRight: "4px" }}
                            >
                                Cancel
                            </button>
                            <button
                                type="button"
                                onClick={() =>
                                    updateBookingStatus(b.id, "no_show")
                                }
                                disabled={updatingBooking}
                            >
                                No-show
                            </button>
                        </div>
                    </li>
                ))}
            </ul>
        );
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
                    display: "flex",
                    gap: "16px",
                    alignItems: "flex-start",
                    marginBottom: "16px"
                }}
            >
                <div style={{ flex: 2 }}>
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
                                    textAlign:
                                        msg.direction === "outbound"
                                            ? "right"
                                            : "left",
                                    marginBottom: "6px"
                                }}
                            >
                                <div
                                    style={{
                                        display: "inline-block",
                                        padding: "6px 10px",
                                        borderRadius: "12px",
                                        backgroundColor:
                                            msg.direction === "outbound"
                                                ? "#e3f2fd"
                                                : "#f5f5f5"
                                    }}
                                >
                                    <div style={{ fontSize: "12px" }}>
                                        {msg.text}
                                    </div>
                                    <div
                                        style={{
                                            fontSize: "10px",
                                            color: "#777",
                                            marginTop: "2px"
                                        }}
                                    >
                                        {msg.delivery_status}
                                        {msg.delivery_error
                                            ? ` (${msg.delivery_error.slice(
                                                  0,
                                                  40
                                              )}...)`
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

                <div style={{ flex: 1 }}>
                    <div
                        style={{
                            border: "1px solid #eee",
                            borderRadius: "8px",
                            padding: "8px",
                            marginBottom: "8px"
                        }}
                    >
                        <div style={{ fontWeight: 600, marginBottom: "4px" }}>
                            Записи
                        </div>
                        {bookingError && (
                            <div style={{ color: "red", marginBottom: "4px" }}>
                                {bookingError}
                            </div>
                        )}
                        {renderBookings()}
                    </div>

                    <div
                        style={{
                            border: "1px solid #eee",
                            borderRadius: "8px",
                            padding: "8px"
                        }}
                    >
                        <div style={{ fontWeight: 600, marginBottom: "4px" }}>
                            Отметить как потерян
                        </div>
                        {lostReasons.length === 0 && (
                            <div style={{ fontSize: "12px" }}>
                                Справочник причин ещё не загружен.
                            </div>
                        )}
                        {lostReasons.length > 0 && (
                            <>
                                <label>
                                    Причина
                                    <select
                                        value={lostReasonCode}
                                        onChange={(event) =>
                                            setLostReasonCode(
                                                event.target.value
                                            )
                                        }
                                        style={{
                                            width: "100%",
                                            boxSizing: "border-box"
                                        }}
                                    >
                                        {lostReasons.map((reason) => (
                                            <option
                                                key={reason.code}
                                                value={reason.code}
                                            >
                                                {reason.title}
                                            </option>
                                        ))}
                                    </select>
                                </label>
                                <label>
                                    Комментарий
                                    <textarea
                                        rows={2}
                                        value={lostNote}
                                        onChange={(event) =>
                                            setLostNote(event.target.value)
                                        }
                                        style={{
                                            width: "100%",
                                            boxSizing: "border-box",
                                            resize: "vertical"
                                        }}
                                    />
                                </label>
                                <button
                                    type="button"
                                    onClick={markLost}
                                    disabled={lostSaving}
                                >
                                    {lostSaving
                                        ? "Сохранение…"
                                        : "Отметить Lost"}
                                </button>
                            </>
                        )}
                        {lostError && (
                            <div
                                style={{
                                    color: "red",
                                    marginTop: "4px",
                                    fontSize: "12px"
                                }}
                            >
                                {lostError}
                            </div>
                        )}
                    </div>

                    <div
                        style={{
                            border: "1px solid #eee",
                            borderRadius: "8px",
                            padding: "8px",
                            marginTop: "8px"
                        }}
                    >
                        <div style={{ fontWeight: 600, marginBottom: "4px" }}>
                            State (debug)
                        </div>
                        <pre
                            style={{
                                fontSize: "11px",
                                backgroundColor: "#fafafa",
                                borderRadius: "4px",
                                padding: "6px",
                                maxHeight: "180px",
                                overflow: "auto",
                                margin: 0
                            }}
                        >
                            {JSON.stringify(conversation.state || {}, null, 2)}
                        </pre>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default LeadPage;

