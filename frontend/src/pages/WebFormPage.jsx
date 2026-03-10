import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { translateErrorMessage } from "../i18n.js";
import ErrorAlert from "../components/ErrorAlert.jsx";

const DAY_START_HOUR = 9;
const DAY_END_HOUR = 15;

const filterSlotsByTimePref = (allSlots, timePref) => {
        return allSlots.filter((slot) => {
            const starts = new Date(slot.starts_at);
            const hour = starts.getHours();
            if (timePref === "day") {
                return hour >= DAY_START_HOUR && hour < DAY_END_HOUR;
            }
            if (timePref === "evening") {
                return hour >= DAY_END_HOUR;
            }
            return true;
        });
    };

function WebFormPage({ apiBase }) {
    const location = useLocation();

    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [message, setMessage] = useState("");
    const [slots, setSlots] = useState([]);
    const [selectedSlotId, setSelectedSlotId] = useState("");
    const [status, setStatus] = useState(null);
    const [error, setError] = useState(null);
    const [submitting, setSubmitting] = useState(false);
    const [loadingSlots, setLoadingSlots] = useState(true);
    const [slotsError, setSlotsError] = useState(null);

    const [prefillGoal, setPrefillGoal] = useState(null);
    const [prefillFormat, setPrefillFormat] = useState(null);
    const [prefillTime, setPrefillTime] = useState(null);

    useEffect(() => {
        const searchParams = new URLSearchParams(location.search);
        const goalParam = searchParams.get("goal");
        const formatParam = searchParams.get("format");
        const timeParam = searchParams.get("time");
        setPrefillGoal(goalParam);
        setPrefillFormat(formatParam);
        setPrefillTime(timeParam);

        const loadSlots = async () => {
            try {
                setLoadingSlots(true);
                setSlotsError(null);
                const now = new Date();
                const to = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
                const fromParam = encodeURIComponent(now.toISOString());
                const toParam = encodeURIComponent(to.toISOString());
                const response = await fetch(
                    `${apiBase}/slots?from_dt=${fromParam}&to_dt=${toParam}`
                );
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                const data = await response.json();
                const filtered =
                    timeParam === "day" || timeParam === "evening"
                        ? filterSlotsByTimePref(data, timeParam)
                        : data;
                setSlots(filtered);
                if (filtered.length > 0) {
                    setSelectedSlotId(filtered[0].id);
                }
            } catch (err) {
                setSlotsError(err.message);
            } finally {
                setLoadingSlots(false);
            }
        };
        loadSlots();
    }, [apiBase, location.search]);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError(null);
        setStatus(null);
        if (!selectedSlotId) {
            setError("Пожалуйста, выберите время записи.");
            return;
        }
        try {
            setSubmitting(true);
            const response = await fetch(`${apiBase}/web/bookings`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    name,
                    phone,
                    message,
                    slot_id: selectedSlotId
                })
            });
            if (!response.ok) {
                const data = await response.json().catch(() => null);
                const detail = data && data.detail ? data.detail : `HTTP ${response.status}`;
                throw new Error(detail);
            }
            const data = await response.json();
            setStatus(data.message || "Запись принята.");
            setName("");
            setPhone("");
            setMessage("");
        } catch (err) {
            setError(err.message);
        } finally {
            setSubmitting(false);
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
        return `${datePart} ${timePart} (${free} мест)`;
    };

    return (
        <div>
            <h3>Запись через веб-форму</h3>
            <p style={{ maxWidth: "480px" }}>
                Выберите удобное время и оставьте контакты. Мы подтвердим запись и, при
                необходимости, уточним детали.
            </p>
            {(prefillGoal || prefillFormat || prefillTime) && (
                <div
                    style={{
                        marginBottom: "8px",
                        padding: "6px 8px",
                        borderRadius: "6px",
                        backgroundColor: "#f5f5f5",
                        fontSize: "12px"
                    }}
                >
                    <div style={{ fontWeight: 600, marginBottom: "2px" }}>
                        Предзаполненные параметры
                    </div>
                    {prefillGoal && (
                        <div>
                            Цель:{" "}
                            <strong>
                                {prefillGoal === "sleep"
                                    ? "сон и восстановление"
                                    : prefillGoal === "pain"
                                    ? "боль / напряжение"
                                    : prefillGoal === "digestion"
                                    ? "пищеварение"
                                    : "другое"}
                            </strong>
                        </div>
                    )}
                    {prefillFormat && (
                        <div>
                            Формат:{" "}
                            <strong>
                                {prefillFormat === "offline" ? "офлайн" : "онлайн"}
                            </strong>
                        </div>
                    )}
                    {prefillTime && (
                        <div>
                            Время:{" "}
                            <strong>
                                {prefillTime === "day" ? "днём" : "вечером"}
                            </strong>
                        </div>
                    )}
                </div>
            )}
            {loadingSlots && <div>Загрузка доступных слотов…</div>}
            {slotsError && (
                <ErrorAlert
                    title="Не удалось загрузить слоты"
                    message={translateErrorMessage(slotsError)}
                />
            )}
            {!loadingSlots && !slotsError && slots.length === 0 && (
                <div>Пока нет свободных слотов. Попробуйте позже.</div>
            )}
            {slots.length > 0 && (
                <form
                    onSubmit={handleSubmit}
                    style={{
                        maxWidth: "480px",
                        display: "flex",
                        flexDirection: "column",
                        gap: "8px"
                    }}
                >
                    <label>
                        Время записи
                        <select
                            value={selectedSlotId}
                            onChange={(event) => setSelectedSlotId(event.target.value)}
                            required
                            style={{ width: "100%", boxSizing: "border-box" }}
                        >
                            {slots.map((slot) => {
                                const free = slot.capacity - slot.reserved_count;
                                if (free <= 0) {
                                    return null;
                                }
                                return (
                                    <option key={slot.id} value={slot.id}>
                                        {renderSlotLabel(slot)}
                                    </option>
                                );
                            })}
                        </select>
                    </label>
                    <label>
                        Имя
                        <input
                            type="text"
                            value={name}
                            onChange={(event) => setName(event.target.value)}
                            required
                            style={{ width: "100%", boxSizing: "border-box" }}
                        />
                    </label>
                    <label>
                        Телефон или контакт
                        <input
                            type="text"
                            value={phone}
                            onChange={(event) => setPhone(event.target.value)}
                            required
                            style={{ width: "100%", boxSizing: "border-box" }}
                        />
                    </label>
                    <label>
                        Комментарий
                        <textarea
                            rows={4}
                            value={message}
                            onChange={(event) => setMessage(event.target.value)}
                            required
                            style={{
                                width: "100%",
                                boxSizing: "border-box",
                                resize: "vertical"
                            }}
                        />
                    </label>
                    <button type="submit" disabled={submitting}>
                        {submitting ? "Отправка…" : "Отправить заявку"}
                    </button>
                </form>
            )}
            {status && (
                <div
                    style={{
                        marginTop: "8px",
                        padding: "8px 10px",
                        borderRadius: "6px",
                        backgroundColor: "#ecfdf3",
                        border: "1px solid #bbf7d0",
                        color: "#166534",
                        fontSize: "13px"
                    }}
                >
                    {status}
                </div>
            )}
            {error && (
                <div style={{ marginTop: "8px" }}>
                    <ErrorAlert
                        title="Не удалось отправить заявку"
                        message={translateErrorMessage(error)}
                    />
                </div>
            )}
        </div>
    );
}

export default WebFormPage;

