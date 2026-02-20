from typing import Optional, List, Tuple, Dict, Any

from .wati_api import wati_api, Message, Contact


# ─── Contacts ──────────────────────────────────────────────────────

def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number."""
    contacts = wati_api.search_contacts(query)
    return [_contact_to_dict(c) for c in contacts]


def list_contacts(
    page_size: int = 20, page_number: int = 1
) -> List[Dict[str, Any]]:
    """List contacts with pagination."""
    contacts = wati_api.get_contacts(page_size=page_size, page_number=page_number)
    return [_contact_to_dict(c) for c in contacts]


def get_contact(target: str) -> Dict[str, Any]:
    """Get a single contact by phone or ID."""
    contact = wati_api.get_contact(target)
    if contact:
        return _contact_to_dict(contact)
    return {}


def add_contact(
    whatsapp_number: str,
    name: str,
    custom_params: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Add a new WhatsApp contact."""
    contact = wati_api.add_contact(whatsapp_number, name, custom_params)
    if contact:
        return _contact_to_dict(contact)
    return {}


def update_contacts(contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Bulk-update contacts (custom params)."""
    updated = wati_api.update_contacts(contacts)
    return [_contact_to_dict(c) for c in updated]


def get_contact_count() -> int:
    """Get total contact count."""
    return wati_api.get_contact_count()


def assign_contact_teams(target: str, teams: List[str]) -> bool:
    """Assign a contact to teams."""
    return wati_api.assign_contact_teams(target, teams)


# ─── Messages / Conversations ─────────────────────────────────────

def get_messages(
    target: str,
    page_size: int = 20,
    page_number: int = 1,
) -> List[Dict[str, Any]]:
    """Get conversation messages for a target (phone number or conversation ID)."""
    messages = wati_api.get_messages(target, page_size=page_size, page_number=page_number)
    return [_message_to_dict(m) for m in messages]


def send_message(target: str, text: str) -> Tuple[bool, str]:
    """Send a text message to a conversation."""
    return wati_api.send_message(target, text)


def send_file(target: str, file_path: str, caption: str = "") -> Tuple[bool, str]:
    """Send a file attachment via multipart upload."""
    return wati_api.send_file(target, file_path, caption)


def send_file_via_url(
    target: str, file_url: str, caption: Optional[str] = None
) -> Tuple[bool, str]:
    """Send a file by providing its URL (no local download needed)."""
    return wati_api.send_file_via_url(target, file_url, caption)


def download_media(message_id: str) -> Optional[str]:
    """Download media by message ID and return the local file path."""
    return wati_api.download_media(message_id)


def send_interactive(
    target: str,
    interactive_type: str,
    button_message: Optional[Dict] = None,
    list_message: Optional[Dict] = None,
) -> Tuple[bool, str]:
    """Send an interactive message (buttons or list)."""
    return wati_api.send_interactive(target, interactive_type, button_message, list_message)


def assign_operator(target: str, assignee_email: Optional[str] = None) -> bool:
    """Assign an operator to a conversation."""
    return wati_api.assign_operator(target, assignee_email)


def update_conversation_status(target: str, new_status: str) -> bool:
    """Update conversation status (open, solved, pending, block)."""
    return wati_api.update_conversation_status(target, new_status)


# ─── Templates ─────────────────────────────────────────────────────

def list_templates(page_size: int = 20, page_number: int = 1) -> List[Dict]:
    """List message templates."""
    return wati_api.list_templates(page_size, page_number)


def get_template(template_id: str) -> Optional[Dict]:
    """Get template details by ID."""
    return wati_api.get_template(template_id)


def send_template(
    template_name: str,
    broadcast_name: str,
    recipients: List[Dict[str, Any]],
    channel: Optional[str] = None,
) -> Tuple[bool, str]:
    """Send template messages (creates a broadcast)."""
    return wati_api.send_template(template_name, broadcast_name, recipients, channel)


# ─── Campaigns ─────────────────────────────────────────────────────

def list_campaigns(
    page_size: int = 20, page_number: int = 1, channel: Optional[str] = None
) -> List[Dict]:
    """List broadcast campaigns."""
    return wati_api.list_campaigns(page_size, page_number, channel)


def get_campaign(broadcast_id: str) -> Optional[Dict]:
    """Get campaign details by ID."""
    return wati_api.get_campaign(broadcast_id)


# ─── Channels ──────────────────────────────────────────────────────

def list_channels(page_size: int = 20, page_number: int = 1) -> List[Dict]:
    """List WhatsApp channels."""
    return wati_api.list_channels(page_size, page_number)


# ─── Helpers ───────────────────────────────────────────────────────

def _contact_to_dict(contact: Contact) -> Dict[str, Any]:
    """Convert a Contact dataclass to a plain dict."""
    d: Dict[str, Any] = {
        "phone": contact.phone,
        "name": contact.name,
        "id": contact.id,
        "wa_id": contact.wa_id,
        "photo": contact.photo,
        "created": contact.created,
        "last_updated": contact.last_updated,
        "contact_status": contact.contact_status,
        "source": contact.source,
        "channel_id": contact.channel_id,
        "opted_in": contact.opted_in,
        "allow_broadcast": contact.allow_broadcast,
        "teams": contact.teams,
        "channel_type": contact.channel_type,
        "display_name": contact.display_name,
    }
    if contact.custom_params:
        params = {}
        for p in contact.custom_params:
            if isinstance(p, dict) and "name" in p and "value" in p:
                params[p["name"]] = p["value"]
        d["custom_params"] = params
    return d


def _message_to_dict(message: Message) -> Dict[str, Any]:
    """Convert a Message dataclass to a plain dict."""
    return {
        "id": message.id,
        "text": message.text,
        "timestamp": message.timestamp.isoformat(),
        "owner": message.owner,
        "type": message.type,
        "status": message.status,
        "operator_name": message.operator_name,
        "conversation_id": message.conversation_id,
    }
