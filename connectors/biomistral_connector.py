import json
import os
from typing import Any


class BioMistralConnector:
    """
    Lightweight connector for running a BioMistral model locally via Hugging Face transformers.

    Environment variables used by default:
        BIOMISTRAL_MODEL_NAME
        BIOMISTRAL_DEVICE
        BIOMISTRAL_MAX_NEW_TOKENS
    """

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        max_new_tokens: int | None = None,
        temperature: float = 0.1,
    ):
        self.model_name = model_name or os.environ.get("BIOMISTRAL_MODEL_NAME", "biomistral/BioMistral-7B")
        self.device = device or os.environ.get("BIOMISTRAL_DEVICE")
        self.max_new_tokens = int(max_new_tokens or os.environ.get("BIOMISTRAL_MAX_NEW_TOKENS", "512"))
        self.temperature = temperature
        self._pipeline = None

    def _load_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline

        try:
            import torch
        except ImportError as exc:  # pragma: no cover - runtime environment dependent
            raise RuntimeError("Install torch and transformers to use BioMistralConnector") from exc

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        except ImportError as exc:  # pragma: no cover - runtime environment dependent
            raise RuntimeError("Install transformers to use BioMistralConnector") from exc

        torch_dtype = torch.float16 if self.device not in (None, "cpu", "CPU") and torch.cuda.is_available() else torch.float32
        tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype=torch_dtype,
        )

        if self.device is None:
            device_arg = 0 if torch.cuda.is_available() else -1
        else:
            device_arg = 0 if str(self.device).lower() in {"cuda", "gpu", "0"} else -1

        if str(self.device).lower() not in {"cpu", "CPU"} and torch.cuda.is_available():
            model.to("cuda")

        self._pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device=device_arg,
        )
        return self._pipeline

    def _format_prompt(self, prompt: str, system_prompt: str | None = None) -> str:
        if system_prompt:
            return f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]"
        return f"<s>[INST] {prompt} [/INST]"

    def invoke_llm(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("prompt must not be empty")

        pipeline = self._load_pipeline()
        formatted_prompt = self._format_prompt(prompt, system_prompt)

        output = pipeline(
            formatted_prompt,
            max_new_tokens=max_tokens or self.max_new_tokens,
            temperature=temperature if temperature is not None else self.temperature,
            do_sample=(temperature is not None or self.temperature > 0),
            pad_token_id=0,
            eos_token_id=2,
        )

        generated = output[0]["generated_text"]
        if generated.startswith(formatted_prompt):
            generated = generated[len(formatted_prompt):]
        return generated.strip()

    def invoke_llm_for_json(
        self,
        prompt: str,
        system_prompt: str | None = None,
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

        raise json.JSONDecodeError("Could not extract JSON from BioMistral response", text[:200], 0)
