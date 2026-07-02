# Annotation Guideline for Alcohol Use Biomarkers

## Purpose
This guideline defines how to annotate mentions of alcohol use, quantity, frequency, related problems, and clinical management in clinical notes.

## 1. Named Entity Recognition (NER) Labels
Use the following labels when the text refers to a relevant alcohol-related concept.

### Core labels
- ALCOHOL_STATUS: Overall drinking status such as current, former, never, social drinker, denies alcohol.
- ALCOHOL_QUANTITY: Amount consumed such as 2 beers, 1 bottle wine, 6 drinks.
- ALCOHOL_FREQUENCY: How often alcohol is consumed such as daily, weekends, occasionally, 3x/week.
- ALCOHOL_TYPE: The kind of alcohol consumed such as beer, wine, liquor, vodka.
- ALCOHOL_PROBLEM: Diagnosed or described alcohol-related disorders such as alcohol abuse, dependence, alcoholism, AUD.
- ALCOHOL_WITHDRAWAL: Withdrawal symptoms or events such as withdrawal, DTs, seizure.
- ALCOHOL_SCREENING_SCORE: Standardized screening tool results such as AUDIT-C 8, CAGE 2/4.
- ALCOHOL_ABSTINENCE: Terms indicating cessation or recovery such as sober, abstinent, in recovery.
- ALCOHOL_COUNSELING: Clinical guidance or intervention such as advised to stop, counseling, reduce intake.

## 2. Assertion Annotation
Assertion describes whether an entity is present, negated, hypothetical, or uncertain.

Use the following assertion values:
- positive: The alcohol use, problem, or symptom is present or confirmed.
- negative: Alcohol use or the condition is denied or absent.
- possible: The condition is suspected but not confirmed.
- conditional: The behavior or plan is mentioned in a future or planned context.
- uncertain: The statement is ambiguous or speculative.

### Examples
- "Patient reports drinking 2 beers daily" -> positive
- "Denies alcohol use" -> negative
- "History of alcohol dependence" -> positive
- "Advised to stop drinking" -> conditional (counseling)
- "Possible alcohol withdrawal" -> possible

## 3. Relation Annotation
Annotate relations between entities when they are explicitly connected in the text.

### Recommended relation types
- HAS_QUANTITY: Connects an ALCOHOL_TYPE or ALCOHOL_STATUS to an ALCOHOL_QUANTITY.
  - Example: beer -> 2 beers
- HAS_FREQUENCY: Connects an ALCOHOL_STATUS or ALCOHOL_TYPE to an ALCOHOL_FREQUENCY.
  - Example: wine -> daily
- HAS_TYPE: Connects an ALCOHOL_STATUS to a specific ALCOHOL_TYPE.
  - Example: current drinker -> vodka
- HAS_SCREENING_RESULT: Connects a screening reference to an ALCOHOL_SCREENING_SCORE.
  - Example: AUDIT-C -> AUDIT-C 8
- LEADS_TO_PROBLEM: Connects alcohol use to an ALCOHOL_PROBLEM.
  - Example: daily drinking -> alcohol dependence
- HAS_WITHDRAWAL: Connects an ALCOHOL_PROBLEM or cessation event to ALCOHOL_WITHDRAWAL symptoms.
  - Example: alcohol dependence -> DTs
- RECEIVES_COUNSELING: Connects an ALCOHOL_STATUS or ALCOHOL_PROBLEM to ALCOHOL_COUNSELING.
  - Example: alcohol abuse -> advised to stop
- ACHIEVES_ABSTINENCE: Connects an ALCOHOL_PROBLEM or ALCOHOL_STATUS to ALCOHOL_ABSTINENCE.
  - Example: alcoholism -> sober

## 4. Annotation Rules
1. Annotate the full meaningful span, not just a single word when possible.
   - Example: "6 drinks per day" should be annotated as a combined ALCOHOL_QUANTITY and ALCOHOL_FREQUENCY concept if the phrase is used as one term.
2. Preserve the original text span as closely as possible.
3. If quantity, type, and frequency are written together, annotate them as separate related entities rather than merging them incorrectly.
   - Example: "2 beers on weekends" -> ALCOHOL_QUANTITY(2 beers), ALCOHOL_FREQUENCY(weekends).
4. Do not annotate general words like "drinking" alone unless they clearly refer to a specific status, type, or quantity.
5. For screening scores, annotate both the tool name and the numeric result as one ALCOHOL_SCREENING_SCORE span when they appear together.
   - Example: "CAGE 2/4" -> single ALCOHOL_SCREENING_SCORE entity.
6. When the note explicitly denies alcohol use, annotate the concept and assign the negative assertion.
7. Distinguish ALCOHOL_ABSTINENCE (current sober state) from ALCOHOL_STATUS (former/never), since abstinence implies a prior history of use.

## 5. Example Annotations
### Example 1
Text: "Patient is a current drinker, consumes 2 beers daily."
- current drinker -> ALCOHOL_STATUS
- 2 beers -> ALCOHOL_QUANTITY
- daily -> ALCOHOL_FREQUENCY
- Relation: HAS_QUANTITY(current drinker, 2 beers), HAS_FREQUENCY(current drinker, daily)

### Example 2
Text: "History of alcohol dependence with prior DTs during withdrawal."
- alcohol dependence -> ALCOHOL_PROBLEM
- DTs -> ALCOHOL_WITHDRAWAL
- Relation: HAS_WITHDRAWAL(alcohol dependence, DTs)

### Example 3
Text: "AUDIT-C score of 8; advised to reduce intake."
- AUDIT-C 8 -> ALCOHOL_SCREENING_SCORE
- advised to reduce intake -> ALCOHOL_COUNSELING
- Relation: HAS_SCREENING_RESULT(AUDIT-C, AUDIT-C 8)

### Example 4
Text: "Former heavy drinker, now sober for 2 years, denies current alcohol use."
- Former heavy drinker -> ALCOHOL_STATUS
- sober -> ALCOHOL_ABSTINENCE
- denies current alcohol use -> ALCOHOL_STATUS (negative assertion)
- Relation: ACHIEVES_ABSTINENCE(Former heavy drinker, sober)

## 6. Notes for Annotators
- Distinguish between alcohol type (what is consumed) and quantity (how much is consumed).
- Distinguish between ALCOHOL_PROBLEM (a diagnosed or described disorder) and ALCOHOL_STATUS (a general use pattern).
- When a note reports a screening tool without a score, do not annotate it as ALCOHOL_SCREENING_SCORE.
- Use consistent labels across all notes.
