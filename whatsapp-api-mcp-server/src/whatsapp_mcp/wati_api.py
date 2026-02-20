import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("wati_api")

# Load environment variables from .env file
env_paths = [
    Path(__file__).resolve().parent / '.env',
    Path(__file__).resolve().parent.parent.parent / '.env',
]

for env_path in env_paths:
    if env_path.exists():
        logger.info(f"Loading .env from {env_path}")
        load_dotenv(dotenv_path=env_path)
        break

# Configuration
WATI_API_BASE_URL = os.environ.get("WATI_API_BASE_URL", "https://live-mt-server.wati.io")
WATI_TENANT_ID = os.environ.get("WATI_TENANT_ID", "")  # Optional in v3
WATI_AUTH_TOKEN = os.environ.get("WATI_AUTH_TOKEN", "your-auth-token")

logger.info(f"Initialized with API URL: {WATI_API_BASE_URL}")


# Data models
@dataclass
class Contact:
    """WhatsApp contact data model (v3 API)."""
    phone: str
    name: Optional[str] = None
    id: Optional[str] = None
    wa_id: Optional[str] = None
    photo: Optional[str] = None
    created: Optional[str] = None
    last_updated: Optional[str] = None
    contact_status: Optional[str] = None
    source: Optional[str] = None
    channel_id: Optional[str] = None
    opted_in: Optional[bool] = None
    allow_broadcast: Optional[bool] = None
    allow_sms: Optional[bool] = None
    teams: Optional[List[str]] = None
    segments: Optional[List[str]] = None
    custom_params: Optional[List[Dict[str, str]]] = None
    channel_type: Optional[str] = None
    display_name: Optional[str] = None


@dataclass
class Message:
    """WhatsApp message data model (v3 API)."""
    id: str
    text: str
    timestamp: datetime
    owner: bool
    type: Optional[str] = None
    status: Optional[str] = None
    assigned_id: Optional[str] = None
    operator_name: Optional[str] = None
    conversation_id: Optional[str] = None
    event_type: Optional[str] = None
    local_message_id: Optional[str] = None


