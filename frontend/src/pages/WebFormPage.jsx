import React, { useState } from "react";

function WebFormPage({ apiBase }) {
    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [message, setMessage] = useState("");
    const [status, setStatus] = useState(null);
    const [error, setError] = useState(null);
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError(null);
        setStatus(null);
        try {
            setSubmitting(true);
            const response = await fetch(`${apiBase}/web/leads`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ name, phone, message })
            });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            setStatus("Заявка принята, мы свяжемся с вами в ближайшее время.");
            setName("");
            setPhone("");
            setMessage("");
        } catch (err) {
            setError(err.message);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div>
            <h3>Оставить заявку</h3>
            <p style={{ maxWidth: "480px" }}>
                Коротко опишите ваш запрос, укажите контакт для связи и удобный формат
                (онлайн/офлайн). Мы вернёмся с предложением времени.
            </p>
            <form
                onSubmit={handleSubmit}
                style={{ maxWidth: "480px", display: "flex", flexDirection: "column", gap: "8px" }}
            >
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
                    Запрос
                    <textarea
                        rows={4}
                        value={message}
                        onChange={(event) => setMessage(event.target.value)}
                        required
                        style={{ width: "100%", boxSizing: "border-box", resize: "vertical" }}
                    />
                </label>
                <button type="submit" disabled={submitting}>
                    {submitting ? "Отправка…" : "Отправить заявку"}
                </button>
            </form>
            {status && <div style={{ marginTop: "8px", color: "green" }}>{status}</div>}
            {error && <div style={{ marginTop: "8px", color: "red" }}>{error}</div>}
        </div>
    );
}

export default WebFormPage;

