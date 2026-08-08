"""Base LLM provider interface."""

import json
from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Standard LLM response."""
    content: str
    model: str = ""
    tokens_used: int = 0
    finish_reason: str = ""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, model: str, api_key: str, temperature: float = 0.7,
                 max_tokens: int = 2048, timeout: int = 30):
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        ...

    async def structured_generate(
        self,
        messages: list[dict[str, str]],
        response_model: Type[BaseModel],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Any:
        """Generate a structured response that conforms to a Pydantic model."""
        schema = response_model.model_json_schema()
        schema_str = json.dumps(schema, indent=2)

        # Append schema instruction to the last message
        enhanced_messages = messages.copy()
        schema_instruction = (
            f"\n\nYou MUST respond with valid JSON that conforms to this schema:\n"
            f"```json\n{schema_str}\n```\n"
            f"Respond ONLY with the JSON object, no additional text."
        )

        if enhanced_messages:
            last_msg = enhanced_messages[-1].copy()
            last_msg["content"] = last_msg["content"] + schema_instruction
            enhanced_messages[-1] = last_msg

        response = await self.generate(
            enhanced_messages,
            temperature=temperature or 0.3,  # Lower temp for structured output
            max_tokens=max_tokens,
        )

        # Parse JSON from response
        content = response.content.strip()
        # Handle markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        try:
            data = json.loads(content)
            return response_model.model_validate(data)
        except (json.JSONDecodeError, Exception) as e:
            # Try to extract JSON from the response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    data = json.loads(content[start:end])
                    return response_model.model_validate(data)
                except (json.JSONDecodeError, Exception):
                    pass
            raise ValueError(f"Failed to parse structured output: {e}\nContent: {content[:500]}")
