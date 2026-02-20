#!/usr/bin/env python3
"""
Test script for verifying the Wati API v3 integration.
Tests basic functionality of the Wati API wrapper against the v3 endpoints.
"""

import os
import logging
import json
import requests
from whatsapp_mcp.wati_api import wati_api

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("wati_test")


def analyze_response_structure(response):
    """Analyzes and prints the structure of an API response."""
    print("\nAnalyzing response structure:")

    if not isinstance(response, dict):
        print(f"Response is not a dictionary: {type(response)}")
        return

    print(f"Response top-level keys: {list(response.keys())}")

    for key in ["contact_list", "contacts", "message_list", "messages", "broadcasts", "channels"]:
        if key in response:
            data = response[key]
            if isinstance(data, list):
                print(f"{key} contains {len(data)} items")
                if data:
                    print(f"First item keys: {list(data[0].keys())}")
            else:
                print(f"{key} is not a list: {type(data)}")


def check_api_connection():
    """Verify basic API connectivity using v3 endpoint."""
    print("\nTesting basic API connectivity (v3)...")

    try:
        url = f"{wati_api.base_url}/api/ext/v3/contacts"
        headers = wati_api.headers

        print(f"Making test request to: {url}")
        response = requests.get(url, headers=headers, params={"page_size": 1, "page_number": 1})

        print(f"Response status code: {response.status_code}")

        try:
            response_json = response.json()
            print(f"Response JSON preview: {json.dumps(response_json)[:500]}...")
            analyze_response_structure(response_json)
        except json.JSONDecodeError:
            print(f"Response is not valid JSON: {response.text[:500]}")

        if response.status_code == 200:
            print("✅ API connection successful (v3)")
        else:
            print(f"❌ API connection failed with status code {response.status_code}")

    except Exception as e:
        print(f"❌ Exception when testing API connection: {str(e)}")


def test_get_contacts():
    """Test retrieving contacts from the Wati v3 API."""
    print("\nTesting get_contacts (v3)...")
    try:
        contacts = wati_api.get_contacts(page_size=5, page_number=1)
        if contacts:
            print(f"✅ Successfully retrieved {len(contacts)} contacts")
            for contact in contacts:
                print(f"  - {contact.name} ({contact.phone})")
        else:
            print("❌ Failed to retrieve contacts - empty result")

            # Diagnostic direct API call
            print("\nDiagnosing get_contacts API directly:")
            url = f"{wati_api.base_url}/api/ext/v3/contacts"
            response = requests.get(url, headers=wati_api.headers, params={"page_size": 5, "page_number": 1})

            if response.status_code == 200:
                try:
                    response_json = response.json()
                    analyze_response_structure(response_json)
                except json.JSONDecodeError:
                    print(f"Response is not valid JSON: {response.text[:500]}")
            else:
                print(f"Direct API call failed with status {response.status_code}")

    except Exception as e:
        print(f"❌ Exception when getting contacts: {str(e)}")


def test_get_contact():
    """Test getting a single contact by phone/ID."""
    print("\nTesting get_contact (v3)...")
    try:
        contacts = wati_api.get_contacts(page_size=1, page_number=1)
        if not contacts:
            print("❌ No contacts found to test with")
            return

        contact = contacts[0]
        target = contact.phone or contact.wa_id or contact.id
        print(f"Fetching contact by target: {target}")

        result = wati_api.get_contact(target)
        if result:
            print(f"✅ Got contact: {result.name} ({result.phone})")
        else:
            print("❌ Failed to get contact")

    except Exception as e:
        print(f"❌ Exception when getting contact: {str(e)}")


def test_get_messages():
    """Test retrieving messages from the Wati v3 API."""
    print("\nTesting get_messages (v3)...")

    try:
        contacts = wati_api.get_contacts(page_size=1, page_number=1)
        if not contacts:
            print("❌ No contacts found to test messages with")
            return

        contact = contacts[0]
        target = contact.phone or contact.wa_id
        print(f"Using contact: {contact.name} ({target})")

        messages = wati_api.get_messages(target, page_size=5, page_number=1)
        if messages:
            print(f"✅ Successfully retrieved {len(messages)} messages")
            for msg in messages:
                text = msg.text if len(msg.text) <= 50 else msg.text[:47] + "..."
                sender = "You" if msg.owner else contact.name
                print(f"  - [{msg.timestamp}] {sender}: {text}")
        else:
            print("❌ Failed to retrieve messages - empty result")
    except Exception as e:
        print(f"❌ Exception when getting messages: {str(e)}")


