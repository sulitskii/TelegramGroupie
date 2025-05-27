"""
Service containers for dependency injection.

This module provides service containers that create and manage
all the services needed by the application, using the appropriate
implementations based on the environment.
"""

import logging
import os
from typing import Optional

from interfaces import (
    DatabaseClient,
    EncryptionService,
    FieldFilterFactory,
    MessageHandler,
    ServiceContainer,
    TelegramBot,
    TelegramUpdateParser,
)

logger = logging.getLogger(__name__)


class ProductionServiceContainer(ServiceContainer):
    """Service container for production environment using real GCP services."""
    
    def __init__(self):
        logger.info("🏭 Initializing production service container...")
        self._db_client: Optional[DatabaseClient] = None
        self._encryption_service: Optional[EncryptionService] = None
        self._telegram_bot: Optional[TelegramBot] = None
        self._telegram_update_parser: Optional[TelegramUpdateParser] = None
        self._field_filter_factory: Optional[FieldFilterFactory] = None
        self._message_handler: Optional[MessageHandler] = None
        
        # Validate required environment variables
        self._validate_environment()
        logger.info("✅ Production service container initialized successfully")
    
    def _validate_environment(self):
        """Validate that all required environment variables are set."""
        required_vars = {
            "GCP_PROJECT_ID": "Google Cloud Project ID",
            "TELEGRAM_TOKEN": "Telegram Bot Token",
            "WEBHOOK_SECRET": "Webhook Secret",
        }
        
        missing_vars = []
        for var, description in required_vars.items():
            if not os.environ.get(var):
                missing_vars.append(f"{var} ({description})")
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables for production: {', '.join(missing_vars)}"
            )
    
    def get_database_client(self) -> DatabaseClient:
        if self._db_client is None:
            from implementations.production import ProductionDatabaseClient
            self._db_client = ProductionDatabaseClient()
        return self._db_client
    
    def get_encryption_service(self) -> EncryptionService:
        if self._encryption_service is None:
            from implementations.production import ProductionEncryptionService
            
            project_id = os.environ.get("GCP_PROJECT_ID")
            kms_location = os.environ.get("KMS_LOCATION", "global")
            kms_key_ring = os.environ.get("KMS_KEY_RING", "telegram-messages")
            kms_key_id = os.environ.get("KMS_KEY_ID", "message-key")
            
            self._encryption_service = ProductionEncryptionService(
                project_id=project_id,
                location_id=kms_location,
                key_ring_id=kms_key_ring,
                key_id=kms_key_id,
            )
        return self._encryption_service
    
    def get_telegram_bot(self) -> TelegramBot:
        if self._telegram_bot is None:
            from implementations.production import ProductionTelegramBot
            
            token = os.environ.get("TELEGRAM_TOKEN")
            self._telegram_bot = ProductionTelegramBot(token)
        return self._telegram_bot
    
    def get_telegram_update_parser(self) -> TelegramUpdateParser:
        if self._telegram_update_parser is None:
            from implementations.production import ProductionTelegramUpdateParser
            from telegram import Bot
            
            token = os.environ.get("TELEGRAM_TOKEN")
            bot = Bot(token=token)
            self._telegram_update_parser = ProductionTelegramUpdateParser(bot)
        return self._telegram_update_parser
    
    def get_field_filter_factory(self) -> FieldFilterFactory:
        if self._field_filter_factory is None:
            from implementations.production import ProductionFieldFilterFactory
            self._field_filter_factory = ProductionFieldFilterFactory()
        return self._field_filter_factory
    
    def get_message_handler(self) -> MessageHandler:
        if self._message_handler is None:
            from implementations.production import ProductionMessageHandler
            
            self._message_handler = ProductionMessageHandler(
                db_client=self.get_database_client(),
                encryption_service=self.get_encryption_service(),
                telegram_bot=self.get_telegram_bot(),
            )
        return self._message_handler


