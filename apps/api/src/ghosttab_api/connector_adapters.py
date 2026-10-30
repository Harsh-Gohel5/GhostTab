"""Selected-item readers; OAuth, resource grants and live wiring are still pending.

The caller must supply a server-owned, authorized client after checking ownership
and the resource grant. A normalized source is data, never proof of authorization.
No credentials, arbitrary URLs, model calls or external writes are accepted here.
"""

import base64
import binascii
import re
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import quote
from uuid import UUID

import httpx

from ghosttab_api.contracts import EvidenceInput


class ConnectorFailure(Exception):
    def __init__(self, code, *, retryable=False):
        self.code, self.retryable = code, retryable
        super().__init__(code)


@dataclass(frozen=True)
class RetrievedSource:
    provider: str
    external_id: str
    evidence: EvidenceInput
    incomplete: bool = False


class BoundedRead:
    def __init__(self, client):
        self.client = client
        self.deadline = time.monotonic() + 20

    def get(self, url, **kwargs):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise httpx.TimeoutException("Source read deadline reached")
        kwargs["timeout"] = min(remaining, kwargs.get("timeout", 20))
        return self.client.get(url, **kwargs)


def identifier(value, pattern=r"[A-Za-z0-9_-]+"):
    if not isinstance(value, str) or len(value) > 256 or not re.fullmatch(pattern, value):
        raise ConnectorFailure("invalid_selection")
    return value


def request(client, url, *, request_timeout=20, **params):
    try:
        response = client.get(url, params=params, timeout=request_timeout, follow_redirects=False)
        if response.status_code == 403 and response.request.url.host in (
            "docs.googleapis.com",
            "gmail.googleapis.com",
        ):
            try:
                reasons = {
                    x.get("reason") for x in response.json().get("error", {}).get("errors", [])
                }
            except (ValueError, AttributeError, TypeError):
                reasons = set()
            if reasons & {
                "rateLimitExceeded",
                "userRateLimitExceeded",
                "quotaExceeded",
                "dailyLimitExceeded",
            }:
                raise ConnectorFailure("provider_unavailable", retryable=True)
            if reasons & {"accessNotConfigured", "serviceDisabled"}:
                raise ConnectorFailure("provider_setup_required")
        if response.status_code == 401 and response.request.url.host in (
            "api.atlassian.com",
            "graph.microsoft.com",
        ):
            raise ConnectorFailure("connection_revoked")
        if response.status_code in (401, 403):
            raise ConnectorFailure("access_denied")
        if response.status_code in (404, 410):
            raise ConnectorFailure("source_unavailable")
        if response.status_code == 429 or response.status_code >= 500:
            raise ConnectorFailure("provider_unavailable", retryable=True)
        if not response.is_success:
            raise ConnectorFailure("request_rejected")
        if len(response.content) > 2_000_000:
            raise ConnectorFailure("response_too_large")
        data = response.json()
        if not isinstance(data, dict):
            raise ConnectorFailure("invalid_response")
        return data
    except httpx.HTTPError as exc:
        raise ConnectorFailure("provider_unavailable", retryable=True) from exc
    except ValueError as exc:
        raise ConnectorFailure("invalid_response") from exc


def structured_text(node, *, docs=False, depth=0):
    if depth > 30:
        raise ConnectorFailure("response_too_complex")
    if isinstance(node, list):
        return "".join(structured_text(x, docs=docs, depth=depth + 1) for x in node)
    if not isinstance(node, dict):
        return ""
    if docs and isinstance(node.get("textRun"), dict):
        return str(node["textRun"].get("content", ""))
    if not docs and node.get("type") == "text":
        return str(node.get("text", ""))
    return "\n".join(
        structured_text(value, docs=docs, depth=depth + 1)
        for value in node.values()
        if isinstance(value, (dict, list))
    )


