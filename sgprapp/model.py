from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class ApplicationType(Enum):
    Unknown = 0
    PR = 1
    Citizen = 2


class ApplicationStatus(Enum):
    Unknown = 0
    Approved = 1
    Rejected = 2
    Pending = 3
    Appeal = 4

    def as_emoji(self):
        return ["❓", "✅", "❌", "⏳", "🔍"][self.value]


@dataclass
class ApplicationRecord:
    type: ApplicationType
    id: Optional[int]
    nickname: str
    description: str
    status: ApplicationStatus
    start: Optional[date]
    end: Optional[date]
    last_update: Optional[date]

    def formatted(self) -> str:
        return f"""
<b>{self.status.as_emoji()} {self.type.name} Application by {self.nickname}</b>

Description: {self.description}

Status: {self.status.name}

Time span: {self.start} -> {self.end}

<i>Last modified at {self.last_update}</i> @sgprapp
""".strip()

    def __str__(self) -> str:
        return self.formatted()

    def __repr__(self) -> str:
        return self.formatted()


DEFAULT_URLS = {
    ApplicationType.PR: "http://sgprapp.com/listPage",
    # ApplicationType.Citizen: "http://sgprapp.com/citizen",
}