class TestServiceContainer(ServiceContainer):
    """Service container for test environment using mock implementations."""
    
    def __init__(self):
        logger.info("🧪 Initializing test service container...")
        self._db_client: Optional[DatabaseClient] = None
        self._encryption_service: Optional[EncryptionService] = None
        self._telegram_bot: Optional[TelegramBot] = None
        self._telegram_update_parser: Optional[TelegramUpdateParser] = None
        self._field_filter_factory: Optional[FieldFilterFactory] = None
        self._message_handler: Optional[MessageHandler] = None
        logger.info("✅ Test service container initialized successfully")
    
    def get_database_client(self) -> DatabaseClient:
        if self._db_client is None:
            from implementations.test import TestDatabaseClient
            self._db_client = TestDatabaseClient()
        return self._db_client
    
    def get_encryption_service(self) -> EncryptionService:
        if self._encryption_service is None:
            from implementations.test import TestEncryptionService
            
            project_id = os.environ.get("GCP_PROJECT_ID", "test-project")
            kms_location = os.environ.get("KMS_LOCATION", "global")
            kms_key_ring = os.environ.get("KMS_KEY_RING", "test-key-ring")
            kms_key_id = os.environ.get("KMS_KEY_ID", "test-key")
            
            self._encryption_service = TestEncryptionService(
                project_id=project_id,
                location_id=kms_location,
                key_ring_id=kms_key_ring,
                key_id=kms_key_id,
            )
        return self._encryption_service
    
    def get_telegram_bot(self) -> TelegramBot:
        if self._telegram_bot is None:
            from implementations.test import TestTelegramBot
            
            token = os.environ.get("TELEGRAM_TOKEN", "test-token")
            self._telegram_bot = TestTelegramBot(token)
        return self._telegram_bot
    
    def get_telegram_update_parser(self) -> TelegramUpdateParser:
        if self._telegram_update_parser is None:
            from implementations.test import TestTelegramUpdateParser
            self._telegram_update_parser = TestTelegramUpdateParser()
        return self._telegram_update_parser
    
    def get_field_filter_factory(self) -> FieldFilterFactory:
        if self._field_filter_factory is None:
            from implementations.test import TestFieldFilterFactory
            self._field_filter_factory = TestFieldFilterFactory()
        return self._field_filter_factory
    
    def get_message_handler(self) -> MessageHandler:
        if self._message_handler is None:
            from implementations.test import TestMessageHandler
            
            self._message_handler = TestMessageHandler(
                db_client=self.get_database_client(),
                encryption_service=self.get_encryption_service(),
                telegram_bot=self.get_telegram_bot(),
            )
        return self._message_handler


def create_service_container(environment: str = None) -> ServiceContainer:
    """
    Factory function to create the appropriate service container.
    
    Args:
        environment: The environment to create the container for.
                    If None, will be determined from environment variables.
                    
    Returns:
        The appropriate service container instance.
    """
    if environment is None:
        # Determine environment from context
        if os.environ.get("FLASK_ENV") == "testing":
            environment = "test"
        elif os.environ.get("APP_ENV") == "test":
            environment = "test"
        elif "pytest" in os.environ.get("_", ""):
            environment = "test"
        else:
            environment = "production"
    
    logger.info(f"🔧 Creating service container for environment: {environment}")
    
    if environment == "test":
        return TestServiceContainer()
    elif environment == "production":
        return ProductionServiceContainer()
    else:
        raise ValueError(f"Unknown environment: {environment}. Use 'test' or 'production'.")


# Global service container instance (initialized by the application)
_service_container: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    """Get the global service container instance."""
    global _service_container
    if _service_container is None:
        raise RuntimeError(
            "Service container not initialized. Call initialize_service_container() first."
        )
    return _service_container


def initialize_service_container(environment: str = None) -> ServiceContainer:
    """Initialize the global service container."""
    global _service_container
    _service_container = create_service_container(environment)
    logger.info(f"🚀 Service container initialized for {environment or 'auto-detected'} environment")
    return _service_container


def reset_service_container():
    """Reset the global service container (useful for testing)."""
    global _service_container
    _service_container = None 