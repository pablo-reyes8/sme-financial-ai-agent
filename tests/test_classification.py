from sme_agent.services.classification import classify_text


def test_classify_greeting():
    assert classify_text("hola") == "saludo"


def test_classify_farewell():
    assert classify_text("adios") == "despedida"


def test_classify_thanks():
    assert classify_text("gracias") == "agradecimiento"


def test_classify_smalltalk():
    assert classify_text("como estas") == "smalltalk"


def test_classify_default():
    assert classify_text("necesito flujo de caja") == "consulta"
