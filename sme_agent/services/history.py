from __future__ import annotations

from typing import Dict, List, Optional

from langchain.memory import ChatMessageHistory, ConversationBufferWindowMemory
from langchain_core.messages import AIMessage, HumanMessage

from sme_agent.prompts import WELCOME_MESSAGES


def reset_session_state(session: Dict) -> None:
    session["chat_history"] = []
    session["ui_messages"] = [msg.copy() for msg in WELCOME_MESSAGES]


def get_ui_messages(session: Dict) -> List[Dict[str, str]]:
    if "ui_messages" not in session:
        session["ui_messages"] = [msg.copy() for msg in WELCOME_MESSAGES]
    return session["ui_messages"]


def build_memory(session: Dict, k: int, chat_items: Optional[List[Dict[str, str]]] = None) -> ConversationBufferWindowMemory:
    history = ChatMessageHistory()
    source_items = chat_items if chat_items is not None else session.get("chat_history", [])
    for item in source_items:
        role = item.get("role")
        content = item.get("content", "")
        if role == "user":
            history.add_user_message(content)
        else:
            history.add_ai_message(content)
    return ConversationBufferWindowMemory(
        chat_memory=history,
        k=k,
        return_messages=True,
        memory_key="chat_history",
        input_key="question",
        output_key="answer",
    )


def serialize_messages(messages: List) -> List[Dict[str, str]]:
    serialized = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        else:
            role = "assistant"
        serialized.append({"role": role, "content": message.content})
    return serialized


def store_history(session: Dict, memory: ConversationBufferWindowMemory) -> None:
    session["chat_history"] = serialize_messages(memory.chat_memory.messages)
