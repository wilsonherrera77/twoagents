"""
Servicio HTTP local que expone Claude como endpoint.
El usuario interactúa manualmente con esta interfaz web.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from flask import Flask, Response, jsonify, render_template_string, request

app = Flask(__name__)

pending_prompts: List[Dict[str, object]] = []
responses: Dict[int, str] = {}


@app.route("/")
def index() -> str:
    """Renderiza la interfaz principal para gestionar prompts pendientes."""

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Claude Service - Discovery Motor V10</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1e1e1e; color: #ffffff; }
            .prompt { background: #2d2d2d; padding: 20px; margin: 10px 0; border-radius: 8px; }
            .prompt-id { color: #4CAF50; font-weight: bold; }
            textarea { width: 100%; height: 200px; background: #1e1e1e; color: #ffffff;
                       border: 1px solid #4CAF50; padding: 10px; font-family: monospace; }
            button { background: #4CAF50; color: white; padding: 10px 20px;
                     border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #45a049; }
            .status { color: #ffa500; }
            pre { background: #000000; padding: 10px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }
        </style>
    </head>
    <body>
        <h1>🤖 Claude Service - Discovery Motor V10</h1>
        <p class="status">Prompts pendientes: {{ pending_count }}</p>

        {% for prompt in prompts %}
        <div class="prompt">
            <div class="prompt-id">Prompt ID: {{ prompt.id }}</div>
            <div><strong>Timestamp:</strong> {{ prompt.timestamp }}</div>
            <div><strong>Tipo:</strong> {{ prompt.type }}</div>
            <pre>{{ prompt.text }}</pre>

            <form action="/respond/{{ prompt.id }}" method="post">
                <textarea name="response" placeholder="Pega aquí la respuesta de Claude..."></textarea><br>
                <button type="submit">Enviar Respuesta</button>
            </form>
        </div>
        {% endfor %}

        {% if pending_count == 0 %}
        <p>✅ No hay prompts pendientes. El sistema está esperando...</p>
        {% endif %}
    </body>
    </html>
    """
    return render_template_string(html, prompts=pending_prompts, pending_count=len(pending_prompts))


@app.route("/health")
def health() -> Response:
    """Expone el estado del servicio para herramientas externas."""

    return jsonify({"status": "ok", "pending_prompts": len(pending_prompts)})


def _enqueue_prompt(prompt: str, prompt_type: str) -> Dict[str, object]:
    prompt_id = len(pending_prompts) + 1
    prompt_data = {
        "id": prompt_id,
        "type": prompt_type,
        "text": prompt,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    pending_prompts.append(prompt_data)
    return prompt_data


def _wait_for_response(prompt_data: Dict[str, object], max_wait: int = 300) -> Dict[str, str]:
    import time

    prompt_id = prompt_data["id"]
    waited = 0
    while waited < max_wait:
        if prompt_id in responses:
            response = responses.pop(prompt_id)
            pending_prompts.remove(prompt_data)
            return {"response": response}
        time.sleep(2)
        waited += 2
    return {"error": "Timeout esperando respuesta"}


@app.route("/analyze", methods=["POST"])
def analyze():
    """Endpoint que utiliza el PM Agent para obtener especificaciones."""

    data = request.json or {}
    prompt = data.get("prompt", "")
    prompt_data = _enqueue_prompt(prompt, "PM_ANALYSIS")
    result = _wait_for_response(prompt_data)
    status = 200 if "response" in result else 408
    return jsonify(result), status


@app.route("/generate", methods=["POST"])
def generate():
    """Endpoint que utiliza el Dev Agent para generar código."""

    data = request.json or {}
    prompt = data.get("prompt", "")
    prompt_data = _enqueue_prompt(prompt, "CODE_GENERATION")
    result = _wait_for_response(prompt_data)
    status = 200 if "response" in result else 408
    return jsonify(result), status


@app.route("/respond/<int:prompt_id>", methods=["POST"])
def respond(prompt_id: int) -> str:
    """Permite al usuario registrar la respuesta manual de Claude."""

    response_text = request.form.get("response", "")
    responses[prompt_id] = response_text
    return """
    <html>
    <body style="background: #1e1e1e; color: #ffffff; font-family: Arial, sans-serif;">
        <h2>✅ Respuesta enviada!</h2>
        <p>El agente recibirá tu respuesta.</p>
        <a href="/" style="color: #4CAF50;">← Volver a prompts pendientes</a>
    </body>
    </html>
    """


if __name__ == "__main__":
    print("🚀 Claude Service iniciado en http://localhost:5000")
    print("📝 Abre el navegador para responder prompts del sistema")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
