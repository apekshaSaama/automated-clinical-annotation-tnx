import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

SRC_ROOT = Path(__file__).resolve().parents[2]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from connectors.anthropic_connector import AnthropicConnector
from connectors.azure_chat_openai_connector import AzureChatOpenAIConnector
from prompts import build_prompt


DEFAULT_SYSTEM_PROMPT = (
    "You are a clinical NLP annotator. Use the provided clinical note and annotation guideline "
    "as the only source of truth for extraction. Return valid JSON only. Do not include commentary. "
    "Only extract entities and relations that are explicitly supported by the guideline. "
    "Do not invent new labels or relation types. "
    "Use only the labels and relation types that appear in the annotation guideline. "
    "Use exact character offsets from the note for start and end. "
    "If an entity or relation is not clearly supported by the guideline, omit it. "
    "Return a JSON array with one document object per input note. Each document object must have "
    "id, data, annotations, and predictions. The predictions array must contain a result list with "
    "entity entries of type 'labels' and relation entries of type 'relation'."
)


_MODEL_VERSION_BY_BACKEND = {
    "anthropic": "anthropic_clinical_ner",
    "azure": "azure_openai_clinical_ner",
}


def _resolve_backend(model_name: str | None) -> str:
    normalized = (model_name or "").strip().lower()
    if normalized == "anthropic" or normalized.startswith("claude"):
        return "anthropic"
    return "azure"


def _build_connector(model_name: str | None) -> AnthropicConnector | AzureChatOpenAIConnector:
    backend = _resolve_backend(model_name)
    if backend == "anthropic":
        return AnthropicConnector()
    return AzureChatOpenAIConnector()


def _read_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as handle:
        return handle.read()


def _compute_offsets(note_text: str, mention: str) -> tuple[int, int] | None:
    if not mention:
        return None
    start = note_text.find(mention)
    if start == -1:
        return None
    end = start + len(mention)
    return start, end


def _normalize_jsl_payload(
    result: Any,
    note_text: str,
    model_version: str = "azure_openai_clinical_ner",
) -> list[dict[str, Any]]:
    if isinstance(result, list):
        if result and all(isinstance(item, dict) for item in result):
            document_items = []
            for idx, item in enumerate(result):
                if not isinstance(item, dict):
                    continue
                if any(key in item for key in ("data", "predictions", "annotations")):
                    document = {
                        "id": item.get("id", idx + 1001),
                        "data": item.get("data") or {"text": note_text},
                        "annotations": item.get("annotations", []),
                        "predictions": item.get("predictions", []),
                    }
                    if not document["data"].get("text"):
                        document["data"]["text"] = note_text
                    document_items.append(document)
                else:
                    raw_annotations = item.get("annotations") or item.get("entities") or []
                    raw_relations = item.get("relations") or []
                    prediction_result = []
                    for annotation in raw_annotations:
                        if not isinstance(annotation, dict):
                            continue
                        mention = annotation.get("text") or annotation.get("mention") or annotation.get("span") or ""
                        label = annotation.get("label") or annotation.get("entity_type") or "OTHER"
                        start_end = None
                        if isinstance(annotation.get("start"), int) and isinstance(annotation.get("end"), int):
                            start_end = (annotation["start"], annotation["end"])
                        else:
                            start_end = _compute_offsets(note_text, mention)

                        if start_end is None:
                            continue

                        prediction_result.append({
                            "id": f"pred_chunk_{len(prediction_result) + 1}",
                            "from_name": "label",
                            "to_name": "text",
                            "type": "labels",
                            "value": {
                                "start": start_end[0],
                                "end": start_end[1],
                                "text": mention,
                                "labels": [label],
                            },
                        })

                    for relation in raw_relations:
                        if not isinstance(relation, dict):
                            continue
                        source = relation.get("source") or {}
                        target = relation.get("target") or {}
                        label = relation.get("label") or relation.get("relation") or "RELATED_TO"
                        source_id = source.get("id") if isinstance(source, dict) else str(source)
                        target_id = target.get("id") if isinstance(target, dict) else str(target)
                        if not source_id:
                            source_id = f"pred_chunk_{len(prediction_result) + 1}"
                        if not target_id:
                            target_id = f"pred_chunk_{len(prediction_result) + 2}"
                        prediction_result.append({
                            "id": f"pred_rel_{len(prediction_result) + 1}",
                            "from_id": source_id,
                            "to_id": target_id,
                            "type": "relation",
                            "labels": [label],
                            "score": 0.95,
                        })

                    document_items.append({
                        "id": item.get("id", idx + 1001),
                        "data": {"text": note_text},
                        "annotations": [],
                        "predictions": [{
                            "id": "pred_set_771",
                            "model_version": model_version,
                            "score": 0.89,
                            "result": prediction_result,
                        }],
                    })
            if document_items:
                return document_items

    if isinstance(result, dict):
        if "predictions" in result and "data" in result:
            return [{
                "id": result.get("id", 1001),
                "data": result.get("data") or {"text": note_text},
                "annotations": result.get("annotations", []),
                "predictions": result.get("predictions", []),
            }]

        raw_annotations = result.get("annotations") or result.get("entities") or []
        raw_relations = result.get("relations") or []
    else:
        raw_annotations = result if isinstance(result, list) else []
        raw_relations = []

    prediction_result: list[dict[str, Any]] = []
    for item in raw_annotations:
        if not isinstance(item, dict):
            continue
        mention = item.get("text") or item.get("mention") or item.get("span") or ""
        label = item.get("label") or item.get("entity_type") or "OTHER"
        start_end = None
        if isinstance(item.get("start"), int) and isinstance(item.get("end"), int):
            start_end = (item["start"], item["end"])
        else:
            start_end = _compute_offsets(note_text, mention)

        if start_end is None:
            continue

        prediction_result.append({
            "id": f"pred_chunk_{len(prediction_result) + 1}",
            "from_name": "label",
            "to_name": "text",
            "type": "labels",
            "value": {
                "start": start_end[0],
                "end": start_end[1],
                "text": mention,
                "labels": [label],
            },
        })

    for item in raw_relations:
        if not isinstance(item, dict):
            continue
        source = item.get("source") or {}
        target = item.get("target") or {}
        label = item.get("label") or item.get("relation") or "RELATED_TO"
        source_id = source.get("id") if isinstance(source, dict) else str(source)
        target_id = target.get("id") if isinstance(target, dict) else str(target)
        if not source_id:
            source_id = f"pred_chunk_{len(prediction_result) + 1}"
        if not target_id:
            target_id = f"pred_chunk_{len(prediction_result) + 2}"
        prediction_result.append({
            "id": f"pred_rel_{len(prediction_result) + 1}",
            "from_id": source_id,
            "to_id": target_id,
            "type": "relation",
            "labels": [label],
            "score": 0.95,
        })

    return [{
        "id": 1001,
        "data": {"text": note_text},
        "annotations": [],
        "predictions": [{
            "id": "pred_set_771",
            "model_version": model_version,
            "score": 0.89,
            "result": prediction_result,
        }],
    }]


