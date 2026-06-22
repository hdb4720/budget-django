# budget/periods/period.py
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Period:
    id: str
    start: date
    end: date
    label: str
    sequence: int
