const form = document.querySelector("#predictionForm");
const textInput = document.querySelector("#textInput");
const characterCount = document.querySelector("#characterCount");
const submitButton = document.querySelector("#submitButton");
const resultSection = document.querySelector("#resultSection");
const emotionName = document.querySelector("#emotionName");
const confidenceValue = document.querySelector("#confidenceValue");
const confidenceBar = document.querySelector("#confidenceBar");
const analyzedText = document.querySelector("#analyzedText");
const methodName = document.querySelector("#methodName");
const modelStatus = document.querySelector("#modelStatus");

textInput.addEventListener("input", () => {
    characterCount.textContent = `${textInput.value.length} / 1000`;
});

async function updateStatus() {
    try {
        const response = await fetch("/api/status");
        const status = await response.json();
        if (status.models.camembert) {
            modelStatus.textContent = "CamemBERT actif";
        } else {
            modelStatus.textContent = "API non configurée";
        }
    } catch (error) {
        modelStatus.textContent = "API indisponible";
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const text = textInput.value.trim();
    if (!text) {
        textInput.focus();
        return;
    }

    submitButton.disabled = true;
    submitButton.firstElementChild.textContent = "Analyse...";
    resultSection.hidden = false;

    try {
        const response = await fetch("/api/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text }),
        });
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Impossible d'analyser cette phrase.");
        }

        emotionName.textContent = result.emotion;
        emotionName.classList.remove("error");
        methodName.textContent = result.method;
        analyzedText.textContent = `« ${result.text} »`;

        if (typeof result.confidence === "number") {
            const percent = Math.round(result.confidence * 100);
            confidenceValue.textContent = `${percent}%`;
            confidenceBar.style.width = `${percent}%`;
        } else {
            confidenceValue.textContent = "—";
            confidenceBar.style.width = "0";
        }
    } catch (error) {
        emotionName.textContent = "Erreur";
        emotionName.classList.add("error");
        confidenceValue.textContent = "—";
        confidenceBar.style.width = "0";
        methodName.textContent = "";
        analyzedText.textContent = error.message;
    } finally {
        submitButton.disabled = false;
        submitButton.firstElementChild.textContent = "Analyser";
        resultSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
});

updateStatus();
