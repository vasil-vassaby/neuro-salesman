export const UI_TEXT = {
    APP_TITLE: "Neuro-Salesman — Входящие",
    NAV_INBOX: "Входящие",
    NAV_BOOKINGS: "Записи",
    NAV_SLOTS: "Слоты",
    NAV_WEB_FORM: "Веб-форма",
    CHECK_API: "Проверить API"
};

export const BOOKING_STATUS_LABELS = {
    requested: "Ожидает подтверждения",
    confirmed: "Подтверждена",
    cancelled: "Отменена",
    no_show: "Не пришёл",
    lost: "Потерян"
};

export function formatBookingStatus(status) {
    return BOOKING_STATUS_LABELS[status] || status;
}

export const REMINDER_STATUS_LABELS = {
    scheduled: "Запланировано",
    sent: "Отправлено",
    delivered: "Доставлено",
    failed: "Ошибка",
    cancelled: "Отменено"
};

export function formatReminderStatus(status) {
    return REMINDER_STATUS_LABELS[status] || status;
}

export const LEAD_STATUS_LABELS = {
    new: "Новый",
    in_progress: "В работе",
    booked: "Запись создана",
    lost: "Потерян"
};

export function formatLeadStatus(status) {
    return LEAD_STATUS_LABELS[status] || status;
}

export const DELIVERY_STATUS_LABELS = {
    pending: "Отправляется",
    sent: "Отправлено",
    delivered: "Доставлено",
    failed: "Ошибка доставки"
};

export function formatDeliveryStatus(status) {
    return DELIVERY_STATUS_LABELS[status] || status;
}

export function translateErrorMessage(message) {
    if (!message) {
        return message;
    }
    if (message.startsWith("HTTP ")) {
        const parts = message.split(" ");
        const code = parts.length >= 2 ? parts[1] : "";
        return code
            ? `Ошибка сервера (код ${code}).`
            : "Ошибка сервера.";
    }
    if (message === "NetworkError when attempting to fetch resource") {
        return "Ошибка сети при загрузке данных";
    }
    if (message === "Invalid booking status") {
        return "Недопустимый статус записи.";
    }
    if (message === "Invalid status transition") {
        return "Так изменить статус записи нельзя.";
    }
    if (message === "Cannot change final status") {
        return "Финальный статус записи нельзя изменить.";
    }
    if (message === "Booking not found") {
        return "Запись не найдена.";
    }
    if (message === "Slot not found") {
        return "Слот не найден.";
    }
    if (message === "Lead not found") {
        return "Лид не найден.";
    }
    if (message === "Unknown reason code") {
        return "Неизвестная причина.";
    }
    if (message === "Conversation not found") {
        return "Диалог не найден.";
    }
    if (
        message.includes("Bad Request") &&
        message.includes("https://api.telegram.org")
    ) {
        return "Telegram вернул ошибку при отправке сообщения.";
    }
    if (message === "Telegram bot is not configured") {
        return "Telegram-бот не настроен.";
    }
    if (message === "Invalid Telegram secret token") {
        return "Неверный секретный токен Telegram.";
    }
    return message;
}

