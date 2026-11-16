import re
import asistente as ia

INSTR_EN = (
    "IMPORTANT: the app interface is in English and the readers are English speakers. "
    "Write your ENTIRE answer in English, even if the data, the question or earlier "
    "messages are in Spanish. Keep place names (provinces, cities) as they are."
)
REMATE_EN = "\n\n(Please answer in English.)"
TRADUCIR = (
    "This is a translation task, not a data question. Translate the following text "
    "into English. Output ONLY the English translation, with the same formatting "
    "and no comments. Keep place names as they are.\n\n"
)
EJEMPLOS_EN = [
    "Which months have the most thermal detections?",
    "When is fire activity highest in Córdoba?",
    "Which provinces have the most recent detections?",
    "Are there unusual months this year?",
]
_ES = frozenset("el la los las del que por con una es se para más muy en de".split())
_EN = frozenset("the of and is are in to with for that this was were".split())


def parece_espanol(txt):
    palabras = re.findall(r"[a-záéíóúñü]+", txt.lower())
    return sum(p in _ES for p in palabras) > sum(p in _EN for p in palabras)


def responder(pregunta, historial, datos, proveedor, clave, modelo, en=True):
    if not en:
        return ia.responder(pregunta, historial, datos, proveedor, clave, modelo)
    resp = ia.responder(
        pregunta + REMATE_EN, historial, f"{INSTR_EN}\n\n{datos}\n\n{INSTR_EN}",
        proveedor, clave, modelo)
    if parece_espanol(resp):
        try:
            resp = ia.responder(TRADUCIR + resp, [], "", proveedor, clave, modelo)
        except Exception:
            pass  # mejor mostrar la respuesta original que un error
    return resp