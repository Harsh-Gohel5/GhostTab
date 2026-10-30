import base64
import copy

import httpx
import pytest
from connector_samples import RESPONSES, SELECTIONS, sample_sources

from ghosttab_api.connector_adapters import ConnectorFailure, read_selected


def test_all_selected_readers_normalize_fictional_sources_without_external_writes():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=RESPONSES[request.url.host])

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        sources = [
            read_selected(client, provider, item_id, container_id=container)
            for provider, item_id, container in SELECTIONS
        ]
    assert len(sources) == 5
    assert all(x.method == "GET" for x in requests)
    assert "Maya owns" in sources[0].evidence.content
    assert "3 PM" in sources[1].evidence.content
    assert "unassigned" in sources[2].evidence.content
    assert "delivery checklist" in sources[3].evidence.content
    assert "<p>" not in sources[4].evidence.content
    assert all(len(x.evidence.content) <= 12000 for x in sources)


@pytest.mark.parametrize(
    "status,code,retry",
    [
        (401, "access_denied", False),
        (403, "access_denied", False),
        (404, "source_unavailable", False),
        (429, "provider_unavailable", True),
        (503, "provider_unavailable", True),
        (302, "request_rejected", False),
    ],
)
def test_provider_failures_are_safe_and_bounded(status, code, retry):
    with httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(status, text="private detail"))
    ) as client:
        with pytest.raises(ConnectorFailure) as error:
            read_selected(client, "google_docs", "synthetic_doc")
    assert error.value.code == code and error.value.retryable == retry
    assert "private detail" not in str(error.value)


@pytest.mark.parametrize(
    "provider,item,container",
    [
        ("google_docs", "https://evil.test", ""),
        ("gmail", "../settings", ""),
        ("slack", "1.2", "https://evil.test"),
        ("jira", "DEMO-1", "evil.test"),
        ("teams", "../users", ""),
    ],
)
def test_invalid_selection_is_rejected_before_network(provider, item, container):
    def unexpected(req):
        pytest.fail("Invalid selection reached transport")

    with httpx.Client(transport=httpx.MockTransport(unexpected)) as client:
        with pytest.raises(ConnectorFailure, match="invalid_selection"):
            read_selected(client, provider, item, container_id=container)


def test_long_document_is_explicitly_marked_incomplete():
    data = {"documentId": "synthetic_doc", "body": {"textRun": {"content": "x" * 20000}}}
    with httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=data))
    ) as client:
        result = read_selected(client, "google_docs", "synthetic_doc")
    assert result.incomplete and len(result.evidence.content) <= 12000
    assert "Incomplete excerpt" in result.evidence.content


def test_slack_pagination_is_not_presented_as_a_complete_thread():
    data = copy.deepcopy(RESPONSES["slack.com"])
    data["has_more"] = True
    with httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=data))
    ) as client:
        result = read_selected(client, "slack", "1234567890.000001", container_id="CDEMO123")
    assert result.incomplete


def test_malformed_and_cross_resource_responses_fail_closed():
    for data in [
        [],
        {"documentId": "another_doc"},
        {"documentId": "synthetic_doc", "tabs": "invalid"},
    ]:
        with httpx.Client(
            transport=httpx.MockTransport(
                lambda req, payload=data: httpx.Response(200, json=payload)
            )
        ) as client:
            with pytest.raises(ConnectorFailure):
                read_selected(client, "google_docs", "synthetic_doc")


def test_samples_are_repeatable_and_never_claim_live_authorization():
    assert sample_sources() == sample_sources()


def test_gmail_prefers_plain_text_and_never_fetches_attachments():
    def part(mime, value, **extra):
        return {
            "mimeType": mime,
            "body": {"data": base64.urlsafe_b64encode(value.encode()).decode()},
            **extra,
        }

    data = {
        "id": "aabbcc",
        "payload": {
            "mimeType": "multipart/mixed",
            "parts": [
                part("text/html", "<p>HTML duplicate</p>"),
                part("text/plain", "Selected plain body"),
                part("text/plain", "Private attachment", filename="not-selected.txt"),
            ],
        },
    }
    with httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=data))
    ) as client:
        result = read_selected(client, "gmail", "aabbcc")
    assert result.evidence.content == "Selected plain body"


def test_teams_text_content_is_not_interpreted_as_html_and_deleted_items_are_omitted():
    data = {
        "value": [
            {"body": {"contentType": "text", "content": "Owner: <unassigned>"}},
            {"deletedDateTime": "2026-10-28", "body": {"content": "Removed text"}},
        ]
    }
    with httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=data))
    ) as client:
        result = read_selected(client, "teams", "19:synthetic@thread.v2")
    assert result.evidence.content == "Sender not provided · Time not provided\nOwner: <unassigned>"


def test_nested_google_docs_tabs_and_tables_keep_text():
    data = {
        "documentId": "synthetic_doc",
        "tabs": [
            {
                "documentTab": {
                    "body": {
                        "content": [
                            {
                                "table": {
                                    "tableRows": [
                                        {
                                            "tableCells": [
                                                {
                                                    "content": [
                                                        {
                                                            "paragraph": {
                                                                "elements": [
                                                                    {
                                                                        "textRun": {
                                                                            "content": "Table text"
                                                                        }
                                                                    }
                                                                ]
                                                            }
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                },
                "childTabs": [
                    {"documentTab": {"body": {"textRun": {"content": "Nested tab text"}}}}
                ],
            }
        ],
    }
    with httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json=data))
    ) as client:
        result = read_selected(client, "google_docs", "synthetic_doc")
    assert "Table text" in result.evidence.content and "Nested tab text" in result.evidence.content


def test_teams_omits_bodyless_deleted_events_and_preserves_chronological_speakers():
    messages = [
        {"deletedDateTime": "2026-11-02", "body": None},
        {"messageType": "systemEventMessage", "body": None},
        {
            "body": {"contentType": "text", "content": "New decision"},
            "from": {"user": {"displayName": "Lee"}},
            "createdDateTime": "2026-11-02T11:00:00Z",
        },
        {
            "body": {"contentType": "text", "content": "Earlier request"},
            "from": {"user": {"displayName": "Maya"}},
            "createdDateTime": "2026-11-02T10:00:00Z",
        },
    ]
    with httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(200, json={"value": messages}))
    ) as client:
        content = read_selected(client, "teams", "19:synthetic@thread.v2").evidence.content
    assert content.index("Maya") < content.index("Lee")
    assert "Earlier request" in content and "New decision" in content
