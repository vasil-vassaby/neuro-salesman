import React from "react";

function ServicesPage() {
    return (
        <div>
            <h3>Услуги</h3>
            <p style={{ maxWidth: "520px" }}>
                Здесь будет справочник услуг: что именно вы предлагаете, как это
                описывается для клиента и к каким шаблонам ответов относится.
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
                В MVP данные об услугах берутся из базы знаний и шаблонов
                ответов. В следующих версиях здесь появится редактируемая
                таблица услуг.
            </div>
        </div>
    );
}

export default ServicesPage;