class WatiAPI:
    """Wrapper for the Wati WhatsApp API v3."""

    def __init__(
        self,
        base_url: str = WATI_API_BASE_URL,
        tenant_id: str = WATI_TENANT_ID,
        auth_token: str = WATI_AUTH_TOKEN,
    ):
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        logger.info(f"WatiAPI v3 initialized with base_url={base_url}")

    # ─── HTTP helpers ──────────────────────────────────────────────

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict:
        """Make a JSON API request to the Wati v3 API.

        The endpoint should already include the full path, e.g.
        ``api/ext/v3/contacts``.  The tenant_id is no longer embedded
        in the URL for v3; the token resolves the tenant.
        """
        url = f"{self.base_url}/{endpoint}"
        logger.debug(f"Making {method} request to {url}")
        logger.debug(f"Params: {params}")
        logger.debug(f"Data: {data}")

        try:
            m = method.upper()
            if m == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif m == "POST":
                response = requests.post(url, headers=self.headers, params=params, json=data)
            elif m == "PUT":
                response = requests.put(url, headers=self.headers, params=params, json=data)
            elif m == "PATCH":
                response = requests.patch(url, headers=self.headers, params=params, json=data)
            elif m == "DELETE":
                response = requests.delete(url, headers=self.headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            logger.debug(f"Response status: {response.status_code}")
            try:
                logger.debug(f"Response body: {response.text[:500]}")
            except Exception:
                pass

            response.raise_for_status()

            try:
                return response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return {"success": False, "error": f"Invalid JSON: {response.text}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}

    def _make_multipart_request(
        self,
        endpoint: str,
        files: Dict,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """Make a multipart/form-data request (for file uploads)."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Authorization": self.headers["Authorization"]}
        logger.debug(f"Multipart POST to {url}")

        try:
            response = requests.post(url, headers=headers, files=files, data=data, params=params)
            logger.debug(f"Response status: {response.status_code}")
            response.raise_for_status()
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"success": False, "error": f"Invalid JSON: {response.text}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Multipart request error: {e}")
            return {"success": False, "error": str(e)}

    def _build_target(self, phone_or_target: str) -> str:
        """Build a v3 target string.

        If ``WATI_TENANT_ID`` (channel) is configured and the input
        looks like a plain phone number, prefix with
        ``channel:phone``.  Otherwise pass through as-is.
        """
        if self.tenant_id and ":" not in phone_or_target:
            return f"{self.tenant_id}:{phone_or_target}"
        return phone_or_target

    # ─── Contacts ──────────────────────────────────────────────────

    def get_contacts(
        self,
        page_size: int = 20,
        page_number: int = 1,
        channel: Optional[str] = None,
    ) -> List[Contact]:
        """List contacts (v3 ``GET /api/ext/v3/contacts``)."""
        params: Dict[str, Any] = {
            "page_size": page_size,
            "page_number": page_number,
        }
        if channel:
            params["channel"] = channel

        response = self._make_request("GET", "api/ext/v3/contacts", params=params)
        return self._parse_contacts(response)

    def search_contacts(self, query: str) -> List[Contact]:
        """Search contacts by listing and filtering client-side.

        The v3 API does not have a dedicated search param on GET /contacts,
        so we pull a page and filter by name/phone containing the query.
        """
        contacts = self.get_contacts(page_size=100, page_number=1)
        q = query.lower()
        return [
            c for c in contacts
            if (c.name and q in c.name.lower())
            or (c.phone and q in c.phone)
            or (c.wa_id and q in c.wa_id)
        ]

    def get_contact(self, target: str) -> Optional[Contact]:
        """Get a single contact (v3 ``GET /api/ext/v3/contacts/{target}``)."""
        response = self._make_request("GET", f"api/ext/v3/contacts/{target}")
        if isinstance(response, dict) and "error" not in response:
            return self._parse_contact(response)
        return None

    def add_contact(
        self,
        whatsapp_number: str,
        name: str,
        custom_params: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[Contact]:
        """Add a new contact (v3 ``POST /api/ext/v3/contacts``)."""
        data: Dict[str, Any] = {
            "whatsapp_number": whatsapp_number,
            "name": name,
        }
        if custom_params:
            data["custom_params"] = custom_params

        response = self._make_request("POST", "api/ext/v3/contacts", data=data)
        if isinstance(response, dict) and "error" not in response:
            return self._parse_contact(response)
        return None

    def update_contacts(
        self, contacts: List[Dict[str, Any]]
    ) -> List[Contact]:
        """Bulk-update contacts (v3 ``PUT /api/ext/v3/contacts``).

        Each entry should have ``target`` and ``customParams``.
        """
        data = {"contacts": contacts}
        response = self._make_request("PUT", "api/ext/v3/contacts", data=data)
        if isinstance(response, dict):
            return self._parse_contacts(response)
        return []

    def get_contact_count(self) -> int:
        """Get total contact count (v3 ``GET /api/ext/v3/contacts/count``)."""
        response = self._make_request("GET", "api/ext/v3/contacts/count")
        if isinstance(response, dict):
            return response.get("count", 0)
        return 0

    def assign_contact_teams(self, target: str, teams: List[str]) -> bool:
        """Assign a contact to teams (v3 ``PUT /api/ext/v3/contacts/teams``)."""
        data = {"target": target, "teams": teams}
        response = self._make_request("PUT", "api/ext/v3/contacts/teams", data=data)
        return bool(response.get("result", False)) if isinstance(response, dict) else False

    # ─── Conversations / Messages ──────────────────────────────────

    def get_messages(
        self,
        target: str,
        page_size: int = 20,
        page_number: int = 1,
    ) -> List[Message]:
        """Get conversation messages (v3 ``GET /api/ext/v3/conversations/{target}/messages``)."""
        params = {"page_size": page_size, "page_number": page_number}
        response = self._make_request(
            "GET", f"api/ext/v3/conversations/{target}/messages", params=params
        )
        return self._parse_messages(response)

    def send_message(self, target: str, text: str) -> Tuple[bool, str]:
        """Send a text message (v3 ``POST /api/ext/v3/conversations/messages/text``)."""
        data = {"target": target, "text": text}
        response = self._make_request("POST", "api/ext/v3/conversations/messages/text", data=data)
        return self._parse_send_response(response)

    def send_file(
        self, target: str, file_path: str, caption: str = ""
    ) -> Tuple[bool, str]:
        """Send a file via multipart upload (v3 ``POST /api/ext/v3/conversations/messages/file``)."""
        import mimetypes as mt

        is_url = file_path.startswith(("http://", "https://"))
        temp_file = None

        try:
            actual_path = file_path
            if is_url:
                import tempfile
                import urllib.request

                ext = os.path.splitext(file_path.split("?")[0])[1] or ".tmp"
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                temp_file.close()
                urllib.request.urlretrieve(file_path, temp_file.name)
                actual_path = temp_file.name

            content_type = mt.guess_type(actual_path)[0] or "application/octet-stream"

            with open(actual_path, "rb") as f:
                files = {"file": (os.path.basename(actual_path), f, content_type)}
                form_data = {"target": target}
                if caption:
                    form_data["caption"] = caption

                response = self._make_multipart_request(
                    "api/ext/v3/conversations/messages/file",
                    files=files,
                    data=form_data,
                )

            return self._parse_send_response(response)
        except Exception as e:
            logger.error(f"Error sending file: {e}")
            return False, f"Error sending file: {e}"
        finally:
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def send_file_via_url(
        self, target: str, file_url: str, caption: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Send a file by URL (v3 ``POST /api/ext/v3/conversations/messages/fileViaUrl``)."""
        data: Dict[str, Any] = {"target": target, "file_url": file_url}
        if caption:
            data["caption"] = caption
        response = self._make_request(
            "POST", "api/ext/v3/conversations/messages/fileViaUrl", data=data
        )
        return self._parse_send_response(response)

    def download_media(self, message_id: str) -> Optional[str]:
        """Download media by message ID (v3 ``GET /api/ext/v3/conversations/messages/file/{message_id}``)."""
        url = f"{self.base_url}/api/ext/v3/conversations/messages/file/{message_id}"
        try:
            response = requests.get(url, headers=self.headers, stream=True)
            if response.status_code == 200:
                os.makedirs("downloads", exist_ok=True)

                # Try to get filename from Content-Disposition
                cd = response.headers.get("Content-Disposition", "")
                if "filename=" in cd:
                    filename = cd.split("filename=")[-1].strip('"')
                else:
                    filename = message_id

                local_path = os.path.join("downloads", filename)
                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                return local_path
            else:
                logger.error(f"Download failed: HTTP {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None

    def send_interactive(
        self,
        target: str,
        interactive_type: str,
        button_message: Optional[Dict] = None,
        list_message: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """Send an interactive message (v3 ``POST /api/ext/v3/conversations/messages/interactive``).

        ``interactive_type`` must be ``"buttons"`` or ``"list"``.
        """
        data: Dict[str, Any] = {"target": target, "type": interactive_type}
        if interactive_type == "buttons" and button_message:
            data["button_message"] = button_message
        elif interactive_type == "list" and list_message:
            data["list_message"] = list_message

        response = self._make_request(
            "POST", "api/ext/v3/conversations/messages/interactive", data=data
        )
        return self._parse_send_response(response)

    def assign_operator(self, target: str, assignee_email: Optional[str] = None) -> bool:
        """Assign an operator to a conversation (v3 ``PUT /api/ext/v3/conversations/{target}/operator``)."""
        data: Dict[str, Any] = {"assignee_email": assignee_email}
        response = self._make_request(
            "PUT", f"api/ext/v3/conversations/{target}/operator", data=data
        )
        return bool(response.get("result", False)) if isinstance(response, dict) else False

    def update_conversation_status(self, target: str, new_status: str) -> bool:
        """Update conversation status (v3 ``PUT /api/ext/v3/conversations/{target}/status``).

        ``new_status`` must be one of: ``open``, ``solved``, ``pending``, ``block``.
        """
        data = {"new_status": new_status}
        response = self._make_request(
            "PUT", f"api/ext/v3/conversations/{target}/status", data=data
        )
        return bool(response.get("result", False)) if isinstance(response, dict) else False

    # ─── Templates ─────────────────────────────────────────────────

    def list_templates(
        self, page_size: int = 20, page_number: int = 1
    ) -> List[Dict]:
        """List message templates (v3 ``GET /api/ext/v3/messageTemplates``)."""
        params = {"page_size": page_size, "page_number": page_number}
        response = self._make_request("GET", "api/ext/v3/messageTemplates", params=params)
        if isinstance(response, dict):
            return response.get("message_templates", response.get("templates", []))
        return []

    def get_template(self, template_id: str) -> Optional[Dict]:
        """Get a template by ID (v3 ``GET /api/ext/v3/messageTemplates/{template_id}``)."""
        response = self._make_request("GET", f"api/ext/v3/messageTemplates/{template_id}")
        if isinstance(response, dict) and "error" not in response:
            return response
        return None

    def send_template(
        self,
        template_name: str,
        broadcast_name: str,
        recipients: List[Dict[str, Any]],
        channel: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Send template messages (v3 ``POST /api/ext/v3/messageTemplates/send``)."""
        data: Dict[str, Any] = {
            "template_name": template_name,
            "broadcast_name": broadcast_name,
            "recipients": recipients,
        }
        if channel:
            data["channel"] = channel

        response = self._make_request("POST", "api/ext/v3/messageTemplates/send", data=data)
        if isinstance(response, dict):
            success = response.get("success", False)
            broadcast_id = response.get("broadcast_id", "")
            msg = f"Broadcast {broadcast_id}" if success else response.get("error", "Unknown error")
            return success, msg
        return False, "Invalid response"

    # ─── Campaigns ─────────────────────────────────────────────────

    def list_campaigns(
        self, page_size: int = 20, page_number: int = 1, channel: Optional[str] = None
    ) -> List[Dict]:
        """List broadcast campaigns (v3 ``GET /api/ext/v3/broadcasts``)."""
        params: Dict[str, Any] = {"page_size": page_size, "page_number": page_number}
        if channel:
            params["channel"] = channel
        response = self._make_request("GET", "api/ext/v3/broadcasts", params=params)
        if isinstance(response, dict):
            return response.get("broadcasts", [])
        return []

    def get_campaign(self, broadcast_id: str) -> Optional[Dict]:
        """Get campaign details (v3 ``GET /api/ext/v3/broadcasts/{broadcast_id}``)."""
        response = self._make_request("GET", f"api/ext/v3/broadcasts/{broadcast_id}")
        if isinstance(response, dict) and "error" not in response:
            return response
        return None

    # ─── Channels ──────────────────────────────────────────────────

    def list_channels(
        self, page_size: int = 20, page_number: int = 1
    ) -> List[Dict]:
        """List WhatsApp channels (v3 ``GET /api/ext/v3/channels``)."""
        params = {"page_size": page_size, "page_number": page_number}
        response = self._make_request("GET", "api/ext/v3/channels", params=params)
        if isinstance(response, dict):
            return response.get("channels", [])
        return []

    # ─── Response parsing helpers ──────────────────────────────────

    def _parse_contacts(self, response: Any) -> List[Contact]:
        """Parse a contact list response."""
        contacts = []
        if not isinstance(response, dict):
            return contacts

        contact_list = response.get("contact_list", response.get("contacts", []))
        if not isinstance(contact_list, list):
            return contacts

        for item in contact_list:
            try:
                contacts.append(self._parse_contact(item))
            except Exception as e:
                logger.warning(f"Error parsing contact: {e}")
        return contacts

    def _parse_contact(self, data: Dict) -> Contact:
        """Parse a single contact dict into a Contact dataclass."""
        return Contact(
            phone=data.get("phone", ""),
            name=data.get("name", ""),
            id=data.get("id", ""),
            wa_id=data.get("wa_id", ""),
            photo=data.get("photo"),
            created=data.get("created"),
            last_updated=data.get("last_updated"),
            contact_status=data.get("contact_status"),
            source=data.get("source"),
            channel_id=data.get("channel_id"),
            opted_in=data.get("opted_in"),
            allow_broadcast=data.get("allow_broadcast"),
            allow_sms=data.get("allow_sms"),
            teams=data.get("teams"),
            segments=data.get("segments"),
            custom_params=data.get("custom_params"),
            channel_type=data.get("channel_type"),
            display_name=data.get("display_name"),
        )

    def _parse_messages(self, response: Any) -> List[Message]:
        """Parse a messages list response."""
        messages = []
        if not isinstance(response, dict):
            return messages

        message_list = response.get("message_list", response.get("messages", []))
        if not isinstance(message_list, list):
            return messages

        for item in message_list:
            try:
                messages.append(self._parse_message(item))
            except Exception as e:
                logger.warning(f"Error parsing message: {e}")
        return messages

    def _parse_message(self, data: Dict) -> Message:
        """Parse a single message dict into a Message dataclass."""
        # Parse timestamp
        timestamp = datetime.now()
        ts_raw = data.get("created") or data.get("timestamp")
        if ts_raw:
            try:
                if isinstance(ts_raw, str):
                    if "T" in ts_raw:
                        timestamp = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                    else:
                        timestamp = datetime.strptime(ts_raw, "%Y-%m-%d %H:%M:%S")
                elif isinstance(ts_raw, (int, float)):
                    timestamp = datetime.fromtimestamp(ts_raw)
            except (ValueError, TypeError):
                pass

        return Message(
            id=data.get("id", ""),
            text=data.get("text", ""),
            timestamp=timestamp,
            owner=data.get("owner", False),
            type=data.get("type"),
            status=data.get("status"),
            assigned_id=data.get("assigned_id"),
            operator_name=data.get("operator_name"),
            conversation_id=data.get("conversation_id"),
            event_type=data.get("event_type"),
            local_message_id=data.get("local_message_id"),
        )

    def _parse_send_response(self, response: Any) -> Tuple[bool, str]:
        """Parse a send-action response into (success, message)."""
        if not isinstance(response, dict):
            return False, "Invalid response"

        if "error" in response and response["error"]:
            return False, str(response["error"])

        # v3 send responses return ``{"message": {...}}`` on success
        if "message" in response and isinstance(response["message"], dict):
            msg_id = response["message"].get("id", "")
            return True, f"Message sent (id: {msg_id})"

        # Fallback for other response shapes
        if response.get("success") is True:
            return True, response.get("broadcast_id", "Success")
        if response.get("result") is True:
            return True, "Success"

        return False, response.get("message", response.get("error", "Unknown response"))


# Create a global API instance
wati_api = WatiAPI()
