# Annotation Guideline for KRAS, NRAS, and MSI Biomarkers

## Purpose
This guideline defines how to annotate biomedical concepts related to colorectal cancer biomarkers in clinical notes. The focus is on named entities, assertion values, and relations involving KRAS, NRAS, and microsatellite instability (MSI).

## 1. Named Entity Recognition (NER) Labels
Use the following labels when the text refers to a relevant biomedical concept.

### Core labels
- GENE: Gene names such as KRAS, NRAS, BRAF.
- MUTATION: Specific mutation names such as G12D, G13D, Q61K, V600E.
- MSI: Terms referring to microsatellite instability, such as MSI, MSI-H, MSI-Low, MSS, microsatellite stable, microsatellite instability.
- TEST: Laboratory or pathology tests such as molecular testing, sequencing, MSI testing, mutation analysis.
- RESULT: Outcome or interpretation such as detected, negative, absent, positive, wild-type, pending.
- STATUS: Status terms such as MSI-Low, MSI-H, MSS, microsatellite stable, microsatellite instability.
- TREATMENT: Treatment concepts such as chemotherapy, immunotherapy, targeted therapy.

### Special guidance for biomarkers
- Annotate KRAS and NRAS as GENE whenever they appear as gene names.
- Annotate specific mutation forms such as KRAS G12D, KRAS G13D, NRAS Q61K, BRAF V600E as a combined entity if the phrase clearly refers to a mutation event.
- Annotate MSI-related terms as MSI when they express instability status or phenotype.

## 2. Assertion Annotation
Assertion describes whether an entity is present, negated, hypothetical, or uncertain.

Use the following assertion values:
- positive: The biomarker, mutation, or abnormality is present or confirmed.
- negative: The biomarker or mutation is absent or not detected.
- possible: The biomarker is suspected but not confirmed.
- conditional: The biomarker is mentioned in a future or planned context.
- uncertain: The statement is ambiguous or speculative.

### Examples
- "KRAS G12D mutation detected" -> positive
- "NRAS testing was negative" -> negative
- "BRAF V600E was not detected" -> negative
- "MSI testing showed MSI-Low phenotype" -> positive with MSI-Low context
- "KRAS testing pending" -> conditional

## 3. Relation Annotation
Annotate relations between entities when they are explicitly connected in the text.

### Recommended relation types
- HAS_MUTATION: Connects a GENE to a MUTATION or to a gene-mutation phrase.
  - Example: KRAS -> G12D
- HAS_RESULT: Connects a TEST to a RESULT.
  - Example: MSI testing -> MSI-H
- HAS_STATUS: Connects an MSI concept to a STATUS entity.
  - Example: MSI -> MSI-Low
- INFLUENCES_TREATMENT: Connects a mutation or MSI result to a treatment concept.
  - Example: MSI-H -> immunotherapy
- HAS_TEST: Connects a note context to a diagnostic test.
  - Example: molecular testing -> MSI testing

## 4. Annotation Rules
1. Annotate the full meaningful span, not just a single word when possible.
   - Example: "KRAS G12D mutation" should be annotated as a combined mutation concept if the phrase is used as one term.
2. Preserve the original text span as closely as possible.
3. If a gene and mutation are written together, annotate them as related entities rather than merging them incorrectly.
4. Do not annotate general words like "testing" alone unless they clearly refer to a diagnostic procedure.
5. For MSI, annotate both the general concept and the specific subtype when both appear.
   - Example: "microsatellite instability (MSI) testing" -> annotate MSI as a concept and test as TEST.
6. When the note says a mutation or MSI finding is negative, annotate the concept and assign the negative assertion.

## 5. Example Annotations
### Example 1
Text: "KRAS G12D mutation detected in tumor tissue."
- KRAS -> GENE
- G12D -> MUTATION
- mutation detected -> RESULT (positive assertion)
- Relation: HAS_MUTATION(KRAS, G12D)

### Example 2
Text: "NRAS testing was negative."
- NRAS -> GENE
- testing -> TEST
- negative -> RESULT (negative assertion)
- Relation: HAS_RESULT(NRAS testing, negative)

### Example 3
Text: "MSI testing showed MSI-H phenotype."
- MSI testing -> TEST
- MSI-H -> MSI
- phenotype -> RESULT or context
- Relation: HAS_RESULT(MSI testing, MSI-H)

## 6. Notes for Annotators
- Distinguish between gene names and mutation names.
- Distinguish between MSI as a general concept and MSI-H/MSI-Low as specific STATUS entities.
- When a mutation is described as "wild-type," annotate it as a negative or absent result rather than a mutation event.
- Use consistent labels across all notes.
