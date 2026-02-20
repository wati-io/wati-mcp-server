from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from .whatsapp import (
    search_contacts as wa_search_contacts,
    list_contacts as wa_list_contacts,
    get_contact as wa_get_contact,
    add_contact as wa_add_contact,
    get_messages as wa_get_messages,
    send_message as wa_send_message,
    send_file as wa_send_file,
    send_file_via_url as wa_send_file_via_url,
    download_media as wa_download_media,
    send_interactive as wa_send_interactive,
    assign_operator as wa_assign_operator,
    update_conversation_status as wa_update_conversation_status,
    list_templates as wa_list_templates,
    get_template as wa_get_template,
    send_template as wa_send_template,
    list_campaigns as wa_list_campaigns,
    get_campaign as wa_get_campaign,
    list_channels as wa_list_channels,
    update_contacts as wa_update_contacts,
    get_contact_count as wa_get_contact_count,
    assign_contact_teams as wa_assign_contact_teams,
)

# Initialize FastMCP server
mcp = FastMCP("whatsapp")


# ─── Contacts ──────────────────────────────────────────────────────


@mcp.tool()
def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number.
    Returns contact information including name, phone, WhatsApp ID, status,
    teams, and custom parameters.

    Args:
        query: A search term to find matching contacts (name or phone)
    """
    return wa_search_contacts(query)


@mcp.tool()
def list_contacts(
    page_size: int = 20, page_number: int = 1
) -> List[Dict[str, Any]]:
    """List WhatsApp contacts with pagination.

    Args:
        page_size: Number of contacts per page (max 100, default 20)
        page_number: Page number, 1-based (default 1)
    """
    return wa_list_contacts(page_size=page_size, page_number=page_number)


@mcp.tool()
def get_contact(target: str) -> Dict[str, Any]:
    """Get detailed information about a specific contact.

    Args:
        target: Phone number (e.g. "85264318721") or contact ID
    """
    return wa_get_contact(target)


@mcp.tool()
def add_contact(
    whatsapp_number: str,
    name: str,
    custom_params: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Add a new WhatsApp contact.

    Args:
        whatsapp_number: Phone number with country code, no + (e.g. "85264318721")
        name: Contact display name
        custom_params: Optional list of {"name": "key", "value": "val"} pairs
    """
    result = wa_add_contact(whatsapp_number, name, custom_params)
    if result:
        return {"success": True, "contact": result}
    return {"success": False, "message": "Failed to add contact"}


