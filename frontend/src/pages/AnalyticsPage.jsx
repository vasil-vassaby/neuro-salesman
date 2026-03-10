import React from "react";

function AnalyticsPage() {
    return (
        <div>
            <h3>Аналитика</h3>
            <p style={{ maxWidth: "520px" }}>
                В этом разделе будет сводка по воронке: сколько лидов пришло,
                сколько дошли до записи, сколько записей состоялось и по каким
                причинам клиенты отваливаются.
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
                Пока раздел показывает только текстовое описание. Когда данные
                будут готовы, здесь появятся простые графики и таблицы.
            </div>
        </div>
    );
}

export default AnalyticsPage;

