from datetime import timedelta
from uuid import uuid4

from app.core.security import get_password_hash, verify_password
from app.repositories.auth import TokenRepository


def test_access_token_can_be_validated_by_another_repository_instance() -> None:
    user_id = uuid4()
    organization_id = uuid4()
    token = TokenRepository().create_token(user_id, organization_id)

    claims = TokenRepository().validate_token(token)

    assert claims == {"user_id": user_id, "organization_id": organization_id}


def test_expired_access_token_is_rejected() -> None:
    token = TokenRepository().create_token(uuid4(), uuid4(), expires_delta=timedelta(seconds=-1))

    assert TokenRepository().validate_token(token) is None


def test_invalid_access_token_is_rejected() -> None:
    assert TokenRepository().validate_token("not-a-signed-token") is None


def test_password_hash_verifies_without_storing_plaintext() -> None:
    password = "a-long-password-for-tests"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("incorrect-password", hashed)
