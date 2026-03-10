import React from "react";

const TONES = {
    neutral: {
        backgroundColor: "#f2f4f7",
        color: "#1f2933",
        borderColor: "#d8e2ec"
    },
    success: {
        backgroundColor: "#e3f9e5",
        color: "#0b6e4f",
        borderColor: "#a6e3b8"
    },
    warning: {
        backgroundColor: "#fff4e5",
        color: "#92400e",
        borderColor: "#ffb648"
    },
    danger: {
        backgroundColor: "#fde8e8",
        color: "#9b1c1c",
        borderColor: "#f5b5b5"
    },
    info: {
        backgroundColor: "#e3f2fd",
        color: "#0b4f6c",
        borderColor: "#90caf9"
    }
};

function StatusBadge({ label, tone = "neutral" }) {
    const style = TONES[tone] || TONES.neutral;

    return (
        <span
            style={{
                display: "inline-flex",
                alignItems: "center",
                padding: "2px 8px",
                borderRadius: "999px",
                fontSize: "11px",
                fontWeight: 500,
                border: "1px solid",
                ...style
            }}
        >
            {label}
        </span>
    );
}

export default StatusBadge;