class HtmlText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if tag in ("br", "p", "div", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def html_text(value):
    parser = HtmlText()
    parser.feed(value)
    return "".join(parser.parts).strip()


def mail_parts(part, depth=0):
    if depth > 12:
        raise ConnectorFailure("response_too_complex")
    if part.get("filename"):
        return []  # Attachments are outside selected-message text retrieval.
    result = []
    mime = part.get("mimeType", "")
    if mime in ("text/plain", "text/html") and (encoded := part.get("body", {}).get("data")):
        try:
            text = base64.b64decode(
                encoded + "=" * (-len(encoded) % 4), altchars=b"-_", validate=True
            ).decode("utf-8", errors="replace")
        except (ValueError, binascii.Error) as exc:
            raise ConnectorFailure("invalid_response") from exc
        result.append((mime, text))
    for child in part.get("parts", []):
        result.extend(mail_parts(child, depth + 1))
    return result


def source(provider, item_id, title, content, url, incomplete=False):
    content = content.strip()
    if not content:
        raise ConnectorFailure("source_empty")
    if len(content) > 12000:
        incomplete = True
    if incomplete:
        content = content[:11900] + "\n[Incomplete excerpt: additional source content was omitted.]"
    return RetrievedSource(
        provider,
        item_id,
        EvidenceInput(
            title=(title or "Untitled source")[:200],
            content=content,
            url=url,
        ),
        incomplete,
    )


def read_selected(client, provider, item_id, *, container_id=""):
    try:
        return _read_selected(client, provider, item_id, container_id=container_id)
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise ConnectorFailure("invalid_response") from exc


def _read_selected(client, provider, item_id, *, container_id=""):
    """Read one explicit selection. Not exposed as an application route yet."""
    if provider == "google_docs":
        identifier(item_id)
        data = request(
            client, f"https://docs.googleapis.com/v1/documents/{item_id}", includeTabsContent="true"
        )
        if data.get("documentId") != item_id:
            raise ConnectorFailure("invalid_response")
        content = structured_text(data.get("tabs") or data.get("body", {}), docs=True)
        return source(
            provider,
            item_id,
            data.get("title", ""),
            content,
            f"https://docs.google.com/document/d/{item_id}/edit",
        )
    if provider == "gmail":
        identifier(item_id, r"[a-fA-F0-9]+")
        data = request(
            client,
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{item_id}",
            format="full",
        )
        if data.get("id") != item_id:
            raise ConnectorFailure("invalid_response")
        payload = data.get("payload", {})
        headers = {x["name"].lower(): x.get("value", "") for x in payload.get("headers", [])}
        parts = mail_parts(payload)
        plain = [text for mime, text in parts if mime == "text/plain"]
        body = "\n".join(plain) if plain else "\n".join(html_text(text) for _, text in parts)
        return source(
            provider,
            item_id,
            headers.get("subject", "Email message"),
            body,
            f"https://mail.google.com/mail/u/0/#all/{item_id}",
        )
    if provider == "slack":
        identifier(container_id, r"[CGD][A-Z0-9]+")
        identifier(item_id, r"[0-9]+\.[0-9]+")
        data = request(
            client,
            "https://slack.com/api/conversations.replies",
            channel=container_id,
            ts=item_id,
            limit=15,
        )
        if data.get("ok") is not True:
            if data.get("error") in (
                "invalid_auth",
                "token_revoked",
                "account_inactive",
                "not_authed",
            ):
                raise ConnectorFailure("connection_revoked")
            if data.get("error") in ("channel_not_found", "message_not_found", "thread_not_found"):
                raise ConnectorFailure("source_unavailable")
            code = "provider_unavailable" if data.get("error") == "ratelimited" else "access_denied"
            raise ConnectorFailure(code, retryable=code == "provider_unavailable")
        messages = data.get("messages", [])
        if not messages or messages[0].get("ts") != item_id:
            raise ConnectorFailure("source_unavailable")
        content = "\n\n".join(str(x.get("text", "")) for x in messages)
        return source(
            provider,
            f"{container_id}:{item_id}",
            "Selected Slack thread",
            content,
            f"https://slack.com/app_redirect?channel={container_id}",
            bool(data.get("has_more") or data.get("response_metadata", {}).get("next_cursor")),
        )
    if provider == "jira":
        identifier(item_id, r"[A-Z][A-Z0-9_]*-[0-9]+")
        try:
            cloud_id = str(UUID(container_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ConnectorFailure("invalid_selection") from exc
        data = request(
            client,
            f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/issue/{item_id}",
            fields="summary,description,status,updated",
        )
        if data.get("key") != item_id:
            raise ConnectorFailure("invalid_response")
        fields = data.get("fields", {})
        content = f"Issue: {item_id}\nStatus: {fields.get('status', {}).get('name', 'Unknown')}\n"
        content += structured_text(fields.get("description", {}))
        return source(provider, item_id, fields.get("summary", item_id), content, "")
    if provider == "teams":
        identifier(item_id, r"19:[A-Za-z0-9_.@-]+")
        encoded = quote(item_id, safe="")
        data = request(
            client,
            f"https://graph.microsoft.com/v1.0/me/chats/{encoded}/messages",
            **{"$top": 50, "$orderby": "createdDateTime desc"},
        )
        messages = data.get("value")
        if not isinstance(messages, list) or len(messages) > 50:
            raise ConnectorFailure("invalid_response")
        parts = []
        for message in reversed(messages):
            if not isinstance(message, dict):
                raise ConnectorFailure("invalid_response")
            if message.get("deletedDateTime") or message.get("messageType", "message") != "message":
                continue
            if not isinstance(message.get("body"), dict):
                raise ConnectorFailure("invalid_response")
            body = message["body"]
            if body.get("contentType") not in ("text", "html") or not isinstance(
                body.get("content"), str
            ):
                raise ConnectorFailure("invalid_response")
            text = html_text(body["content"]) if body["contentType"] == "html" else body["content"]
            sender = message.get("from") or {}
            if not isinstance(sender, dict):
                raise ConnectorFailure("invalid_response")
            identity = sender.get("user") or sender.get("application") or {}
            if not isinstance(identity, dict):
                raise ConnectorFailure("invalid_response")
            name = identity.get("displayName") or "Sender not provided"
            stamp = message.get("createdDateTime") or "Time not provided"
            if not isinstance(name, str) or not isinstance(stamp, str):
                raise ConnectorFailure("invalid_response")
            if text.strip():
                parts.append(f"{name[:200]} · {stamp[:100]}\n{text}")
        content = "\n\n".join(parts)
        return source(
            provider,
            item_id,
            "Selected Teams chat",
            content,
            f"https://teams.microsoft.com/l/chat/{encoded}/conversations",
            bool(data.get("@odata.nextLink")),
        )
    raise ConnectorFailure("unsupported_provider")
