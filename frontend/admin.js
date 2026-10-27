const API_BASE = "http://127.0.0.1:8000";
const TOKEN_KEY = "aits_admin_token";

const loginSection = document.getElementById("login-section");
const dashboardSection = document.getElementById("dashboard-section");
const logoutButton = document.getElementById("logout-button");
const loginForm = document.getElementById("login-form");
const loginMessage = document.getElementById("login-message");
const createEventForm = document.getElementById("create-event-form");
const createAdminForm = document.getElementById("create-admin-form");
const adminEventsList = document.getElementById("admin-events-list");
const adminEventsMessage = document.getElementById("admin-events-message");
const rosterSection = document.getElementById("roster-section");
const rosterTitle = document.getElementById("roster-title");
const rosterMessage = document.getElementById("roster-message");
const rosterContent = document.getElementById("roster-content");
const toast = document.getElementById("toast");

let toastTimer;

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setMessage(element, message, type = "") {
    element.textContent = message;
    element.className = `form-message ${type}`.trim();
}

function showToast(message, isError = false) {
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.add("show");

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 4000);
}

function makeElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;

    return element;
}

function formatDeadline(value) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) return "Deadline unavailable";

    return new Intl.DateTimeFormat("en-IN", {
        dateStyle: "medium",
        timeStyle: "short"
    }).format(date);
}

async function apiRequest(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = getToken();

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers
    });

    const data = await response.json().catch(() => ({}));

    if (response.status === 401 && token) {
        localStorage.removeItem(TOKEN_KEY);
        updateView(false);
        throw new Error("Your session expired or your token is invalid. Please log in again.");
    }

    if (!response.ok) {
        throw new Error(data.detail || data.message || `Request failed (${response.status}).`);
    }

    return data;
}

function updateView(isLoggedIn) {
    loginSection.classList.toggle("hidden", isLoggedIn);
    dashboardSection.classList.toggle("hidden", !isLoggedIn);
    logoutButton.classList.toggle("hidden", !isLoggedIn);

    if (!isLoggedIn) {
        rosterSection.classList.add("hidden");
    }
}

async function login(username, password) {
    const body = new URLSearchParams();
    body.set("username", username);
    body.set("password", password);

    const response = await fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || "Login failed.");
    }

    if (!data.access_token) {
        throw new Error("The backend did not return an access token.");
    }

    localStorage.setItem(TOKEN_KEY, data.access_token);
}

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;
    const submitButton = loginForm.querySelector("button[type='submit']");

    submitButton.disabled = true;
    setMessage(loginMessage, "Signing in...");

    try {
        await login(username, password);
        loginForm.reset();
        updateView(true);
        setMessage(loginMessage, "");
        await loadAdminEvents();
    } catch (error) {
        setMessage(loginMessage, error.message, "error");
    } finally {
        submitButton.disabled = false;
    }
});

logoutButton.addEventListener("click", () => {
    localStorage.removeItem(TOKEN_KEY);
    updateView(false);
    setMessage(loginMessage, "You have logged out.", "success");
});

createEventForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = document.getElementById("event-name").value.trim();
    const deadline = document.getElementById("event-deadline").value;
    const submitButton = createEventForm.querySelector("button[type='submit']");

    if (!name || !deadline) {
        setMessage(document.getElementById("event-message"),
            "Enter an event name and deadline.", "error");
        return;
    }

    // datetime-local provides a local date/time without a timezone suffix.
    submitButton.disabled = true;
    setMessage(document.getElementById("event-message"), "Creating event...");

    try {
        const data = await apiRequest("/events", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                event_name: name,
                deadline: deadline
            })
        });

        createEventForm.reset();

        setMessage(
            document.getElementById("event-message"),
            data.message || "Event created successfully.",
            "success"
        );

        await loadAdminEvents();
        showToast(data.message || "Event created successfully.");
    } catch (error) {
        setMessage(document.getElementById("event-message"), error.message, "error");
    } finally {
        submitButton.disabled = false;
    }
});

createAdminForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("new-admin-username").value.trim();
    const email = document.getElementById("new-admin-email").value.trim();
    const password = document.getElementById("new-admin-password").value;
    const messageElement = document.getElementById("admin-message");
    const submitButton = createAdminForm.querySelector("button[type='submit']");

    submitButton.disabled = true;
    setMessage(messageElement, "Creating admin account...");

    try {
        const data = await apiRequest("/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password })
        });

        createAdminForm.reset();
        setMessage(messageElement, data.message || "Admin created successfully.", "success");
    } catch (error) {
        setMessage(messageElement, error.message, "error");
    } finally {
        submitButton.disabled = false;
    }
});

