"""Provider package initialization and registration."""
from app.providers.base import provider_registry
from app.providers.email_provider import EmailProvider
from app.providers.sms_provider import SMSProvider
from app.providers.whatsapp_provider import WhatsAppProvider

# Register all providers at import time
provider_registry.register(EmailProvider)
provider_registry.register(SMSProvider)
provider_registry.register(WhatsAppProvider)
