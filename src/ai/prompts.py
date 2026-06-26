"""System prompt tanlash."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BEKZOD_PERSONA_FILE = ROOT / "data" / "bekzod_persona.txt"


def _load_bekzod_prompt() -> str:
    if BEKZOD_PERSONA_FILE.exists():
        return BEKZOD_PERSONA_FILE.read_text(encoding="utf-8").strip()
    return "Sen Bekzod Baratov nomidan javob beruvchi yordamchisan."


def build_system_prompt(
    name: str = "",
    about: str = "",
    tone: str = "",
    persona: str = "bekzod",
) -> str:
    if persona.lower() == "custom" and about.strip():
        return f"""Sen {name or "Foydalanuvchi"} nomidan Telegram xabarlariga javob berasan.

{name or "Foydalanuvchi"} haqida:
{about.strip()}

Uslub: {tone or "do'stona va tabiiy"}

Qoidalar:
- 3-5 gap, qisqa va tabiiy javob ber
- Har doim o'zbek tilida javob ber
- Suhbat kontekstini hisobga ol
- Hech qachon AI ekaningni aytma
- So'ralmagan ma'lumot qo'shma
"""

    return _load_bekzod_prompt()