def extract_clinical_ner(
    clinical_note: str,
    guideline_text: str | None = None,
    connector: AnthropicConnector | AzureChatOpenAIConnector | None = None,
    system_prompt: str | None = None,
    model_name: str | None = None,
) -> dict[str, Any]:
    if not clinical_note or not clinical_note.strip():
        raise ValueError("clinical_note must not be empty")

    if connector is None:
        connector = _build_connector(model_name)

    guideline_text = guideline_text or ""
    prompt = build_prompt(model_name or "", clinical_note, guideline_text)

    result = connector.invoke_llm_for_json(
        prompt=prompt,
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
    )

    model_version = _MODEL_VERSION_BY_BACKEND[_resolve_backend(model_name)]
    return _normalize_jsl_payload(result, clinical_note, model_version=model_version)


def _build_output_path(note_name: str, backend: str, output_path: str | None = None) -> str | None:
    if output_path:
        return output_path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_folder = backend.lower()
    os.makedirs(model_folder, exist_ok=True)
    return os.path.join(model_folder, f"{note_name}_output_{timestamp}.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract clinical NER as JSL-compatible JSON using Azure OpenAI or Anthropic")
    parser.add_argument("note", nargs="?", help="Clinical note text to analyze")
    parser.add_argument("--file", dest="file_path", help="Path to a text file containing the clinical note")
    parser.add_argument("--guideline", dest="guideline_path", help="Path to the annotation guideline file")
    parser.add_argument("--output", dest="output_path", help="Optional file to write the JSON results")
    parser.add_argument(
        "--model",
        dest="model_name",
        help="Model name used for prompt selection and backend routing. Pass 'anthropic' to use the "
        "Anthropic API instead of Azure OpenAI.",
    )
    args = parser.parse_args()

    if args.file_path:
        note_text = _read_text(args.file_path)
        note_name = os.path.splitext(os.path.basename(args.file_path))[0]
    else:
        note_text = args.note or ""
        if not note_text:
            note_text = input("Enter clinical note: ")
        note_name = "note"

    if args.guideline_path:
        guideline_text = _read_text(args.guideline_path)
    else:
        default_guideline = os.path.join(os.path.dirname(__file__), "annotation_guideline.md")
        guideline_text = _read_text(default_guideline) if os.path.exists(default_guideline) else ""

    backend = _resolve_backend(args.model_name)
    connector = _build_connector(args.model_name)

    start_time = time.perf_counter()
    output = extract_clinical_ner(
        note_text,
        guideline_text=guideline_text,
        connector=connector,
        model_name=args.model_name,
    )
    elapsed_seconds = round(time.perf_counter() - start_time, 3)
    usage = getattr(connector, "last_usage", None) or {}

    output_path = _build_output_path(note_name, backend, args.output_path)

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(output, handle, indent=2)
        metrics_payload = {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "elapsed_seconds": elapsed_seconds,
        }
        print(f"METRICS_JSON {json.dumps(metrics_payload)}")
        print(f"Saved results to {output_path}")
    else:
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
