import React, { useEffect, useState } from "react";
import {
    formatBookingStatus,
    formatReminderStatus,
    getBookingStatusTone,
    translateErrorMessage
} from "../i18n.js";
import StatusBadge from "../components/StatusBadge.jsx";
import ErrorAlert from "../components/ErrorAlert.jsx";

function formatDateTime(value) {
    if (!value) {
        return "";
    }
    return new Date(value).toLocaleString();
}

function formatTime(value) {
    if (!value) {
        return "";
    }
    return new Date(value).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
    });
}

function startOfDay(date) {
    const copy = new Date(date);
    copy.setHours(0, 0, 0, 0);
    return copy;
}

function endOfDay(date) {
    const copy = new Date(date);
    copy.setHours(23, 59, 59, 999);
    return copy;
}

function toIso(value) {
    return value.toISOString();
}

function BookingsPage({ apiBase }) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [statusFilter, setStatusFilter] = useState("requested,confirmed");
    const [dayFilter, setDayFilter] = useState("today_tomorrow");
    const [search, setSearch] = useState("");

    const load = async () => {
        try {
            setLoading(true);
            setError(null);

            const now = new Date();
            let fromDt;
            let toDt;

            if (dayFilter === "today") {
                fromDt = startOfDay(now);
                toDt = endOfDay(now);
            } else if (dayFilter === "tomorrow") {
                const tomorrow = new Date(now);
                tomorrow.setDate(now.getDate() + 1);
                fromDt = startOfDay(tomorrow);
                toDt = endOfDay(tomorrow);
            } else {
                const tomorrow = new Date(now);
                tomorrow.setDate(now.getDate() + 1);
                fromDt = startOfDay(now);
                toDt = endOfDay(tomorrow);
            }

            const params = new URLSearchParams();
            params.set("from_dt", toIso(fromDt));
            params.set("to_dt", toIso(toDt));
            if (statusFilter) {
                params.set("status", statusFilter);
            }
            if (search.trim()) {
                params.set("search", search.trim());
            }

            const response = await fetch(`${apiBase}/bookings?${params.toString()}`);
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

    useEffect(() => {
        load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [apiBase, statusFilter, dayFilter]);

    const handleSearchSubmit = (event) => {
        event.preventDefault();
        load();
    };

    const grouped = items.reduce(
        (acc, booking) => {
            if (!booking.scheduled_at) {
                acc.other.push(booking);
                return acc;
            }
            const date = new Date(booking.scheduled_at);
            const today = new Date();
            const tomorrow = new Date();
            tomorrow.setDate(today.getDate() + 1);
            const isToday =
                date.toDateString() === today.toDateString();
            const isTomorrow =
                date.toDateString() === tomorrow.toDateString();
            if (isToday) {
                acc.today.push(booking);
            } else if (isTomorrow) {
                acc.tomorrow.push(booking);
            } else {
                acc.other.push(booking);
            }
            return acc;
        },
        { today: [], tomorrow: [], other: [] }
    );

    const renderRemindersCell = (booking) => {
        if (!booking.reminders || booking.reminders.length === 0) {
            return (
                <span style={{ fontSize: "11px", color: "#6b7280" }}>
                    Напоминаний нет
                </span>
            );
        }
        return (
            <div style={{ fontSize: "11px", color: "#374151" }}>
                {booking.reminders
                    .sort(
                        (a, b) =>
                            new Date(a.remind_at) - new Date(b.remind_at)
                    )
                    .slice(0, 3)
                    .map((reminder) => (
                        <div key={reminder.id}>
                            {formatDateTime(reminder.remind_at)} —{" "}
                            {formatReminderStatus(reminder.status)}
                        </div>
                    ))}
                {booking.reminders.length > 3 && (
                    <div style={{ color: "#6b7280" }}>и другие…</div>
                )}
            </div>
        );
    };

    const renderGroup = (title, list) => {
        if (list.length === 0) {
            return null;
        }
        return (
            <div style={{ marginTop: "16px" }}>
                <div
                    style={{
                        fontWeight: 600,
                        marginBottom: "4px",
                        fontSize: "14px"
                    }}
                >
                    {title}
                </div>
                <div style={{ overflowX: "auto" }}>
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
                                    Пациент
                                </th>
                                <th
                                    style={{
                                        padding: "8px",
                                        borderBottom: "1px solid #e5e7eb"
                                    }}
                                >
                                    Время
                                </th>
                                <th
                                    style={{
                                        padding: "8px",
                                        borderBottom: "1px solid #e5e7eb"
                                    }}
                                >
                                    Телефон
                                </th>
                                <th
                                    style={{
                                        padding: "8px",
                                        borderBottom: "1px solid #e5e7eb"
                                    }}
                                >
                                    Статус
                                </th>
                                <th
                                    style={{
                                        padding: "8px",
                                        borderBottom: "1px solid #e5e7eb"
                                    }}
                                >
                                    Напоминания
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {list.map((booking) => (
                                <tr
                                    key={booking.id}
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
                                            {booking.lead_display_name ||
                                                booking.contact_name}
                                        </div>
                                        <div
                                            style={{
                                                fontSize: "11px",
                                                color: "#6b7280"
                                            }}
                                        >
                                            #{booking.id}
                                        </div>
                                    </td>
                                    <td
                                        style={{
                                            padding: "8px",
                                            fontSize: "12px"
                                        }}
                                    >
                                        {booking.scheduled_at
                                            ? formatDateTime(
                                                  booking.scheduled_at
                                              )
                                            : "—"}
                                    </td>
                                    <td
                                        style={{
                                            padding: "8px",
                                            fontSize: "12px"
                                        }}
                                    >
                                        {booking.contact_phone || "—"}
                                    </td>
                                    <td style={{ padding: "8px" }}>
                                        <StatusBadge
                                            label={formatBookingStatus(
                                                booking.status
                                            )}
                                            tone={getBookingStatusTone(
                                                booking.status
                                            )}
                                        />
                                    </td>
                                    <td style={{ padding: "8px" }}>
                                        {renderRemindersCell(booking)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };

    return (
        <div>
            <h3>Записи</h3>
            <div
                style={{
                    display: "flex",
                    gap: "12px",
                    alignItems: "flex-end",
                    marginBottom: "12px",
                    flexWrap: "wrap"
                }}
            >
                <div>
                    <div
                        style={{
                            fontSize: "12px",
                            marginBottom: "4px"
                        }}
                    >
                        Диапазон
                    </div>
                    <select
                        value={dayFilter}
                        onChange={(event) => setDayFilter(event.target.value)}
                    >
                        <option value="today_tomorrow">Сегодня + завтра</option>
                        <option value="today">Только сегодня</option>
                        <option value="tomorrow">Только завтра</option>
                    </select>
                </div>
                <div>
                    <div
                        style={{
                            fontSize: "12px",
                            marginBottom: "4px"
                        }}
                    >
                        Статусы
                    </div>
                    <select
                        value={statusFilter}
                        onChange={(event) =>
                            setStatusFilter(event.target.value)
                        }
                    >
                        <option value="requested,confirmed">
                            Ожидает подтверждения + подтверждена
                        </option>
                        <option value="requested">
                            только ожидает подтверждения
                        </option>
                        <option value="confirmed">только подтверждена</option>
                        <option value="cancelled">только отменена</option>
                        <option value="no_show">только не пришёл</option>
                        <option value="requested,confirmed,cancelled,no_show">
                            все
                        </option>
                    </select>
                </div>
                <form onSubmit={handleSearchSubmit}>
                    <div
                        style={{
                            fontSize: "12px",
                            marginBottom: "4px"
                        }}
                    >
                        Поиск по имени / телефону
                    </div>
                    <div style={{ display: "flex", gap: "4px" }}>
                        <input
                            type="text"
                            value={search}
                            onChange={(event) =>
                                setSearch(event.target.value)
                            }
                            placeholder="Имя или телефон"
                        />
                        <button type="submit">Искать</button>
                    </div>
                </form>
            </div>

            {loading && <div>Загрузка записей…</div>}
            {error && (
                <ErrorAlert
                    title="Не удалось загрузить записи"
                    message={translateErrorMessage(error)}
                />
            )}
            {!loading && !error && items.length === 0 && (
                <div>Записей в выбранном диапазоне нет.</div>
            )}

            {renderGroup("Сегодня", grouped.today)}
            {renderGroup("Завтра", grouped.tomorrow)}
            {renderGroup("Другие даты", grouped.other)}
        </div>
    );
}

export default BookingsPage;

