from __future__ import annotations

import logging
import os
import time
import uuid

from flask import Flask, jsonify, render_template, request, session
from markdown import markdown
import bleach

from sme_agent.chains import build_chain, build_retriever
from sme_agent.config import Settings, require_openai_key
from sme_agent.db import (
    Database,
    ensure_user,
    get_llm_stats,
    list_preferences,
    load_recent_messages,
    save_chat_message,
    save_llm_call,
    save_preference,
)
from sme_agent.prompts import INFO_MESSAGE, QUICK_REPLIES, SUBTITLE, TITLE
from sme_agent.services.classification import RESPUESTAS_RAPIDAS, classify_text, normalize_text
from sme_agent.services.history import build_memory, get_ui_messages, reset_session_state
from sme_agent.services.monitoring import LLMMonitor
from sme_agent.services.preferences import (
    build_preference_context,
    format_preferences,
    is_show_preferences,
    parse_save_command,
)


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

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    logger = logging.getLogger("sme_agent")

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["SETTINGS"] = settings
    app.config["RETRIEVER"] = build_retriever(settings)
    app.config["DB"] = Database(settings.database_url)
    app.config["DB"].init_db()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    if settings.enable_metrics:

        @app.get("/metrics")
        def metrics():
            stats = get_llm_stats(app.config["DB"])
            return jsonify(stats)

    @app.route("/", methods=["GET", "POST"])
    def index():
        user_id = session.get("user_id")
        if not user_id:
            user_id = str(uuid.uuid4())
            session["user_id"] = user_id
        ensure_user(app.config["DB"], user_id)

        if request.method == "GET":
            reset_session_state(session)

        ui_messages = get_ui_messages(session)

        if request.method == "POST":
            text = request.form.get("user_input", "").strip()
            if text:
                ui_messages.append({"sender": "user", "text": text})

                normalized = normalize_text(text.lower())
                save_command = parse_save_command(text)
                if save_command:
                    save_chat_message(app.config["DB"], user_id, "user", text)
                    key, value = save_command
                    save_preference(app.config["DB"], user_id, key, value)
                    raw = (
                        f"Listo. Guarde {key} = {value}. "
                        "Si quieres verlos, escribe: mis datos."
                    )
                elif is_show_preferences(text):
                    save_chat_message(app.config["DB"], user_id, "user", text)
                    prefs = list_preferences(app.config["DB"], user_id)
                    raw = format_preferences(prefs)
                else:
                    tipo = classify_text(text)
                    if tipo != "consulta":
                        save_chat_message(app.config["DB"], user_id, "user", text)
                        raw = RESPUESTAS_RAPIDAS[tipo]
                    elif normalized == "informacion":
                        save_chat_message(app.config["DB"], user_id, "user", text)
                        raw = INFO_MESSAGE
                    else:
                        history_items = load_recent_messages(
                            app.config["DB"], user_id, settings.memory_window * 2
                        )
                        save_chat_message(app.config["DB"], user_id, "user", text)
                        memory = build_memory(
                            session, settings.memory_window, chat_items=history_items
                        )
                        chain = build_chain(settings, app.config["RETRIEVER"], memory)
                        monitor = LLMMonitor()
                        start_time = time.monotonic()
                        status = "ok"
                        error_message = None
                        try:
                            prefs = list_preferences(app.config["DB"], user_id)
                            preference_context = build_preference_context(prefs)
                            question_text = text
                            if preference_context:
                                question_text = f"{text}\n\n{preference_context}"
                            if hasattr(chain, "invoke"):
                                result = chain.invoke(
                                    {"question": question_text},
                                    config={"callbacks": [monitor]},
                                )
                            else:
                                result = chain(
                                    {"question": question_text}, callbacks=[monitor]
                                )
                            raw = result["answer"]
                        except Exception as exc:
                            status = "error"
                            error_message = str(exc)
                            raw = (
                                "Ocurrio un problema generando la respuesta. "
                                "Intenta de nuevo o ajusta la pregunta."
                            )
                            logger.exception("Error en llamada a la cadena")

                        latency_ms = int((time.monotonic() - start_time) * 1000)
                        usage = monitor.usage
                        save_llm_call(
                            app.config["DB"],
                            user_id,
                            usage.model or settings.model_name,
                            latency_ms,
                            usage.prompt_tokens,
                            usage.completion_tokens,
                            usage.total_tokens,
                            status,
                            error_message,
                        )

                raw = raw.replace("\\(", "(").replace("\\)", ")")
                html = markdown(raw, extensions=["extra"])
                safe_html = bleach.clean(
                    html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True
                )

                ui_messages.append({"sender": "bot", "text": safe_html})
                save_chat_message(app.config["DB"], user_id, "assistant", raw)

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
