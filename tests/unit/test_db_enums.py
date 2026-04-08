from app.db.models.document import DocumentStatus
from app.db.models.message import MessageRole


def test_document_status_values_are_stable():
    assert DocumentStatus.PENDING.value == "pending"
    assert DocumentStatus.PROCESSING.value == "processing"
    assert DocumentStatus.COMPLETED.value == "completed"
    assert DocumentStatus.FAILED.value == "failed"


def test_message_role_values_are_stable():
    assert MessageRole.USER.value == "user"
    assert MessageRole.ASSISTANT.value == "assistant"
