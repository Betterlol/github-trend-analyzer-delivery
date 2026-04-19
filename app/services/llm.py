import json
import re
from typing import Any

import httpx

from app.config import get_settings


class LLMGenerationError(RuntimeError):
    pass


def extract_json_object(text: str) -> dict[str, Any]:
    content = text.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", content, flags=re.DOTALL)
    for block in fenced:
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            continue

    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = content[start : end + 1]
        return json.loads(candidate)

    raise LLMGenerationError("model response does not contain a valid JSON object")


class OpenAICompatibleLLM:
    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.llm_enabled and self.settings.llm_api_key)

    async def generate_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> dict[str, Any]:
        if not self.enabled:
            raise LLMGenerationError("LLM is disabled or API key is missing")

        base_url = self.settings.llm_base_url.rstrip("/")
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.llm_model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_sec) as client:
                response = await client.post(f"{base_url}/chat/completions", headers=headers, json=payload)
        except httpx.HTTPError as exc:
            raise LLMGenerationError(f"LLM request transport error: {exc}") from exc

        if response.status_code != 200:
            raise LLMGenerationError(f"LLM request failed: {response.status_code} {response.text}")

        try:
            body = response.json()
        except ValueError as exc:
            raise LLMGenerationError("LLM response is not valid JSON") from exc
        choices = body.get("choices", [])
        if not choices:
            raise LLMGenerationError("LLM response contains no choices")
        content = choices[0].get("message", {}).get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise LLMGenerationError("LLM response content is empty")
        return extract_json_object(content)
