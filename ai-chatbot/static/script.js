const form = document.getElementById("chat-form");
const promptInput = document.getElementById("prompt");
const dialectInput = document.getElementById("dialect");
const modelInput = document.getElementById("model");
const responseBox = document.getElementById("response");
const statusBadge = document.getElementById("status");
const copyButton = document.getElementById("copy-btn");
const downloadLink = document.getElementById("download-link");
const notice = document.getElementById("notice");
const historyList = document.getElementById("history-list");

function setOutput(text, warning = "") {
    responseBox.textContent = text || "No output generated.";
    copyButton.disabled = !text;
    downloadLink.href = text ? `/download?query=${encodeURIComponent(text)}` : "#";
    downloadLink.setAttribute("aria-disabled", text ? "false" : "true");

    notice.hidden = !warning;
    notice.textContent = warning;
}

function providerLabel(result) {
    if (result.provider === "openai") {
        return "AI";
    }
    if (result.provider === "groq") {
        return "AI";
    }
    return result.error ? "Local" : "Ready";
}

function renderHistory(history) {
    historyList.innerHTML = "";

    if (!history.length) {
        const empty = document.createElement("p");
        empty.className = "muted";
        empty.textContent = "No recent queries yet.";
        historyList.appendChild(empty);
        return;
    }

    history.forEach((item) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "history-item";
        button.textContent = item.question;
        button.dataset.question = item.question;
        button.dataset.query = item.query;
        historyList.appendChild(button);
    });
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const prompt = promptInput.value.trim();
    if (!prompt) {
        setOutput("", "Please enter a requirement.");
        return;
    }

    statusBadge.textContent = "Generating";
    setOutput("Generating output...");

    try {
        const response = await fetch("/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                prompt,
                dialect: dialectInput.value,
                model: modelInput.value,
            }),
        });

        const data = await response.json();
        const result = data.result || {};
        const output = result.query || data.query || "";
        const warning = result.error || data.error || "";

        if (!response.ok) {
            throw new Error(warning || `Server returned ${response.status}`);
        }

        setOutput(output, warning);
        renderHistory(data.history || []);
        statusBadge.textContent = providerLabel(result);
    } catch (error) {
        setOutput("", `Request failed: ${error.message}`);
        statusBadge.textContent = "Error";
    }
});

copyButton.addEventListener("click", async () => {
    await navigator.clipboard.writeText(responseBox.textContent);
    statusBadge.textContent = "Copied";
    setTimeout(() => {
        statusBadge.textContent = "Ready";
    }, 1200);
});

historyList.addEventListener("click", (event) => {
    const item = event.target.closest(".history-item");
    if (!item) {
        return;
    }

    promptInput.value = item.dataset.question;
    setOutput(item.dataset.query);
});

if (!responseBox.textContent.startsWith("Your SQL")) {
    copyButton.disabled = false;
    downloadLink.href = `/download?query=${encodeURIComponent(responseBox.textContent)}`;
    downloadLink.setAttribute("aria-disabled", "false");
}
