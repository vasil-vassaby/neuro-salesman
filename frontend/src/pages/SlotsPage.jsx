import React, { useEffect, useState } from "react";
import { translateErrorMessage } from "../i18n.js";
import ErrorAlert from "../components/ErrorAlert.jsx";

function SlotsPage({ apiBase }) {
    const [slots, setSlots] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [startsAt, setStartsAt] = useState("");
    const [endsAt, setEndsAt] = useState("");
    const [capacity, setCapacity] = useState(1);
    const [notes, setNotes] = useState("");
    const [saving, setSaving] = useState(false);

    const loadSlots = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await fetch(`${apiBase}/slots`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            setSlots(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadSlots();
    }, [apiBase]);

    const handleCreate = async (event) => {
        event.preventDefault();
        setError(null);
        try {
            setSaving(true);
            const payload = {
                starts_at: new Date(startsAt).toISOString(),
                ends_at: new Date(endsAt).toISOString(),
                capacity: Number(capacity),
                notes: notes || null
            };
            const response = await fetch(`${apiBase}/slots`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                const data = await response.json().catch(() => null);
                const detail = data && data.detail ? data.detail : `HTTP ${response.status}`;
                throw new Error(detail);
            }
            setStartsAt("");
            setEndsAt("");
            setCapacity(1);
            setNotes("");
            await loadSlots();
        } catch (err) {
            setError(err.message);
        } finally {
            setSaving(false);
        }
    };

    const handleDeactivate = async (slotId) => {
        setError(null);
        try {
            const response = await fetch(`${apiBase}/slots/${slotId}`, {
                method: "DELETE"
            });
            if (!response.ok) {
                const data = await response.json().catch(() => null);
                const detail = data && data.detail ? data.detail : `HTTP ${response.status}`;
                throw new Error(detail);
            }
            await loadSlots();
        } catch (err) {
            setError(err.message);
        }
    };

    const renderSlotLabel = (slot) => {
        const starts = new Date(slot.starts_at);
        const ends = new Date(slot.ends_at);
        const pad = (n) => (n < 10 ? `0${n}` : `${n}`);
        const datePart = `${pad(starts.getDate())}.${pad(
            starts.getMonth() + 1
        )}.${starts.getFullYear()}`;
        const timePart = `${pad(starts.getHours())}:${pad(
            starts.getMinutes()
        )}–${pad(ends.getHours())}:${pad(ends.getMinutes())}`;
        const free = slot.capacity - slot.reserved_count;
        return `${datePart} ${timePart} (${free}/${slot.capacity})`;
    };

    return (
        <div>
            <h3>Слоты записи</h3>
            <form
                onSubmit={handleCreate}
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "8px",
                    maxWidth: "480px",
                    marginBottom: "16px"
                }}
            >
                <div style={{ fontWeight: 600 }}>Создать слот</div>
                <label>
                    Начало
                    <input
                        type="datetime-local"
                        value={startsAt}
                        onChange={(event) => setStartsAt(event.target.value)}
                        required
                        style={{ width: "100%", boxSizing: "border-box" }}
                    />
                </label>
                <label>
                    Конец
                    <input
                        type="datetime-local"
                        value={endsAt}
                        onChange={(event) => setEndsAt(event.target.value)}
                        required
                        style={{ width: "100%", boxSizing: "border-box" }}
                    />
                </label>
                <label>
                    Вместимость
                    <input
                        type="number"
                        min="1"
                        value={capacity}
                        onChange={(event) => setCapacity(event.target.value)}
                        required
                        style={{ width: "100%", boxSizing: "border-box" }}
                    />
                </label>
                <label>
                    Заметка
                    <input
                        type="text"
                        value={notes}
                        onChange={(event) => setNotes(event.target.value)}
                        style={{ width: "100%", boxSizing: "border-box" }}
                    />
                </label>
                <button type="submit" disabled={saving}>
                    {saving ? "Сохранение…" : "Создать слот"}
                </button>
            </form>

            {loading && <div>Загрузка слотов…</div>}
            {error && (
                <ErrorAlert
                    title="Не удалось загрузить слоты"
                    message={translateErrorMessage(error)}
                />
            )}
            {!loading && slots.length === 0 && <div>Слотов пока нет.</div>}
            {!loading && slots.length > 0 && (
                <div style={{ overflowX: "auto", marginTop: "8px" }}>
                    <table
                        style={{
                            width: "100%",
                            borderCollapse: "collapse",
                            fontSize: "13px"
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
                                    Время и вместимость
                                </th>
                                <th
                                    style={{
                                        padding: "8px",
                                        borderBottom: "1px solid #e5e7eb"
                                    }}
                                >
                                    Заметка
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
                            {slots.map((slot) => (
                                <tr
                                    key={slot.id}
                                    style={{
                                        borderBottom: "1px solid #f3f4f6"
                                    }}
                                >
                                    <td style={{ padding: "8px" }}>
                                        {renderSlotLabel(slot)}
                                    </td>
                                    <td
                                        style={{
                                            padding: "8px",
                                            fontSize: "12px",
                                            color: "#4b5563"
                                        }}
                                    >
                                        {slot.notes || "—"}
                                    </td>
                                    <td style={{ padding: "8px" }}>
                                        <button
                                            type="button"
                                            onClick={() =>
                                                handleDeactivate(slot.id)
                                            }
                                            style={{
                                                padding: "4px 8px",
                                                borderRadius: "6px",
                                                border: "1px solid #fecaca",
                                                backgroundColor: "#fef2f2",
                                                color: "#b91c1c",
                                                fontSize: "12px",
                                                cursor: "pointer"
                                            }}
                                        >
                                            Деактивировать
                                        </button>
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

export default SlotsPage;

