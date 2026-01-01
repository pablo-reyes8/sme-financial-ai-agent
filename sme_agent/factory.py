from __future__ import annotations

import os

from flask import Flask, render_template, request, session
from markdown import markdown
import bleach

from sme_agent.chains import build_chain, build_retriever
from sme_agent.config import Settings, require_openai_key
from sme_agent.prompts import INFO_MESSAGE, QUICK_REPLIES, SUBTITLE, TITLE
from sme_agent.services.classification import RESPUESTAS_RAPIDAS, classify_text, normalize_text
from sme_agent.services.history import build_memory, get_ui_messages, reset_session_state, store_history


ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "code",
    "pre",
    "blockquote",
    "a",
]
ALLOWED_ATTRIBUTES = {"code": ["class"], "pre": ["class"], "a": ["href", "title"]}


def create_app() -> Flask:
    settings = Settings()
    require_openai_key(settings)
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["SETTINGS"] = settings
    app.config["RETRIEVER"] = build_retriever(settings)

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "GET":
            reset_session_state(session)

        ui_messages = get_ui_messages(session)

        if request.method == "POST":
            text = request.form.get("user_input", "").strip()
            if text:
                ui_messages.append({"sender": "user", "text": text})

                normalized = normalize_text(text.lower())
                tipo = classify_text(text)
                if tipo != "consulta":
                    raw = RESPUESTAS_RAPIDAS[tipo]
                elif normalized == "informacion":
                    raw = INFO_MESSAGE
                else:
                    memory = build_memory(session, settings.memory_window)
                    chain = build_chain(settings, app.config["RETRIEVER"], memory)
                    try:
                        raw = chain({"question": text})["answer"]
                        store_history(session, memory)
                    except Exception:
                        raw = (
                            "Ocurrio un problema generando la respuesta. "
                            "Intenta de nuevo o ajusta la pregunta."
                        )

                raw = raw.replace("\\(", "(").replace("\\)", ")")
                html = markdown(raw, extensions=["extra"])
                safe_html = bleach.clean(
                    html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
                )

                ui_messages.append({"sender": "bot", "text": safe_html})

                session["ui_messages"] = ui_messages

        user_count = sum(1 for message in ui_messages if message["sender"] == "user")
        return render_template(
            "index.html",
            title=TITLE,
            subtitle=SUBTITLE,
            messages=ui_messages,
            quick_replies=QUICK_REPLIES,
            user_count=user_count,
        )

    return app
