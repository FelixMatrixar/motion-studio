from abc import ABC, abstractmethod
from typing import Dict, Any

class INode(ABC):
    """
    Interface for any step in the pipeline.
    Satisfies LSP: Orchestrator doesn't care what the node does.
    """
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        pass

class IStorageService(ABC):
    """
    Interface for storage operations.
    """
    @abstractmethod
    async def upload(self, local_path: str, destination_path: str) -> str:
        """Uploads a file and returns the public URL."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> None:
        """Deletes a file."""
        pass

class IMediaProcessor(ABC):
    """
    Interface for media processing.
    """
    @abstractmethod
    async def trim_and_resize(self, input_path: str, output_path: str = None) -> str:
        """Returns the path to the processed file."""
        pass