function createAdminEventCard(event) {
    const card = makeElement("article", "admin-event");
    const title = makeElement("h3", "", event.event_name || "Untitled event");
    const deadline = makeElement("p", "", `Deadline: ${formatDeadline(event.deadline)}`);

    const statusText = new Date(event.deadline) < new Date()
        ? "Expired"
        : "Live";

    const status = makeElement(
        "span",
        `status ${statusText === "Live" ? "status-live" : "status-expired"}`,
        statusText
    );

    const actions = makeElement("div", "admin-event-actions");

    const rosterButton = makeElement("button", "button button-outline", "View roster");
    rosterButton.type = "button";
    rosterButton.addEventListener("click", () => loadRoster(event));

    const deleteButton = makeElement("button", "button button-danger", "Delete event");
    deleteButton.type = "button";
    deleteButton.addEventListener("click", () => deleteEvent(event));

    actions.append(rosterButton, deleteButton);
    card.append(title, status, deadline, actions);

    return card;
}

async function loadAdminEvents() {
    adminEventsList.replaceChildren(makeElement("p", "muted", "Loading events..."));
    setMessage(adminEventsMessage, "");

    try {
        const events = await apiRequest("/events");

        if (!Array.isArray(events)) {
            throw new Error("The events endpoint returned an unexpected response.");
        }

        adminEventsList.replaceChildren();

        if (events.length === 0) {
            adminEventsList.append(
                makeElement("p", "empty-state", "No events have been created.")
            );
            return;
        }

        events.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
        events.forEach(event => adminEventsList.append(createAdminEventCard(event)));
    } catch (error) {
        if (error.message.includes("No active events found")) {
            adminEventsList.replaceChildren(
                makeElement("p", "empty-state", "No events have been created.")
            );
        } else {
            adminEventsList.replaceChildren(
                makeElement("p", "empty-state", error.message)
            );
        }
    }
}

async function deleteEvent(event) {
    const confirmed = window.confirm(
        `Delete "${event.event_name}"?\n\nThis removes the event and its event-manager links.`
    );

    if (!confirmed) return;

    try {
        const data = await apiRequest(`/events/${encodeURIComponent(event.id)}`, {
            method: "DELETE"
        });

        showToast(data.message || "Event deleted.");
        rosterSection.classList.add("hidden");
        await loadAdminEvents();
    } catch (error) {
        showToast(error.message, true);
    }
}

async function loadRoster(event) {
    rosterSection.classList.remove("hidden");
    rosterTitle.textContent = `Student registrations — ${event.event_name}`;
    rosterContent.replaceChildren();
    setMessage(rosterMessage, "Loading roster...");

    try {
        const students = await apiRequest(`/events/${encodeURIComponent(event.id)}`);

        if (!Array.isArray(students)) {
            throw new Error("The roster endpoint returned an unexpected response.");
        }

        setMessage(rosterMessage, `${students.length} student(s) registered.`, "success");

        if (students.length === 0) {
            rosterContent.append(
                makeElement("p", "empty-state", "No students have registered for this event.")
            );
            return;
        }

        const table = document.createElement("table");
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        ["Student name", "Roll number", "Team member"].forEach(label => {
            headerRow.append(makeElement("th", "", label));
        });

        thead.append(headerRow);

        const tbody = document.createElement("tbody");

        students.forEach(student => {
            const row = document.createElement("tr");
            row.append(
                makeElement("td", "", student.name || "—"),
                makeElement("td", "", student.roll_number || "—"),
                makeElement("td", "", student.team_member || "—")
            );
            tbody.append(row);
        });

        table.append(thead, tbody);
        rosterContent.append(table);
    } catch (error) {
        if (error.message.includes("No student found")) {
            setMessage(rosterMessage, "No students have registered for this event.");
        } else {
            setMessage(rosterMessage, error.message, "error");
        }
    }
}

document.getElementById("refresh-admin-events").addEventListener("click", loadAdminEvents);

async function startDashboard() {
    if (!getToken()) {
        updateView(false);
        return;
    }

    updateView(true);
    await loadAdminEvents();
}

startDashboard();