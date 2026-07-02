import json
import os
import urllib.error
import urllib.request


class AzureChatOpenAIConnector:
    """Lightweight Azure OpenAI chat connector using the REST API."""

    def __init__(
        self,
        endpoint: str = None,
        api_key: str = None,
        deployment_name: str = None,
        api_version: str = None,
        timeout: int = 60,
    ):
        self.endpoint = (endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT") or "").rstrip("/")
        self.api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
        self.deployment_name = deployment_name or os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        self.api_version = api_version or os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01")
        self.timeout = timeout
        self.last_usage = None

        if not self.endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required")
        if not self.api_key:
            raise ValueError("AZURE_OPENAI_API_KEY is required")
        if not self.deployment_name:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT is required")

    def _build_url(self) -> str:
        return (
            f"{self.endpoint}/openai/deployments/{self.deployment_name}/chat/completions"
            f"?api-version={self.api_version}"
        )

    def _build_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

    def invoke_llm(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {"messages": messages}
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if response_format is not None:
            payload["response_format"] = response_format

        request = urllib.request.Request(
            url=self._build_url(),
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
            raise RuntimeError(f"Azure OpenAI request failed ({exc.code}): {error_body}") from exc

        self.last_usage = data.get("usage") or None

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("Azure OpenAI returned no choices")

        message = choices[0].get("message", {})
        content = message.get("content", "")

        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict):
                    parts.append(part.get("text", ""))
            content = "".join(parts)

        return content or ""

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
            response_format={"type": "json_object"},
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

        raise json.JSONDecodeError("Could not extract JSON from Azure OpenAI response", text[:200], 0)
