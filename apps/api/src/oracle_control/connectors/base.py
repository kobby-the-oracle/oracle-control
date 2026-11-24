from abc import ABC, abstractmethod
from typing import Any
from oracle_control.models import AgentEventIn

class SourceConnector(ABC):
    """Contract for source adapters. Implementations must preserve source IDs and provenance."""
    name: str
    @abstractmethod
    def parse(self, record: dict[str, Any], *, tenant_id: str) -> AgentEventIn:
        raise NotImplementedError
