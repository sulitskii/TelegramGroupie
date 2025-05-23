"""Mock Firestore implementation for testing"""

import uuid
from datetime import datetime
from typing import Any


class MockDocument:
    """Mock Firestore document"""

    def __init__(self, doc_id: str, data: dict[str, Any]):
        self.id = doc_id
        self._data = data

    def to_dict(self) -> dict[str, Any]:
        return self._data.copy()

    @property
    def exists(self) -> bool:
        return True


class MockQuery:
    """Mock Firestore query"""

    def __init__(self, collection_name: str, mock_client):
        self.collection_name = collection_name
        self.mock_client = mock_client
        self._filters = []
        self._limit_value = None
        self._start_after_doc = None

    def where(self, filter=None, **kwargs):
        """Add a filter to the query"""
        # For compatibility with both old and new syntax
        if filter:
            self._filters.append(filter)
        elif kwargs:
            # Handle old-style where(field, op, value)
            field = kwargs.get("field")
            op = kwargs.get("op")
            value = kwargs.get("value")
            if field and op and value is not None:
                self._filters.append({"field": field, "op": op, "value": value})
        return self

    def limit(self, count: int):
        """Limit the number of results"""
        self._limit_value = count
        return self

    def start_after(self, doc):
        """Start after a specific document"""
        self._start_after_doc = doc
        return self

    def stream(self) -> list[MockDocument]:
        """Execute the query and return documents"""
        # Get all documents from the collection
        all_docs = self.mock_client._collections.get(self.collection_name, [])

        # Apply filters
        filtered_docs = []
        for doc in all_docs:
            matches = True
            for filter_obj in self._filters:
                if hasattr(filter_obj, "field") and hasattr(filter_obj, "value"):
                    # New filter format
                    field = filter_obj.field
                    value = filter_obj.value
                elif isinstance(filter_obj, dict):
                    # Dict format
                    field = filter_obj["field"]
                    value = filter_obj["value"]
                else:
                    continue

                if field in doc._data and doc._data[field] != value:
                    matches = False
                    break

            if matches:
                filtered_docs.append(doc)

        # Apply limit
        if self._limit_value:
            filtered_docs = filtered_docs[: self._limit_value]

        return filtered_docs


class MockCollection:
    """Mock Firestore collection"""

    def __init__(self, collection_name: str, mock_client):
        self.collection_name = collection_name
        self.mock_client = mock_client

    def add(self, data: dict[str, Any]) -> tuple:
        """Add a document to the collection"""
        doc_id = str(uuid.uuid4())
        doc = MockDocument(doc_id, data)

        if self.collection_name not in self.mock_client._collections:
            self.mock_client._collections[self.collection_name] = []

        self.mock_client._collections[self.collection_name].append(doc)
        return (datetime.utcnow(), doc)

    def document(self, doc_id: str):
        """Get a document reference"""
        docs = self.mock_client._collections.get(self.collection_name, [])
        for doc in docs:
            if doc.id == doc_id:
                return doc
        return MockDocument(doc_id, {})

    def where(self, filter=None, **kwargs):
        """Create a query with a filter"""
        query = MockQuery(self.collection_name, self.mock_client)
        return query.where(filter=filter, **kwargs)

    def limit(self, count: int):
        """Create a query with a limit"""
        query = MockQuery(self.collection_name, self.mock_client)
        return query.limit(count)

    def stream(self):
        """Stream all documents in the collection"""
        return self.mock_client._collections.get(self.collection_name, [])


class MockFirestoreClient:
    """Mock Firestore client for testing"""

    def __init__(self):
        self._collections = {}
        # Add some sample data for testing
        self._seed_test_data()

    def collection(self, collection_name: str) -> MockCollection:
        """Get a collection reference"""
        return MockCollection(collection_name, self)

    def _seed_test_data(self):
        """Add some test data for integration tests"""
        messages_data = [
            {
                "message_id": 1,
                "chat_id": -100123456789,
                "chat_title": "Test Group",
                "user_id": 123456,
                "username": "testuser",
                "encrypted_text": {
                    "ciphertext": "mock_encrypted_text_1",
                    "encrypted_data_key": "mock_key_1",
                    "iv": "mock_iv_1",
                    "salt": "mock_salt_1",
                },
                "timestamp": datetime.utcnow(),
                "type": "telegram",
            },
            {
                "message_id": 2,
                "chat_id": -100123456789,
                "chat_title": "Test Group",
                "user_id": 789012,
                "username": "testuser2",
                "encrypted_text": {
                    "ciphertext": "mock_encrypted_text_2",
                    "encrypted_data_key": "mock_key_2",
                    "iv": "mock_iv_2",
                    "salt": "mock_salt_2",
                },
                "timestamp": datetime.utcnow(),
                "type": "telegram",
            },
        ]

        # Add test messages
        self._collections["messages"] = [
            MockDocument(f"msg_{i}", data) for i, data in enumerate(messages_data)
        ]


# Mock FieldFilter for compatibility
class MockFieldFilter:
    """Mock FieldFilter for compatibility with real Firestore"""

    def __init__(self, field: str, op: str, value: Any):
        self.field = field
        self.op = op
        self.value = value


# For compatibility with the main app
def Client():
    """Create a mock Firestore client"""
    return MockFirestoreClient()
