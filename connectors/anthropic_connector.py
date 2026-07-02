import json
import os
import urllib.error
import urllib.request


class AnthropicConnector:
    """Lightweight Anthropic Messages API connector using the REST API directly."""

    _API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        api_version: str = None,
        timeout: int = 60,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
        self.api_version = api_version or os.environ.get("ANTHROPIC_API_VERSION", "2023-06-01")
        self.timeout = timeout
        self.last_usage = None

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required")

    def _build_headers(self) -> dict:
        return {
            "content-type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
        }

    def invoke_llm(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        payload = {
            "model": self.model,
            "max_tokens": max_tokens or 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt
        if temperature is not None:
            payload["temperature"] = temperature

        request = urllib.request.Request(
            url=self._API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._build_headers(),
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                data = json.loads(body)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Anthropic request failed ({exc.code}): {error_body}") from exc

        usage = data.get("usage") or {}
        prompt_tokens = usage.get("input_tokens")
        completion_tokens = usage.get("output_tokens")
        self.last_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": (
                prompt_tokens + completion_tokens
                if prompt_tokens is not None and completion_tokens is not None
                else None
            ),
        }

        blocks = data.get("content", []) or []
        text_parts = [
            block.get("text", "")
            for block in blocks
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "".join(text_parts)

    def invoke_llm_for_json(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict | list:
        raw = self.invoke_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            inner = [line for line in lines[1:] if line.strip() != "```"]
            text = "\n".join(inner).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        try:
            result, _ = json.JSONDecoder().raw_decode(text)
            return result
        except (json.JSONDecodeError, ValueError):
            pass
        print(f"Warning: Could not parse JSON from Anthropic response. Raw text:\n{text[:200]}")
        print(f"length of text: {len(text)}")
        raise json.JSONDecodeError("Could not extract JSON from Anthropic response", text[:200], 0)
