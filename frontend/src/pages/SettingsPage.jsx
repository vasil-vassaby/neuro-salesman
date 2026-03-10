import React from "react";

function SettingsPage() {
    return (
        <div>
            <h3>Настройки</h3>
            <p style={{ maxWidth: "520px" }}>
                Здесь будут базовые настройки нейро-продавца: данные о клинике,
                ссылке на веб-форму, режим Telegram и параметры напоминаний.
            </p>
            <div
                style={{
                    marginTop: "12px",
                    padding: "12px",
                    borderRadius: "8px",
                    border: "1px dashed #d1d5db",
                    backgroundColor: "#f9fafb",
                    fontSize: "13px"
                }}
            >
                Раздел пока в разработке. Сейчас основные параметры настраиваются
                через переменные окружения в `.env`.
            </div>
        </div>
    );
}

export default SettingsPage;

