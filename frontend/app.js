const API_BASE = "https://aits-campus-website.onrender.com/";

const liveList = document.getElementById("live-events-list");
const expiredList = document.getElementById("expired-events-list");
const refreshButton = document.getElementById("refresh-events");
const toast = document.getElementById("toast");

let toastTimer;

function showToast(message, isError = false) {
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.add("show");

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 4000);
}

function formatDeadline(value) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Deadline unavailable";
    }

    return new Intl.DateTimeFormat("en-IN", {
        dateStyle: "medium",
        timeStyle: "short"
    }).format(date);
}

function makeElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    if (text !== undefined) {
        element.textContent = text;
    }

    return element;
}

function showEmpty(container, message) {
    container.replaceChildren(
        makeElement("p", "empty-state", message)
    );
}

function createEventCard(event, expired) {
    const card = makeElement(
        "article",
        expired ? "event-card expired-card" : "event-card"
    );

    const banner = makeElement("div", "event-banner");
    banner.append(
        makeElement("span", "", expired ? "Registration closed" : "Campus event")
    );

    const content = makeElement("div", "event-content");

    content.append(
        makeElement(
            "span",
            `status ${expired ? "status-expired" : "status-live"}`,
            expired ? "Expired" : "Registration open"
        ),
        makeElement("h3", "", event.event_name || "Untitled event"),
        makeElement(
            "p",
            "event-deadline",
            `Deadline: ${formatDeadline(event.deadline)}`
        )
    );

    if (!expired) {
        const form = makeElement("form", "form-stack");
        form.noValidate = false;

        const nameLabel = makeElement("label", "", "Student name");
        const nameInput = makeElement("input");
        nameInput.name = "name";
        nameInput.type = "text";
        nameInput.maxLength = 100;
        nameInput.autocomplete = "name";
        nameInput.required = true;
        nameInput.placeholder = "Enter your full name";
        nameLabel.append(nameInput);

        const rollLabel = makeElement("label", "", "Roll number");
        const rollInput = makeElement("input");
        rollInput.name = "roll_number";
        rollInput.type = "text";
        rollInput.maxLength = 10;
        rollInput.required = true;
        rollInput.autocomplete = "off";
        rollInput.placeholder = "Enter your roll number";
        rollLabel.append(rollInput);

        const submit = makeElement("button", "button button-primary", "Register");
        submit.type = "submit";

        form.append(nameLabel, rollLabel, submit);

        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const name = nameInput.value.trim();
            const rollNumber = rollInput.value.trim();

            if (!name || !rollNumber) {
                showToast("Please enter your name and roll number.", true);
                return;
            }

            submit.disabled = true;
            submit.textContent = "Registering...";

            try {
                const response = await fetch(
                    `${API_BASE}/enrollments/${encodeURIComponent(event.id)}`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            name: name,
                            roll_number: rollNumber
                        })
                    }
                );

                const data = await response.json().catch(() => ({}));

                if (!response.ok) {
                    throw new Error(
                        data.detail || "Registration failed. Please try again."
                    );
                }

                showToast(data.message || "Registration successful!");
                form.reset();
            } catch (error) {
                showToast(
                    error.message === "Failed to fetch"
                        ? "Cannot connect to the backend. Check that FastAPI is running."
                        : error.message,
                    true
                );
            } finally {
                submit.disabled = false;
                submit.textContent = "Register";
            }
        });

        content.append(form);
    }

    card.append(banner, content);
    return card;
}

async function loadEvents() {
    refreshButton.disabled = true;
    liveList.replaceChildren(makeElement("p", "muted", "Loading events..."));
    expiredList.replaceChildren(makeElement("p", "muted", "Loading events..."));

    try {
        const response = await fetch(`${API_BASE}/events`);
        const data = await response.json().catch(() => ({}));

        if (response.status === 404) {
            showEmpty(liveList, "No events have been created yet.");
            showEmpty(expiredList, "No expired events to display.");
            return;
        }

        if (!response.ok) {
            throw new Error(data.detail || "Could not load events.");
        }

        if (!Array.isArray(data)) {
            throw new Error("The events endpoint returned an unexpected response.");
        }

        const now = new Date();
        const liveEvents = [];
        const expiredEvents = [];

        for (const event of data) {
            const deadline = new Date(event.deadline);

            if (Number.isNaN(deadline.getTime())) {
                // Avoid offering registration if a deadline cannot be read.
                expiredEvents.push(event);
            } else if (now > deadline) {
                expiredEvents.push(event);
            } else {
                liveEvents.push(event);
            }
        }

        liveEvents.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));
        expiredEvents.sort((a, b) => new Date(b.deadline) - new Date(a.deadline));

        liveList.replaceChildren();

        if (liveEvents.length === 0) {
            showEmpty(liveList, "There are no live events right now. Check back soon!");
        } else {
            liveEvents.forEach(event => liveList.append(createEventCard(event, false)));
        }

        expiredList.replaceChildren();

        if (expiredEvents.length === 0) {
            showEmpty(expiredList, "No expired events to display.");
        } else {
            expiredEvents.forEach(event => expiredList.append(createEventCard(event, true)));
        }
    } catch (error) {
        showEmpty(liveList, "Unable to load events. Check the backend connection and try refreshing.");
        showEmpty(expiredList, "Events could not be loaded.");

        showToast(
            error.message === "Failed to fetch"
                ? "Cannot connect to FastAPI. Make sure your backend is running."
                : error.message,
            true
        );
    } finally {
        refreshButton.disabled = false;
    }
}

refreshButton.addEventListener("click", loadEvents);

loadEvents();