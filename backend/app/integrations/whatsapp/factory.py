from typing import Optional
from app.integrations.whatsapp.base import WhatsAppProvider
from app.integrations.whatsapp.mock_provider import MockWhatsAppProvider
from app.integrations.whatsapp.cloud_api import WhatsAppCloudAPIProvider
from app.core.config import settings


_provider_instance: Optional[WhatsAppProvider] = None


def get_whatsapp_provider() -> WhatsAppProvider:
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    if settings.whatsapp_mock_mode:
        _provider_instance = MockWhatsAppProvider()
    else:
        # In production, we need to get credentials from the database
        # This will be set up when an account is configured
        _provider_instance = MockWhatsAppProvider()

    return _provider_instance


def set_whatsapp_provider(provider: WhatsAppProvider):
    global _provider_instance
    _provider_instance = provider


def create_cloud_api_provider(
    access_token: str,
    phone_number_id: str,
    business_account_id: str,
    webhook_verify_token: str,
) -> WhatsAppCloudAPIProvider:
    return WhatsAppCloudAPIProvider(
        access_token=access_token,
        phone_number_id=phone_number_id,
        business_account_id=business_account_id,
        webhook_verify_token=webhook_verify_token,
    )