@mcp.tool()
def update_contacts(
    contacts: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Bulk-update contacts' custom parameters.

    Args:
        contacts: List of {"target": "phone_or_id", "customParams": [{"name": "k", "value": "v"}]}
    """
    updated = wa_update_contacts(contacts)
    return {"success": bool(updated), "updated_count": len(updated), "contacts": updated}


@mcp.tool()
def get_contact_count() -> Dict[str, Any]:
    """Get total number of WhatsApp contacts."""
    count = wa_get_contact_count()
    return {"count": count}


@mcp.tool()
def assign_contact_teams(target: str, teams: List[str]) -> Dict[str, Any]:
    """Assign a contact to one or more teams.

    Args:
        target: Phone number or contact ID
        teams: List of team names (e.g. ["Support", "Sales"])
    """
    success = wa_assign_contact_teams(target, teams)
    return {"success": success}


# ─── Messages / Conversations ─────────────────────────────────────


@mcp.tool()
def get_messages(
    target: str,
    page_size: int = 20,
    page_number: int = 1,
) -> List[Dict[str, Any]]:
    """Get conversation messages for a contact or conversation.

    Args:
        target: Phone number (e.g. "85264318721") or conversation ID
        page_size: Messages per page (max 100, default 20)
        page_number: Page number, 1-based (default 1)
    """
    return wa_get_messages(target, page_size=page_size, page_number=page_number)


@mcp.tool()
def send_message(target: str, text: str) -> Dict[str, Any]:
    """Send a WhatsApp text message to a contact.

    Args:
        target: Recipient phone number with country code, no + (e.g. "85264318721")
        text: The message text to send
    """
    if not target:
        return {"success": False, "message": "Target must be provided"}
    success, msg = wa_send_message(target, text)
    return {"success": success, "message": msg}


@mcp.tool()
def send_file(target: str, file_path: str, caption: str = "") -> Dict[str, Any]:
    """Send a file (image, video, document, audio) via WhatsApp.

    Args:
        target: Recipient phone number with country code, no + (e.g. "85264318721")
        file_path: Absolute path to the file or a URL
        caption: Optional caption for the file
    """
    success, msg = wa_send_file(target, file_path, caption)
    return {"success": success, "message": msg}


@mcp.tool()
def send_file_via_url(
    target: str, file_url: str, caption: Optional[str] = None
) -> Dict[str, Any]:
    """Send a file by URL without downloading it locally first.

    Args:
        target: Recipient phone number with country code, no + (e.g. "85264318721")
        file_url: Public URL of the file to send
        caption: Optional caption
    """
    success, msg = wa_send_file_via_url(target, file_url, caption)
    return {"success": success, "message": msg}


@mcp.tool()
def download_media(message_id: str) -> Dict[str, Any]:
    """Download media from a WhatsApp message.

    Args:
        message_id: The ID of the message containing the media
    """
    file_path = wa_download_media(message_id)
    if file_path:
        return {"success": True, "message": "Media downloaded", "file_path": file_path}
    return {"success": False, "message": "Failed to download media"}


@mcp.tool()
def send_interactive(
    target: str,
    interactive_type: str,
    body_text: str,
    buttons: Optional[List[Dict[str, str]]] = None,
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    button_text: Optional[str] = None,
    sections: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Send an interactive WhatsApp message with buttons or a list.

    Args:
        target: Recipient phone number with country code, no + (e.g. "85264318721")
        interactive_type: Either "buttons" or "list"
        body_text: Main message body text
        buttons: For type="buttons": list of {"text": "Button label"} (max 3)
        header_text: Optional header text
        footer_text: Optional footer text
        button_text: For type="list": text shown on the list button
        sections: For type="list": list of {"title": "...", "rows": [{"title": "...", "description": "..."}]}
    """
    if not target:
        return {"success": False, "message": "Target must be provided"}
    if interactive_type not in ("buttons", "list"):
        return {"success": False, "message": "type must be 'buttons' or 'list'"}

    if interactive_type == "buttons":
        if not buttons:
            return {"success": False, "message": "buttons required for type='buttons'"}
        button_message: Dict[str, Any] = {"body": body_text, "buttons": buttons}
        if header_text:
            button_message["header"] = {"type": "text", "text": header_text}
        if footer_text:
            button_message["footer"] = footer_text
        success, msg = wa_send_interactive(target, "buttons", button_message=button_message)
    else:
        if not sections:
            return {"success": False, "message": "sections required for type='list'"}
        list_message: Dict[str, Any] = {"body": body_text, "sections": sections}
        if header_text:
            list_message["header"] = header_text
        if footer_text:
            list_message["footer"] = footer_text
        if button_text:
            list_message["button_text"] = button_text
        success, msg = wa_send_interactive(target, "list", list_message=list_message)

    return {"success": success, "message": msg}


@mcp.tool()
def assign_operator(target: str, assignee_email: Optional[str] = None) -> Dict[str, Any]:
    """Assign an operator to a WhatsApp conversation.
    Pass no email (or null) to assign to the bot.

    Args:
        target: Phone number or conversation ID
        assignee_email: Operator's email address (null = assign to bot)
    """
    success = wa_assign_operator(target, assignee_email)
    return {"success": success}


@mcp.tool()
def update_conversation_status(target: str, new_status: str) -> Dict[str, Any]:
    """Update a conversation's status.

    Args:
        target: Phone number or conversation ID
        new_status: One of "open", "solved", "pending", "block"
    """
    if new_status not in ("open", "solved", "pending", "block"):
        return {"success": False, "message": "status must be open, solved, pending, or block"}
    success = wa_update_conversation_status(target, new_status)
    return {"success": success}


# ─── Templates ─────────────────────────────────────────────────────


@mcp.tool()
def list_templates(
    page_size: int = 20, page_number: int = 1
) -> List[Dict]:
    """List WhatsApp message templates.

    Args:
        page_size: Templates per page (max 100, default 20)
        page_number: Page number, 1-based (default 1)
    """
    return wa_list_templates(page_size, page_number)


@mcp.tool()
def get_template(template_id: str) -> Dict[str, Any]:
    """Get details of a specific message template.

    Args:
        template_id: The template's unique ID
    """
    result = wa_get_template(template_id)
    if result:
        return result
    return {"success": False, "message": "Template not found"}


@mcp.tool()
def send_template(
    template_name: str,
    broadcast_name: str,
    recipients: List[Dict[str, Any]],
    channel: Optional[str] = None,
) -> Dict[str, Any]:
    """Send template messages to one or more recipients.

    Args:
        template_name: Name of the approved template
        broadcast_name: Name for this broadcast batch
        recipients: List of {"phone_number": "...", "custom_params": [{"name": "k", "value": "v"}]}
        channel: Optional channel name or phone (null = default channel)
    """
    success, msg = wa_send_template(template_name, broadcast_name, recipients, channel)
    return {"success": success, "message": msg}


# ─── Campaigns ─────────────────────────────────────────────────────


@mcp.tool()
def list_campaigns(
    page_size: int = 20, page_number: int = 1
) -> List[Dict]:
    """List broadcast campaigns.

    Args:
        page_size: Campaigns per page (max 100, default 20)
        page_number: Page number, 1-based (default 1)
    """
    return wa_list_campaigns(page_size, page_number)


@mcp.tool()
def get_campaign(broadcast_id: str) -> Dict[str, Any]:
    """Get details and statistics for a broadcast campaign.

    Args:
        broadcast_id: The campaign's unique ID
    """
    result = wa_get_campaign(broadcast_id)
    if result:
        return result
    return {"success": False, "message": "Campaign not found"}


# ─── Channels ──────────────────────────────────────────────────────


@mcp.tool()
def list_channels(
    page_size: int = 20, page_number: int = 1
) -> List[Dict]:
    """List available WhatsApp channels.

    Args:
        page_size: Channels per page (max 100, default 20)
        page_number: Page number, 1-based (default 1)
    """
    return wa_list_channels(page_size, page_number)


# ─── Server ────────────────────────────────────────────────────────


def run_server():
    """Run the WhatsApp MCP Server."""
    mcp.run()


if __name__ == "__main__":
    run_server()
