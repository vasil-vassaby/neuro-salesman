import React, { useEffect, useState } from "react";
import { translateErrorMessage } from "../i18n.js";

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
                <div style={{ color: "red" }}>
                    {translateErrorMessage(error)}
                </div>
            )}
            {!loading && slots.length === 0 && <div>Слотов пока нет.</div>}
            {!loading && slots.length > 0 && (
                <ul style={{ listStyle: "none", padding: 0 }}>
                    {slots.map((slot) => (
                        <li
                            key={slot.id}
                            style={{
                                border: "1px solid #ddd",
                                borderRadius: "8px",
                                padding: "8px",
                                marginBottom: "8px"
                            }}
                        >
                            <div>{renderSlotLabel(slot)}</div>
                            {slot.notes && (
                                <div style={{ fontSize: "12px", color: "#555" }}>
                                    {slot.notes}
                                </div>
                            )}
                            <button
                                type="button"
                                onClick={() => handleDeactivate(slot.id)}
                                style={{ marginTop: "4px" }}
                            >
                                Деактивировать
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default SlotsPage;

