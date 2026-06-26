"""Asosiy kirish nuqtasi."""

from __future__ import annotations

import argparse
import asyncio
import base64
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ai.prompts import build_system_prompt
from src.ai.provider import AIProvider
from src.bot.handlers import TelegramAutoReply
from src.config import get_settings
from src.control.state import ControlManager
from src.storage.conversation import ConversationStore


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_session_from_env(session_path: str) -> None:
    """SESSION_BASE64 env variable dan session faylni yaratadi."""
    session_b64 = os.environ.get("SESSION_BASE64")
    if not session_b64:
        return
    session_file = Path(session_path + ".session")
    if session_file.exists():
        return
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_bytes(base64.b64decode(session_b64))
    logging.getLogger(__name__).info("Session fayl SESSION_BASE64 dan yuklandi.")


def cleanup_old_messages(db_path: str, days: int = 3) -> None:
    """3 kundan eski xabarlarni o'chiradi."""
    import sqlite3
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(
            f"DELETE FROM messages WHERE created_at < datetime('now', '-{days} days')"
        )
        conn.commit()
        conn.close()
        logging.getLogger(__name__).info(f"{days} kundan eski xabarlar o'chirildi.")
    except Exception as e:
        logging.getLogger(__name__).warning(f"DB tozalashda xatolik: {e}")


def cmd_status(control: ControlManager) -> None:
    state = control.load()
    status = "YOQILGAN" if state.enabled else "O'CHIRILGAN"
    print(f"Holat: {status}")
    print(f"Yangilangan: {state.updated_at}")


def cmd_enable(control: ControlManager) -> None:
    state = control.enable()
    print(f"AI avtojavob YOQILDI ({state.updated_at})")


def cmd_disable(control: ControlManager) -> None:
    state = control.disable()
    print(f"AI avtojavob O'CHIRILDI ({state.updated_at})")


async def cmd_run(settings, control, store, ai) -> None:
    app = TelegramAutoReply(settings, control, store, ai)
    await app.start()
    print("Tizim ishga tushdi. To'xtatish: Ctrl+C")
    print(f"Boshqaruv: Saved Messages ga '{settings.control_command_prefix} on/off/status' yozing")
    await app.run_until_disconnected()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Telegram AI avtojavob tizimi (shaxsiy akkaunt)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Batafsil log")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Tizimni ishga tushirish")
    sub.add_parser("enable", help="Avtojavobni yoqish")
    sub.add_parser("disable", help="Avtojavobni o'chirish")
    sub.add_parser("status", help="Holatni ko'rish")

    args = parser.parse_args()
    setup_logging(args.verbose)

    settings = get_settings()

    # Session faylni env dan yukla (Render uchun)
    load_session_from_env(settings.session_name)

    # 3 kundan eski xabarlarni o'chir
    cleanup_old_messages(settings.db_path, days=3)

    control = ControlManager(settings.control_state_path)
    store = ConversationStore(settings.db_path, settings.max_history_messages)
    system_prompt = build_system_prompt(
        name=settings.user_name,
        about=settings.user_about,
        tone=settings.user_tone,
        persona=settings.persona,
    )
    ai = AIProvider(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        system_prompt=system_prompt,
        provider=settings.ai_provider,
    )

    if args.command == "run":
        asyncio.run(cmd_run(settings, control, store, ai))
    elif args.command == "enable":
        cmd_enable(control)
    elif args.command == "disable":
        cmd_disable(control)
    elif args.command == "status":
        cmd_status(control)


if __name__ == "__main__":
    main()