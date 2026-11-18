import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class ProviderResult:
    answer: str
    model: str
    input_tokens: int
    output_tokens: int


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, prompt_version: str) -> ProviderResult:
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    def generate(self, prompt: str, prompt_version: str) -> ProviderResult:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key is not configured")

        system_instruction = (
            "Return only valid JSON. "
            "Use this schema: {\"answer\":\"string\"}. "
            f"Use prompt version {prompt_version}. "
        )
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.gemini_model}:generateContent"
        )
        try:
            response = httpx.post(
                url,
                params={"key": settings.gemini_api_key},
                json={
                    "systemInstruction": {"parts": [{"text": system_instruction}]},
                    "generationConfig": {"responseMimeType": "application/json"},
                    "contents": [{"parts": [{"text": prompt}]}],
                },
                timeout=30,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ValueError("Gemini provider request failed") from exc

        payload = response.json()
        candidates = payload.get("candidates") or []
        if not candidates:
            raise ValueError("Gemini returned no candidate response")
        parts = candidates[0].get("content", {}).get("parts") or []
        text = "".join(str(part.get("text", "")) for part in parts).strip()
        try:
            structured = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("Gemini returned invalid structured output") from exc
        if not isinstance(structured, dict) or not isinstance(structured.get("answer"), str):
            raise ValueError("Gemini response does not match the required schema")

        usage = payload.get("usageMetadata") or {}
        return ProviderResult(
            answer=structured["answer"],
            model=settings.gemini_model,
            input_tokens=int(usage.get("promptTokenCount", 0)),
            output_tokens=int(usage.get("candidatesTokenCount", 0)),
        )


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.ai_provider == "gemini":
        return GeminiProvider()
    raise ValueError("Unsupported AI provider")
