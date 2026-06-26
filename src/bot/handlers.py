"""Telethon klient va xabar handlerlari."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import TYPE_CHECKING

from telethon import TelegramClient, events
from telethon.tl.types import User

from src.ai.provider import AIProvider
from src.control.state import ControlManager
from src.storage.conversation import ConversationStore

if TYPE_CHECKING:
    from src.config import Settings

logger = logging.getLogger(__name__)


class TelegramAutoReply:
    def __init__(
        self,
        settings: Settings,
        control: ControlManager,
        store: ConversationStore,
        ai: AIProvider,
    ) -> None:
        self._settings = settings
        self._control = control
        self._store = store
        self._ai = ai
        self._me_id: int | None = None

        self.client = TelegramClient(
            settings.session_name,
            settings.telegram_api_id,
            settings.telegram_api_hash,
        )

    async def start(self) -> None:
        await self._store.init()
        await self.client.start(phone=self._settings.telegram_phone)
        me = await self.client.get_me()
        self._me_id = me.id
        logger.info("Telegram ga ulandi: %s (id=%s)", me.first_name, me.id)

        self.client.add_event_handler(
            self._on_new_message,
            events.NewMessage(incoming=True),
        )
        self.client.add_event_handler(
            self._on_self_command,
            events.NewMessage(outgoing=True, func=lambda e: e.is_private),
        )

    async def run_until_disconnected(self) -> None:
        await self.client.run_until_disconnected()

    async def _on_new_message(self, event: events.NewMessage.Event) -> None:
        if not event.is_private:
            return

        sender = await event.get_sender()
        if not isinstance(sender, User) or sender.bot:
            return

        if not self._control.is_enabled():
            return

        text = (event.message.message or "").strip()
        if not text:
            return

        chat_id = event.chat_id
        logger.info("Yangi xabar chat_id=%s: %s", chat_id, text[:80])

        delay = random.uniform(
            self._settings.min_reply_delay,
            self._settings.max_reply_delay,
        )
        await asyncio.sleep(delay)

        if not self._control.is_enabled():
            return

        try:
            history = await self._store.get_history(chat_id)
            reply = await self._ai.generate_reply(history, text)

            await self._send_reply(event, reply)

            await self._store.add_message(chat_id, "user", text)
            await self._store.add_message(chat_id, "assistant", reply)

            logger.info("Javob yuborildi chat_id=%s", chat_id)
        except Exception:
            logger.exception("Xabarga javob berishda xatolik chat_id=%s", chat_id)

    async def _send_reply(self, event: events.NewMessage.Event, text: str) -> None:
        try:
            await event.respond(text, parse_mode="md")
        except Exception:
            logger.warning("Markdown xato, oddiy matn yuborilmoqda")
            await event.respond(text)

    async def _on_self_command(self, event: events.NewMessage.Event) -> None:
        if event.chat_id != self._me_id:
            return
        await self._handle_self_command(event)

    async def _handle_self_command(self, event: events.NewMessage.Event) -> None:
        """Saved Messages orqali boshqaruv: .ai on / .ai off / .ai status"""
        text = (event.message.message or "").strip().lower()
        prefix = self._settings.control_command_prefix.lower()

        commands = {
            f"{prefix} on": self._cmd_enable,
            f"{prefix} off": self._cmd_disable,
            f"{prefix} toggle": self._cmd_toggle,
            f"{prefix} status": self._cmd_status,
        }

        handler = commands.get(text)
        if handler:
            await handler(event)

    async def _cmd_enable(self, event: events.NewMessage.Event) -> None:
        self._control.enable()
        await event.respond("AI avtojavob YOQILDI.")

    async def _cmd_disable(self, event: events.NewMessage.Event) -> None:
        self._control.disable()
        await event.respond("AI avtojavob O'CHIRILDI.")

    async def _cmd_toggle(self, event: events.NewMessage.Event) -> None:
        state = self._control.toggle()
        status = "YOQILDI" if state.enabled else "O'CHIRILDI"
        await event.respond(f"AI avtojavob {status}.")

    async def _cmd_status(self, event: events.NewMessage.Event) -> None:
        state = self._control.load()
        status = "yoqilgan" if state.enabled else "o'chirilgan"
        await event.respond(f"Holat: {status}\nYangilangan: {state.updated_at}")
