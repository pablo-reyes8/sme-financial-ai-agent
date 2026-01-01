from langchain_core.messages import AIMessage, HumanMessage

from sme_agent.services.history import serialize_messages


def test_serialize_messages():
    messages = [HumanMessage(content="hola"), AIMessage(content="respuesta")]
    serialized = serialize_messages(messages)
    assert serialized == [
        {"role": "user", "content": "hola"},
        {"role": "assistant", "content": "respuesta"},
    ]
