"""
Abstract interfaces for dependency injection.

This module defines the contracts that all implementations must follow,
enabling clean separation between the application logic and external services.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, Union
from datetime import datetime


class DatabaseDocument(Protocol):
    """Protocol for database document objects."""
    
    @property
    def id(self) -> str:
        """Document ID."""
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary."""
        ...
    
    @property
    def exists(self) -> bool:
        """Check if document exists."""
        ...


class DatabaseQuery(Protocol):
    """Protocol for database query objects."""
    
    def where(self, filter: Any = None, **kwargs) -> "DatabaseQuery":
        """Add a where filter to the query."""
        ...
    
    def limit(self, count: int) -> "DatabaseQuery":
        """Limit the number of results."""
        ...
    
    def start_after(self, document: DatabaseDocument) -> "DatabaseQuery":
        """Start results after the given document."""
        ...
    
    def stream(self) -> List[DatabaseDocument]:
        """Execute query and return documents."""
        ...


class DatabaseCollection(Protocol):
    """Protocol for database collection objects."""
    
    def add(self, data: Dict[str, Any]) -> tuple:
        """Add a document to the collection."""
        ...
    
    def document(self, doc_id: str) -> DatabaseDocument:
        """Get a document reference."""
        ...
    
    def where(self, filter: Any = None, **kwargs) -> DatabaseQuery:
        """Create a filtered query."""
        ...
    
    def limit(self, count: int) -> DatabaseQuery:
        """Create a limited query."""
        ...
    
    def stream(self) -> List[DatabaseDocument]:
        """Stream all documents."""
        ...


class DatabaseClient(ABC):
    """Abstract database client interface."""
    
    @abstractmethod
    def collection(self, collection_name: str) -> DatabaseCollection:
        """Get a collection reference."""
        pass


class FieldFilterFactory(ABC):
    """Abstract factory for creating field filters."""
    
    @abstractmethod
    def create_filter(self, field: str, op: str, value: Any) -> Any:
        """Create a field filter for database queries."""
        pass


class EncryptionService(ABC):
    """Abstract encryption service interface."""
    
    @abstractmethod
    def encrypt_message(self, plaintext: str) -> Dict[str, Any]:
        """Encrypt a message and return encrypted data."""
        pass
    
    @abstractmethod
    def decrypt_message(self, encrypted_data: Dict[str, Any]) -> str:
        """Decrypt a message from encrypted data."""
        pass


class TelegramMessage(Protocol):
    """Protocol for Telegram message objects."""
    
    @property
    def message_id(self) -> int:
        """Message ID."""
        ...
    
    @property
    def text(self) -> Optional[str]:
        """Message text."""
        ...
    
    @property
    def chat(self) -> "TelegramChat":
        """Chat information."""
        ...
    
    @property
    def from_user(self) -> "TelegramUser":
        """User information."""
        ...


class TelegramChat(Protocol):
    """Protocol for Telegram chat objects."""
    
    @property
    def id(self) -> int:
        """Chat ID."""
        ...
    
    @property
    def title(self) -> Optional[str]:
        """Chat title."""
        ...
    
    @property
    def type(self) -> str:
        """Chat type."""
        ...


class TelegramUser(Protocol):
    """Protocol for Telegram user objects."""
    
    @property
    def id(self) -> int:
        """User ID."""
        ...
    
    @property
    def username(self) -> Optional[str]:
        """Username."""
        ...
    
    @property
    def first_name(self) -> Optional[str]:
        """First name."""
        ...


class TelegramUpdate(Protocol):
    """Protocol for Telegram update objects."""
    
    @property
    def message(self) -> Optional[TelegramMessage]:
        """Message in update."""
        ...


class TelegramBot(ABC):
    """Abstract Telegram bot interface."""
    
    @abstractmethod
    async def send_message(
        self, 
        chat_id: int, 
        text: str, 
        parse_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message to a chat."""
        pass


class TelegramUpdateParser(ABC):
    """Abstract Telegram update parser interface."""
    
    @abstractmethod
    def parse_update(self, update_data: Dict[str, Any]) -> TelegramUpdate:
        """Parse raw update data into TelegramUpdate object."""
        pass


class MessageHandler(ABC):
    """Abstract message handler interface."""
    
    @abstractmethod
    async def handle_message(self, update: TelegramUpdate) -> Optional[int]:
        """Handle an incoming message."""
        pass


# Service container interface
class ServiceContainer(ABC):
    """Abstract service container for dependency injection."""
    
    @abstractmethod
    def get_database_client(self) -> DatabaseClient:
        """Get database client."""
        pass
    
    @abstractmethod
    def get_encryption_service(self) -> EncryptionService:
        """Get encryption service."""
        pass
    
    @abstractmethod
    def get_telegram_bot(self) -> TelegramBot:
        """Get Telegram bot."""
        pass
    
    @abstractmethod
    def get_telegram_update_parser(self) -> TelegramUpdateParser:
        """Get Telegram update parser."""
        pass
    
    @abstractmethod
    def get_field_filter_factory(self) -> FieldFilterFactory:
        """Get field filter factory."""
        pass
    
    @abstractmethod
    def get_message_handler(self) -> MessageHandler:
        """Get message handler."""
        pass 