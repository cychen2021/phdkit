from typing import Protocol

class ConfigReader(Protocol):
    def __call__(self) -> dict:
        ...