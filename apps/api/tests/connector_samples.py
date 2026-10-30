"""Fictional provider responses and a fake model. Never contacts a live service."""

import base64
import json

import httpx

from ghosttab_api.connector_adapters import read_selected
from ghosttab_api.meta import ModelResult

SELECTIONS = [
    ("google_docs", "synthetic_doc", ""),
    ("gmail", "aabbcc", ""),
    ("slack", "1234567890.000001", "CDEMO123"),
    ("jira", "DEMO-1", "11111111-1111-4111-8111-111111111111"),
    ("teams", "19:synthetic@thread.v2", ""),
]

RESPONSES = {
    "docs.googleapis.com": {
        "documentId": "synthetic_doc",
        "title": "Fictional launch brief",
        "tabs": [
            {
                "documentTab": {
                    "body": {
                        "content": [
                            {
                                "paragraph": {
                                    "elements": [
                                        {
                                            "textRun": {
                                                "content": "Maya owns the launch checklist.\n"
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        ],
    },
    "gmail.googleapis.com": {
        "id": "aabbcc",
        "payload": {
            "mimeType": "text/plain",
            "headers": [{"name": "Subject", "value": "Fictional approval request"}],
            "body": {
                "data": base64.urlsafe_b64encode(
                    b"Lee must approve the plan by Thursday at 3 PM."
                ).decode()
            },
        },
    },
    "slack.com": {
        "ok": True,
        "messages": [{"ts": "1234567890.000001", "text": "The support contact is unassigned."}],
    },
    "api.atlassian.com": {
        "key": "DEMO-1",
        "fields": {
            "summary": "Fictional delivery checklist",
            "status": {"name": "In progress"},
            "description": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "Review the delivery checklist before launch."}
                        ],
                    }
                ],
            },
        },
    },
    "graph.microsoft.com": {
        "value": [
            {
                "body": {
                    "contentType": "html",
                    "content": "<p>Confirm handoff ownership before the meeting.</p>",
                }
            }
        ]
    },
}


def sample_sources():
    def respond(request):
        return httpx.Response(200, json=RESPONSES[request.url.host])

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        return [
            read_selected(client, provider, item_id, container_id=container)
            for provider, item_id, container in SELECTIONS
        ]


class SampleModel:
    def complete(self, body):
        evidence = json.loads(body["messages"][1]["content"])["evidence"]
        points = [
            {
                "text": "Synthetic source: " + item["title"],
                "citations": [{"evidence_id": item["id"], "quote": item["content"][:500]}],
            }
            for item in evidence
        ]
        return ModelResult(
            json.dumps(
                {
                    "summary": {
                        "text": "Synthetic rehearsal; no live services or AI were used.",
                        "citations": [p["citations"][0] for p in points],
                    },
                    "facts": points,
                    "next_steps": [],
                    "unknowns": ["Real account access is not configured."],
                    "draft": "Synthetic draft: review ownership, deadline and support.",
                }
            ),
            {"prompt_tokens": 1, "completion_tokens": 1},
            "synthetic-only",
        )
