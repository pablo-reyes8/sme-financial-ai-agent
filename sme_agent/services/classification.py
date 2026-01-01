import re
import unicodedata


_GREETINGS = re.compile(r"(hola|buenas|hey|que tal)\b.*")
_FAREWELLS = re.compile(r"(adios|nos vemos|hasta luego)\b.*")
_THANKS = re.compile(r"(gracias|muchas gracias|mil gracias)\b.*")
_SMALLTALK = re.compile(r"(como estas|como te va|que tal estas)\b.*")


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def classify_text(text: str) -> str:
    txt = normalize_text(text.lower().strip())
    if _GREETINGS.fullmatch(txt):
        return "saludo"
    if _FAREWELLS.fullmatch(txt):
        return "despedida"
    if _THANKS.fullmatch(txt):
        return "agradecimiento"
    if _SMALLTALK.fullmatch(txt):
        return "smalltalk"
    return "consulta"


RESPUESTAS_RAPIDAS = {
    "saludo": "Hola. En que puedo ayudarte hoy con tus finanzas?",
    "despedida": "Hasta luego. Fue un placer ayudarte. Que tengas un excelente dia.",
    "agradecimiento": "El placer es mio. Hay algo mas en lo que pueda asistirte?",
    "smalltalk": "Muy bien, gracias. En que puedo apoyar tus finanzas hoy?",
}
