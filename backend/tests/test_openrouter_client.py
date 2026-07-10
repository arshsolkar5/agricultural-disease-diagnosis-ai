import json
from types import SimpleNamespace

import pytest

from app.llm.openrouter import OpenRouterClient
from app.models.llm import VisionAnalysis


@pytest.mark.asyncio
async def test_openrouter_structured_vision_request(monkeypatch):
    captured_payload = {}

    async def fake_post(self, url, headers=None, json=None):  # noqa: A002
        captured_payload["url"] = url
        captured_payload["headers"] = headers
        captured_payload["json"] = json
        return SimpleNamespace(
            status_code=200,
            text="ok",
            json=lambda: {
                "choices": [
                    {
                        "message": {
                            "content": json_module.dumps(
                                {
                                    "crop_type": "rice",
                                    "image_quality_score": 0.82,
                                    "confidence": 0.9,
                                    "observations": [
                                        {
                                            "category": "lesion",
                                            "description": "Brown lesions visible",
                                            "confidence": 0.88,
                                        }
                                    ],
                                    "uncertainties": ["Some blur at the edges"],
                                    "follow_up_questions": ["Can you upload a closer image?"],
                                    "needs_follow_up": True,
                                    "summary": "Structured multimodal response.",
                                    "quality_notes": ["Clear enough for symptom detection."],
                                }
                            )
                        }
                    }
                ]
            },
        )

    json_module = json
    monkeypatch.setattr("httpx.AsyncClient.post", fake_post, raising=True)

    client = OpenRouterClient(api_key="test-key", model="openrouter/free", max_retries=1)
    result = await client.chat_structured(
        system_prompt="You are a crop analyst.",
        user_prompt="Analyze the crop observations and return JSON only.",
        schema_model=VisionAnalysis,
        temperature=0.0,
        max_tokens=256,
    )

    assert captured_payload["url"].endswith("/chat/completions")
    assert captured_payload["json"]["model"] == "openrouter/free"
    assert captured_payload["json"]["messages"][1]["content"] == "Analyze the crop observations and return JSON only."
    assert result.image_quality_score == pytest.approx(0.82)
    assert result.observations[0].category == "lesion"