def test_send_message():
    """Test sending a message via the Wati v3 API (dry run)."""
    print("\nTesting send_message endpoint construction (v3, no actual send)...")

    try:
        contacts = wati_api.get_contacts(page_size=1, page_number=1)
        if not contacts:
            print("❌ No contacts found to test with")
            return

        contact = contacts[0]
        target = contact.phone or contact.wa_id
        print(f"Would send message to: {contact.name} ({target})")

        url = f"{wati_api.base_url}/api/ext/v3/conversations/messages/text"
        print(f"Would call API endpoint: {url}")
        print(f"With body: {{\"target\": \"{target}\", \"text\": \"test\"}}")
        print("✅ API endpoint construction successful")

    except Exception as e:
        print(f"❌ Exception when testing send_message: {str(e)}")


def test_list_templates():
    """Test listing message templates."""
    print("\nTesting list_templates (v3)...")
    try:
        templates = wati_api.list_templates(page_size=5, page_number=1)
        if templates:
            print(f"✅ Retrieved {len(templates)} templates")
            for t in templates[:3]:
                print(f"  - {t.get('name', t.get('id', 'unknown'))}")
        else:
            print("ℹ️  No templates found (this may be normal)")
    except Exception as e:
        print(f"❌ Exception when listing templates: {str(e)}")


def test_list_channels():
    """Test listing channels."""
    print("\nTesting list_channels (v3)...")
    try:
        channels = wati_api.list_channels(page_size=10, page_number=1)
        if channels:
            print(f"✅ Retrieved {len(channels)} channels")
            for ch in channels:
                print(f"  - {ch.get('name', 'unnamed')} ({ch.get('channel', '')})")
        else:
            print("ℹ️  No additional channels found (default channel excluded)")
    except Exception as e:
        print(f"❌ Exception when listing channels: {str(e)}")


def test_list_campaigns():
    """Test listing campaigns."""
    print("\nTesting list_campaigns (v3)...")
    try:
        campaigns = wati_api.list_campaigns(page_size=5, page_number=1)
        if campaigns:
            print(f"✅ Retrieved {len(campaigns)} campaigns")
        else:
            print("ℹ️  No campaigns found (this may be normal)")
    except Exception as e:
        print(f"❌ Exception when listing campaigns: {str(e)}")


def check_env_vars():
    """Check if environment variables are set correctly."""
    print("\nChecking environment variables...")

    api_url = os.environ.get("WATI_API_BASE_URL")
    tenant_id = os.environ.get("WATI_TENANT_ID")
    auth_token = os.environ.get("WATI_AUTH_TOKEN")

    missing_vars = []
    if not api_url:
        missing_vars.append("WATI_API_BASE_URL")
    if not auth_token:
        missing_vars.append("WATI_AUTH_TOKEN")

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please make sure these are set in the .env file.")
        return False

    if tenant_id:
        print(f"ℹ️  WATI_TENANT_ID is set: {tenant_id} (used for multi-channel targeting)")
    else:
        print("ℹ️  WATI_TENANT_ID not set (optional in v3, tenant resolved from Bearer token)")

    print("✅ All required environment variables are set")
    return True


def main():
    """Run all tests."""
    print("=== Wati API v3 Integration Test ===")
    print(f"API Base URL: {os.environ.get('WATI_API_BASE_URL', 'Not set')}")
    print(f"Tenant ID: {os.environ.get('WATI_TENANT_ID', 'Not set (optional)')}")
    print(f"Auth Token: {'Set' if os.environ.get('WATI_AUTH_TOKEN') else 'Not set'}")
    print("====================================")

    if not check_env_vars():
        print("\n❌ Environment variable check failed. Exiting tests.")
        return

    check_api_connection()

    test_get_contacts()
    test_get_contact()
    test_get_messages()
    test_send_message()
    test_list_templates()
    test_list_channels()
    test_list_campaigns()

    print("\n=== Test Summary ===")
    print("Please check the logs above for detailed information.")
    print("If you're seeing errors, verify:")
    print("1. Your API credentials in the .env file")
    print("2. The API base URL is correct (e.g. https://live-mt-server.wati.io)")
    print("3. Your Wati account is active and properly configured")
    print("4. Your network can reach the Wati API servers")


if __name__ == "__main__":
    main()
