# automated-clinical-annotation-tnx

Extracts entities, relations, and assertion statuses from clinical notes as
JSL (John Snow Labs / Label Studio) compatible prediction JSON, using an LLM
guided by an annotation guideline document.

## Requirements

- Python 3.10+
- No third-party packages are required to run `clinical_ner_extractor.py` — it
  only uses the standard library plus the connector for whichever backend you
  select.

## Backend configuration

The extractor supports two LLM backends. Pick one and set the matching
environment variables before running.

### Azure OpenAI (default)

```bash
set AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
set AZURE_OPENAI_API_KEY=<your-azure-openai-key>
set AZURE_OPENAI_DEPLOYMENT=<your-deployment-name>
set AZURE_OPENAI_API_VERSION=2024-02-01   REM optional, this is the default
```

### Anthropic

```bash
set ANTHROPIC_API_KEY=<your-anthropic-api-key>
set ANTHROPIC_MODEL=claude-sonnet-5        REM optional, this is the default
set ANTHROPIC_API_VERSION=2023-06-01       REM optional, this is the default
```

(Use `export` instead of `set` on macOS/Linux.)

The backend is chosen by the `--model` flag: pass `anthropic` (or any model
name starting with `claude`) to use the Anthropic connector; anything else
uses Azure OpenAI.

## Usage

```bash
python clinical_ner_extractor.py [NOTE_TEXT] [OPTIONS]
```

| Option         | Description                                                                                   |
|----------------|-----------------------------------------------------------------------------------------------|
| `NOTE_TEXT`    | Clinical note text passed directly as an argument. Ignored if `--file` is given.               |
| `--file`       | Path to a text file containing the clinical note.                                              |
| `--guideline`  | Path to the annotation guideline file. Defaults to `annotation_guideline.md` if omitted.       |
| `--output`     | Path to write the resulting JSON. If omitted, a timestamped file is created (see below).       |
| `--model`      | Model name — selects both the backend (`anthropic` vs. Azure OpenAI) and prompt variant.       |

If neither `NOTE_TEXT` nor `--file` is given, you'll be prompted to enter the
note text interactively.

### Examples

Run with the default Azure OpenAI backend, reading a note from file:

```bash
python clinical_ner_extractor.py --file notes/consultation/consult_note_1.txt --guideline annotation_guidelines/annotation_guideline.md
```

Run against a smoking-status note using the Anthropic backend:

```bash
python clinical_ner_extractor.py --file notes/smoking/100070.txt --guideline annotation_guidelines/Smoking_Status.md --model anthropic
```

Pass note text inline and write to a specific output path:

```bash
python clinical_ner_extractor.py "Patient denies tobacco use." --guideline annotation_guidelines/Smoking_Status.md --model anthropic --output claude_output/inline_note.json
```

## Output

- If `--output` is not provided, results are written to `<backend>/<note_name>_output_<timestamp>.json`,
  where `<backend>` is `azure` or `anthropic` depending on `--model`
  (e.g. `azure/consult_note_1_output_20260702_120000.json`). See
  `_build_output_path` in `clinical_ner_extractor.py` for the exact logic.
- When writing to a file, a line like `METRICS_JSON {"prompt_tokens": ..., "completion_tokens": ..., "total_tokens": ..., "elapsed_seconds": ...}`
  is printed to stdout with token usage and timing.
- If no output path resolves, the JSON is printed to stdout instead.

The output is a JSON array of document objects (`id`, `data`, `annotations`,
`predictions`), where each `predictions[].result` entry is one of:

- an **entity** — `type: "labels"`, `from_name: "label"`
- an **assertion** attached to an entity span — `type: "labels"`, `from_name: "assertion"`, same `start`/`end`/`text` as the entity it applies to
- a **relation** between two entities — `type: "relation"`, linking `from_id`/`to_id`

See [prompts.py](prompts.py) for the exact prompt/output-format contract given
to the model.
