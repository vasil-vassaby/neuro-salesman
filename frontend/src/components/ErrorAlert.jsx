import React from "react";

function ErrorAlert({ title = "Произошла ошибка", message }) {
    if (!message) {
        return null;
    }

    return (
        <div
            style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "8px",
                padding: "8px 10px",
                borderRadius: "6px",
                backgroundColor: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#991b1b",
                fontSize: "13px",
                margin: "4px 0"
            }}
        >
            <div
                aria-hidden="true"
                style={{
                    width: "18px",
                    height: "18px",
                    borderRadius: "999px",
                    backgroundColor: "#fee2e2",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: "11px",
                    flexShrink: 0
                }}
            >
                !
            </div>
            <div>
                <div
                    style={{
                        fontWeight: 600,
                        marginBottom: "2px"
                    }}
                >
                    {title}
                </div>
                <div>{message}</div>
            </div>
        </div>
    );
}

export default ErrorAlert;

