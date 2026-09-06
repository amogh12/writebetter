from abc import ABC, abstractmethod


class Provider(ABC):
    @abstractmethod
    def complete(self, messages: list[dict], model: str) -> str: ...
