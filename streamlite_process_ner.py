import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


DEFAULT_NOTES_FOLDER = ROOT / "notes" / "consultation"
DEFAULT_GUIDELINE_PATH = ROOT / "annotation_guideline.md"
DEFAULT_OUTPUT_FOLDER = ROOT / "azure"

MODEL_OPTIONS = {
    "OpenAI (Azure)": "openai",
    "Claude (Anthropic)": "claude",
}

st.set_page_config(page_title="Clinical NER Pipeline", layout="wide")


def load_json_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def get_documents(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    raise ValueError("Expected a JSON object or a JSON array.")


def extract_entities(doc: dict[str, Any]) -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    predictions = doc.get("predictions") or []
    for prediction in predictions:
        for item in prediction.get("result") or []:
            if item.get("type") != "labels":
                continue
            value = item.get("value") or {}
            start = value.get("start")
            end = value.get("end")
            text = value.get("text") or ""
            labels = value.get("labels") or []
            if isinstance(start, int) and isinstance(end, int):
                entities.append(
                    {
                        "id": item.get("id"),
                        "text": text,
                        "start": start,
                        "end": end,
                        "labels": labels,
                        "label": labels[0] if labels else "UNKNOWN",
                    }
                )
    return sorted(entities, key=lambda entry: entry["start"])


def extract_relations(doc: dict[str, Any], entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entity_map = {entity["id"]: entity for entity in entities if entity.get("id")}
    relations: list[dict[str, Any]] = []
    predictions = doc.get("predictions") or []
    for prediction in predictions:
        for item in prediction.get("result") or []:
            if item.get("type") != "relation":
                continue
            labels = item.get("labels") or []
            relations.append(
                {
                    "id": item.get("id"),
                    "source": entity_map.get(item.get("from_id")),
                    "target": entity_map.get(item.get("to_id")),
                    "labels": labels,
                    "label": labels[0] if labels else "UNKNOWN",
                    "score": item.get("score"),
                }
            )
    return relations

st.markdown(
    """
    <style>
    .page-title {
        color: var(--e-global-color-cf16703, #003d99);
        font-size: 3rem;
        font-weight: 700;
        line-height: 1.05;
        margin-bottom: 0.25rem;
        text-align: center;
        display: block;
        width: 100%;
        margin-left: auto;
        margin-right: auto;
    }
    .page-subtitle {
        font-size: 1.05rem;
        color: #525252;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    [data-testid="stTextInput"] label,
    [data-testid="stSelectbox"] label {
        color: var(--e-global-color-cf16703, #003d99);
        font-weight: 600;
    }
    
    /* 1. Apply standard custom blue border line shadow */
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] div[role="combobox"],
    [data-testid="stSelectbox"] div[data-baseweb="select"],
    .stSelectbox div[data-baseweb="select"] > div {
        border-color: var(--e-global-color-cf16703, #003d99) !important;
        box-shadow: 0 0 0 1px var(--e-global-color-cf16703, #003d99) inset !important;
    }
    
    /* 2. OVERRIDE: Eliminates the native orange/red highlight ring on focus completely */
    [data-testid="stTextInput"] input:focus,
    [data-testid="stSelectbox"] div[role="combobox"]:focus,
    [data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within,
    .stSelectbox div[data-baseweb="select"] > div:focus-within,
    .stSelectbox div[data-baseweb="select"] > div:active,
    .stSelectbox div[data-baseweb="select"] > div:focus {
        outline: 2px solid rgba(0, 61, 153, 0.25) !important;
        border-color: var(--e-global-color-cf16703, #003d99) !important;
        box-shadow: 0 0 0 1px var(--e-global-color-cf16703, #003d99) inset !important;
    }
    
    /* 3. Ensure parent submit button container spans full width */
    div[data-testid="stFormSubmitButton"] {
        width: 100% !important;
        display: block !important;
        text-align: center !important;
        margin-top: 1rem !important;
    }

    /* 4. Center button element */
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #003d99 !important; 
        color: #ffffff !important;
        border-color: #003d99 !important;
        
        padding: 0.2rem 1.5rem !important; 
        font-size: 0.95rem !important;
        
        max-width: 150px !important; 
        margin: 0 auto !important; 
        display: block !important;
        
        border-radius: 8px !important;
        font-weight: 700 !important;
        box-shadow: none !important;
    }
    
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #002966 !important; 
        border-color: #002966 !important;
        color: #ffffff !important;
    }
    </style>

    <div class="page-title">Clinical NER Processing</div>
    """,
    unsafe_allow_html=True,
)

with st.form("annotation_form"):
    notes_folder_path = st.text_input("Notes folder path", value=str(DEFAULT_NOTES_FOLDER))
    guideline_path = st.text_input("Guideline file path", value=str(DEFAULT_GUIDELINE_PATH))
    output_folder_path = st.text_input("Output folder path", value=str(DEFAULT_OUTPUT_FOLDER))
    model_label = st.selectbox("Model", options=list(MODEL_OPTIONS.keys())) 

    submitted = st.form_submit_button("Annotate", use_container_width=True)
if submitted:
    notes_folder = Path(notes_folder_path).expanduser()
    guideline_file = Path(guideline_path).expanduser()
    output_folder = Path(output_folder_path).expanduser()
    model_name = MODEL_OPTIONS[model_label]

    if not notes_folder.is_dir():
        st.error(f"Notes folder not found: {notes_folder}")
        st.stop()
    if not guideline_file.exists():
        st.error(f"Guideline file not found: {guideline_file}")
        st.stop()

    output_folder.mkdir(parents=True, exist_ok=True)

    with st.spinner("Running clinical NER extraction..."):
        cmd = [
            sys.executable,
            str(ROOT / "clinical_ner_extractor.py"),
            "--input_folder",
            str(notes_folder),
            "--output_folder",
            str(output_folder),
            "--guideline",
            str(guideline_file),
            "--model",
            model_name,
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))

    if completed.returncode == 0:
        success_log_file = output_folder / "annotation_success.log"
        with open(success_log_file, "w", encoding="utf-8") as handle:
            if completed.stdout:
                handle.write("STDOUT:\n")
                handle.write(completed.stdout)
                handle.write("\n")
            if completed.stderr:
                handle.write("STDERR:\n")
                handle.write(completed.stderr)
                handle.write("\n")

        st.success(f"Annotation complete. Results written to: {output_folder}")
        st.info(f"Success log written to: {success_log_file}")
        # if st.button("Clinical NER JSON Viewer"):
        #     payload = load_json_file(str(output_file))
        #     documents = get_documents(payload)
        #     if not documents:
        #         st.warning("No documents were found in the generated JSON.")
        #         st.stop()

        #     document = documents[0]
        #     text = (document.get("data") or {}).get("text") or ""
        #     entities = extract_entities(document)
        #     relations = extract_relations(document, entities)

        #     col1, col2 = st.columns([1.2, 1.0], gap="large")
        #     with col1:
        #         st.subheader("Clinical Note")
        #         st.text_area("Note", value=text, height=420, disabled=True)
        #     with col2:
        #         st.subheader("Entities")
        #         if entities:
        #             for entity in entities:
        #                 st.markdown(
        #                     f"<div style='font-size: 0.95rem;'>- {entity['text']} → {entity['label']} ({entity['start']}, {entity['end']})</div>",
        #                     unsafe_allow_html=True,
        #                 )
        #         else:
        #             st.info("No entities found.")

        #         st.subheader("Relations")
        #         if relations:
        #             for relation in relations:
        #                 source_text = relation.get("source", {}).get("text", "<unknown>")
        #                 target_text = relation.get("target", {}).get("text", "<unknown>")
        #                 st.markdown(
        #                     f"<div style='font-size: 0.95rem;'>- {source_text} → {target_text} [{relation['label']}]</div>",
        #                     unsafe_allow_html=True,
        #                 )
        #         else:
        #             st.info("No relations found.")
    else:
        log_file = output_folder / "annotation_error.log"
        with open(log_file, "w", encoding="utf-8") as handle:
            if completed.stderr:
                handle.write("STDERR:\n")
                handle.write(completed.stderr)
                handle.write("\n")
            if completed.stdout:
                handle.write("STDOUT:\n")
                handle.write(completed.stdout)
                handle.write("\n")

        st.error("Annotation failed. Check the log file for details.")
        # st.info(f"Error log written to: {log_file}")
