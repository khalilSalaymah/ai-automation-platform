"""Integration connectors for external services."""

from .base import BaseConnector
from .slack import SlackConnector
from .gmail import GmailConnector
from .outlook import OutlookConnector
from .notion import NotionConnector
from .stripe import StripeConnector
from .airtable import AirtableConnector
from .shopify import ShopifyConnector
from .google_calendar import GoogleCalendarConnector

__all__ = [
    "BaseConnector",
    "SlackConnector",
    "GmailConnector",
    "OutlookConnector",
    "NotionConnector",
    "StripeConnector",
    "AirtableConnector",
    "ShopifyConnector",
    "GoogleCalendarConnector",
]
