import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)


def load_env_file() -> None:
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    with env_path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_env_file()


def load_emotions() -> list[str]:
    import json

    config_path = BASE_DIR / "static" / "emotions.json"
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as file:
            config = json.load(file)
        return config.get("emotions", [])
    return ["joie", "tristesse", "colère", "peur", "surprise", "dégoût"]


EMOTION_CLASSES = load_emotions()


class EmotionPredictor:
    def __init__(self) -> None:
        model_repo = os.getenv("EMOFR_MODEL_REPO", "AbdelkarimAouad/camembert-emofr")
        self.token = os.getenv("HF_TOKEN") or os.getenv("token_Hub")
        self.classifier = None
        self.available = False
        self.load_error = None
        self.load_model(model_repo)

    def load_model(self, model_repo: str) -> None:
        try:
            from transformers import pipeline

            options = {}
            if self.token:
                options["token"] = self.token
            self.classifier = pipeline(
                "text-classification",
                model=model_repo,
                top_k=None,
                **options,
            )
            self.available = True
        except Exception as exc:
            self.load_error = str(exc)
            app.logger.warning("Chargement CamemBERT impossible: %s", exc)

    def predict_camembert(self, text: str) -> dict:
        if not self.classifier:
            raise RuntimeError(self.load_error or "Le modèle CamemBERT n'est pas chargé.")

        raw = self.classifier(text, truncation=True, max_length=64)
        predictions = raw[0] if isinstance(raw, list) and raw and isinstance(raw[0], list) else raw
        if not isinstance(predictions, list) or not predictions:
            raise RuntimeError("Réponse inattendue du modèle CamemBERT.")

        return {
            "label": predictions[0]["label"],
            "confidence": round(float(predictions[0]["score"]), 4),
        }


predictor = EmotionPredictor()


@app.get("/")
def index():
    return render_template("index.html", emotions=EMOTION_CLASSES)


@app.post("/api/predict")
def predict():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": "Veuillez saisir une phrase."}), 400
    if len(text) > 1000:
        return jsonify({"error": "La phrase ne doit pas dépasser 1000 caractères."}), 400

    try:
        camembert = predictor.predict_camembert(text)
    except Exception as exc:
        app.logger.error("Erreur CamemBERT: %s", exc)
        return jsonify({
            "error": "Le modèle Hugging Face n'est pas disponible.",
        }), 502

    emotion = camembert["label"]
    confidence = camembert["confidence"]
    method = "CamemBERT chargé depuis Hugging Face"

    return jsonify({
        "text": text,
        "emotion": emotion,
        "confidence": confidence,
        "method": method,
        "provider": "huggingface-direct",
    })


@app.get("/api/status")
def status():
    return jsonify({
        "emotions": EMOTION_CLASSES,
        "models": {"camembert": predictor.available},
        "provider": "huggingface-direct",
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")