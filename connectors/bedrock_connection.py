
import os
import json
import time
import threading

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class BedrockConnection:
    """
    Thread-safe AWS Bedrock client for LLM text generation and Titan embeddings.

    The model_id is configurable per-call so you can use different models
    for different tasks (e.g. Sonnet for complex reasoning, Haiku for fast tasks).
    """

    # Shared client across all instances (boto3 clients are thread-safe)
    _client = None
    _lock = threading.Lock()

    def __init__(
        self,
        region: str = None,
        default_model_id: str = None,
        embed_model_id: str = None,
        max_retries: int = 5,
        base_delay: float = 3.0,
    ):
        """
        Initialize the Bedrock connection.

        Args:
            region:             AWS region (env: AWS_REGION, default: us-east-1)
            default_model_id:   Default LLM model/inference profile ID (env: BEDROCK_MODEL_ID)
                                Claude 4.x requires cross-region profile with "us." prefix.
            embed_model_id:     Titan Embed model ID (env: BEDROCK_EMBED_MODEL_ID)
            max_retries:        Retry attempts on throttling (default: 3)
            base_delay:         Base backoff delay in seconds (default: 1.0)
        """
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")

        # Default model IDs — override via env or per-call
        self.default_model_id = default_model_id or os.environ.get("BEDROCK_MODEL_ID")
        #self.embed_model_id = embed_model_id or os.environ.get("BEDROCK_EMBED_MODEL_ID")
        self.max_retries = max_retries
        self.base_delay  = base_delay

        self._init_client()

    # ──────────────────────────────────────────────
    # Client setup
    # ──────────────────────────────────────────────

    def _init_client(self):
        """Create the Bedrock client (shared, created only once)."""
        with BedrockConnection._lock:
            if BedrockConnection._client is None:
                # 600s read timeout — large batch prevention prompts with extended thinking
                # (6000+ token thinking budget can take 5-8 minutes to process)
                _cfg = Config(
                    read_timeout=600,
                    connect_timeout=10,
                    retries={"max_attempts": 0},   # retry logic handled in _call_with_retry
                )
                BedrockConnection._client = boto3.client(
                    "bedrock-runtime",
                    region_name=self.region,
                    config=_cfg,
                )
                print(f"[Bedrock] Client created — region: {self.region}")
                print(f"[Bedrock] Default LLM model:   {self.default_model_id}")
                print(f"[Bedrock] Embed model:         {self.embed_model_id}")

    def _call_with_retry(self, func):
        """
        Execute a Bedrock API call with automatic retry on throttling.

        Args:
            func: Zero-argument callable that makes the API call.

        Returns:
            Result of func() on success.

        Raises:
            Last ClientError if all retries are exhausted.
        """
        _RETRYABLE = {
            "ThrottlingException",
            "ServiceUnavailableException",
            "InternalServerException",
            "ModelTimeoutException",
        }
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return func()
            except ClientError as e:
                code = e.response["Error"]["Code"]
                if code in _RETRYABLE:
                    last_error = e
                    delay = self.base_delay * (2 ** attempt)
                    print(f"[Bedrock] {code} — retrying in {delay:.1f}s "
                          f"({attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    raise
        raise last_error

    # ──────────────────────────────────────────────
    # LLM — text generation
    # ──────────────────────────────────────────────

    # Bedrock API REQUIRES max_tokens in the request body. This is the single
    # fixed output cap used for every call. High enough for our largest output
    # (section extraction ~16K tokens), low enough that
    # (input + max_tokens) fits the 200K context window.
    _MAX_OUTPUT_TOKENS = 16384

    def invoke_llm(
        self,
        prompt: str,
        system_prompt: str = None,
        model_id: str = None,
        enable_thinking: bool = False,
        thinking_budget: int = 4000,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Send a prompt to the LLM and get a text response.

        Args:
            prompt:          The user message to send.
            system_prompt:   Optional system instruction.
            model_id:        LLM model or inference profile ID.
            enable_thinking: If True, enable Claude's extended thinking mode
                             and log the private reasoning to stdout.
            thinking_budget: Tokens allowed for reasoning (only used when thinking is on).
            temperature:     Sampling temperature. Ignored when thinking is on
                             (Bedrock requires temperature=1 in that case).
            max_tokens:      Override the default output cap (_MAX_OUTPUT_TOKENS).
                             When thinking is on, thinking_budget is added on top.

        Returns:
            The model's text response as a string.
        """
        model_id = model_id or self.default_model_id

        # Final token budget: thinking budget is added on top when enabled.
        base_cap = max_tokens if max_tokens is not None else self._MAX_OUTPUT_TOKENS
        MAX_TOKENS = (thinking_budget + base_cap) if enable_thinking else base_cap

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]}
            ],
        }

        if enable_thinking:
            # temperature must be 1 when thinking is enabled
            body["thinking"]     = {"type": "enabled", "budget_tokens": thinking_budget}
            body["temperature"]  = 1
        elif temperature is not None:
            body["temperature"]  = temperature

        if system_prompt:
            body["system"] = system_prompt

        def call():
            # Debug: log request shape (chars, not tokens)
            print(f"[Bedrock] REQUEST → model={model_id} | max_tokens={body['max_tokens']} | "
                  f"thinking={'on' if 'thinking' in body else 'off'} | "
                  f"prompt_chars={len(prompt)} | system_chars={len(system_prompt or '')}")

            response = BedrockConnection._client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            result = json.loads(response["body"].read())
            stop   = result.get("stop_reason", "unknown")
            usage  = result.get("usage", {})
            print(f"[Bedrock] stop={stop} | in={usage.get('input_tokens','?')} out={usage.get('output_tokens','?')}")

            # Content is a list of blocks — may include "thinking" and "text".
            blocks = result.get("content", []) or []
            thinking_text = ""
            text = ""
            for block in blocks:
                btype = block.get("type")
                if btype == "thinking":
                    thinking_text += block.get("thinking", "")
                elif btype == "text":
                    text += block.get("text", "")

            if thinking_text:
                # Log the full thinking for debugging / audit
                print(f"[Bedrock] THINKING ({len(thinking_text)} chars):")
                print(thinking_text)
                print("[Bedrock] END THINKING")

            if not text:
                print("[Bedrock] WARNING: empty text response body")
            return text

        return self._call_with_retry(call)

    def invoke_llm_for_json(
        self,
        prompt: str,
        system_prompt: str = None,
        model_id: str = None,
        enable_thinking: bool = False,
        thinking_budget: int = 4000,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict | list:
        """
        Send a prompt to the LLM and parse the response as JSON.

        Automatically strips markdown code fences (```json ... ```) if present.

        Args:
            prompt:        The user message — must ask the model to return JSON.
            system_prompt: Optional system instruction.
            model_id:      LLM model ID (defaults to env BEDROCK_MODEL_ID).
            max_tokens:    Max output tokens.

        Returns:
            Parsed JSON as a Python dict or list.

        Example:
            entries = bedrock.invoke_llm_for_json(
                prompt="Extract PIPD subcategories. Return as a JSON array.",
                system_prompt="Output ONLY valid JSON. No commentary."
            )
            for entry in entries:
                print(entry["pd_subcategory"])
        """
        raw = self.invoke_llm(
            prompt, system_prompt, model_id,
            enable_thinking=enable_thinking,
            thinking_budget=thinking_budget,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        text = raw.strip()

        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            inner = [l for l in lines[1:] if l.strip() != "```"]
            text = "\n".join(inner).strip()

        # Try strict parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try raw_decode (stops after first complete JSON value)
        try:
            result, _ = json.JSONDecoder().raw_decode(text)
            return result
        except (json.JSONDecodeError, ValueError):
            pass

        # Find JSON array or object buried in surrounding text
        for start_char, end_char in [('[', ']'), ('{', '}')]:
            start = text.find(start_char)
            if start == -1:
                continue
            # Find the matching closing bracket
            depth = 0
            for i in range(start, len(text)):
                if text[i] == start_char:
                    depth += 1
                elif text[i] == end_char:
                    depth -= 1
                    if depth == 0:
                        candidate = text[start:i+1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break

        # Last-ditch: JSON was truncated (stop=max_tokens). Try to salvage
        # partial output by trimming to the last complete key-value pair and
        # closing remaining brackets.
        for start_char, end_char in [('{', '}'), ('[', ']')]:
            start = text.find(start_char)
            if start == -1:
                continue
            candidate = text[start:]
            # Trim to the last complete value (end with '",' or '},' or '"')
            for marker in ('"}', '",', '}]', '"\n'):
                last = candidate.rfind(marker)
                if last != -1:
                    candidate = candidate[:last + len(marker.rstrip(',\n'))]
                    break
            # Close any remaining unbalanced brackets
            depth_sq = candidate.count('[') - candidate.count(']')
            depth_cu = candidate.count('{') - candidate.count('}')
            candidate = candidate.rstrip(', \n')
            candidate += '}' * depth_cu + ']' * depth_sq
            try:
                result = json.loads(candidate)
                print(f"[Bedrock] WARNING: recovered truncated JSON — output was cut off")
                return result
            except json.JSONDecodeError:
                continue

        # Nothing worked — log and raise
        print(f"[Bedrock] JSON parse failed. Raw response (first 500 chars): {raw[:500]}")
        raise json.JSONDecodeError("Could not extract JSON from LLM response", raw[:200], 0)

    # ──────────────────────────────────────────────
    # Titan — vector embeddings
    # ──────────────────────────────────────────────

    def get_embedding(
        self,
        text: str,
        embed_model_id: str = None,
    ) -> list[float]:
        """
        Convert a text string into a vector embedding.

        Args:
            text:           The text to embed.
            embed_model_id: Embedding model ID (defaults to env BEDROCK_EMBED_MODEL_ID).

        Returns:
            List of floats (embedding vector).
            Titan v1 → 1536 dims | Titan v2 → 1024 dims

        Example:
            vector = bedrock.get_embedding("Participant missed Day 5 visit.")
            print(len(vector))  # 1024
        """
        model_id = embed_model_id or self.embed_model_id
        body     = {"inputText": text}

        def call():
            response = BedrockConnection._client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            result = json.loads(response["body"].read())
            return result["embedding"]

        return self._call_with_retry(call)

    def get_embeddings(
        self,
        texts: list[str],
        embed_model_id: str = None,
        delay_between: float = 0.2,
    ) -> list[list[float]]:
        """
        Embed a list of texts with rate-limiting delay between each call.

        Args:
            texts:          List of strings to embed.
            embed_model_id: Embedding model ID (defaults to env BEDROCK_EMBED_MODEL_ID).
            delay_between:  Seconds to wait between API calls (default: 0.2s).

        Returns:
            List of embedding vectors in the same order as input texts.

        Example:
            sections = ["eligibility criteria...", "dosing schedule..."]
            vectors = bedrock.get_embeddings(sections)
        """
        embeddings = []
        total = len(texts)

        for i, text in enumerate(texts):
            vector = self.get_embedding(text, embed_model_id)
            embeddings.append(vector)

            if i < total - 1:
                time.sleep(delay_between)

            if (i + 1) % 10 == 0 or (i + 1) == total:
                print(f"[Bedrock] Embedded {i + 1}/{total} texts")

        return embeddings

    # ──────────────────────────────────────────────
    # Health check
    # ──────────────────────────────────────────────

    def ping(self) -> dict:
        """
        Test both the LLM and embedding connections.

        Returns:
            Dict with status for llm and embed.

        Example:
            status = bedrock.ping()
            print(status["llm"])    # "connected"
            print(status["embed"])  # "connected"
        """
        result = {
            "region":          self.region,
            "default_model_id": self.default_model_id,
            "embed_model_id":  self.embed_model_id,
        }

        # Test LLM
        try:
            text = self.invoke_llm("Say OK.")
            result["llm"] = "connected"
            result["llm_response"] = text.strip()
        except Exception as e:
            result["llm"] = "error"
            result["llm_error"] = str(e)

        # Test embeddings
        try:
            vector = self.get_embedding("test")
            result["embed"] = "connected"
            result["embed_dimensions"] = len(vector)
        except Exception as e:
            result["embed"] = "error"
            result["embed_error"] = str(e)

        return result
