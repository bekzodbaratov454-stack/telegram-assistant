"""Boshqaruv holati."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ControlState:
    enabled: bool = False
    updated_at: str = ""

    @classmethod
    def default(cls) -> ControlState:
        return cls(enabled=False, updated_at=_now())

    @classmethod
    def from_dict(cls, data: dict) -> ControlState:
        return cls(
            enabled=bool(data.get("enabled", False)),
            updated_at=str(data.get("updated_at", _now())),
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ControlManager:
    def __init__(self, state_path: str | Path) -> None:
        self._path = Path(state_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> ControlState:
        if not self._path.exists():
            state = ControlState.default()
            self.save(state)
            return state
        with self._path.open("r", encoding="utf-8") as f:
            return ControlState.from_dict(json.load(f))

    def save(self, state: ControlState) -> None:
        state.updated_at = _now()
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(asdict(state), f, indent=2, ensure_ascii=False)

    def is_enabled(self) -> bool:
        return self.load().enabled

    def enable(self) -> ControlState:
        state = self.load()
        state.enabled = True
        self.save(state)
        return state

    def disable(self) -> ControlState:
        state = self.load()
        state.enabled = False
        self.save(state)
        return state

    def toggle(self) -> ControlState:
        state = self.load()
        state.enabled = not state.enabled
        self.save(state)
        return state
