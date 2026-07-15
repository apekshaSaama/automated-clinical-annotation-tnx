# Smoking Status \- Current

- Involves NER and Assertion
- Tips and good practice: <https://www.johnsnowlabs.com/tips-and-tricks-on-how-to-annotate-assertion-in-clinical-texts/>
- Article on how to achieve higher accuracy in assertion classification: <https://arxiv.org/abs/2503.17425>

# Alignment on annotations

## NER (General)

- NER Labels: **Smoking\_Status, Substance\_Quantity, Substance\_Duration, Substance\_Frequency, Smoking\_Type, Section\_Header**
- When Smoking / Tobacco is part of section header, this should be annotated appropriately as “section header” and does need any assertion
- Is “Passive Exposure” a type of smoking that we should annotate?
    -  we do not need to worry about it for this set of annotations.  This would be more for specific studying regarding second-hand smoke
- In many ambulatory notes, *patient education* is listed, these often mention recommendations/help on quitting smoking, alcoholism in the family. 
    - Do **NOT** need to annotate patient education info or patient counseling info
- “Smokeless tobacco use: “ and “Electronic Cigarette/Vaping: “
    - We will ignore these phrases for now, as they are default “fields” in the form - Do **NOT** need to annotate as NER
- Do not annotate Nicotine when listed as drug
- Do not annotate questionnaires
- Do not annotate words which are related to smoking
- Mind section headers


## Assertion (General)

THE CONTEXT WINDOW FOR ASSERTION IS THE **SENTENCE**

ASSERTION LABELS ARE ASSIGNED ONLY TO **SMOKING\_STATUS **NER

- **Current smoker**: active smoker, current every day smoker, patient smokes, smokes daily, smokes occasionally
- **Former smoker**: ex-smoker, past smoker, remote smoker, distant smoker, reformed smoker, in remission, remote smoker
- **Never smoker**: lifelong non-smoker, never smoked, no history of smoking
- **Unknown if ever smoked**: if unclear if former or never smoker, often mentioned as "non smoker" without any other detail, please note Never smokers will be a subgroup of this group. If in one sentence patient is described as nonsmoker without any other detail, please use this label. Even if in a different sentence patient is described as a former smoker. The context for assertion is within that one sentence.
    - This is used when we know the current status but not historical status
- **Smoker current status unknown**: if unclear if still smoking, "patient has history of smoking", "History of tobacco use", “Tobacco use HX”, please note Current and Former smokers will be subgroups of this group
    - This is used when we know the historical status but not current status
- **Someone Else**: relates to family, household (for example "parents smoke outdoors", "family history of tobacco use")


 NER and Assertion combinations for smoking

- “Tobacco use (date): never (less than 100 cigarettes in lifetime)”
    - NER: **Smoking\_Status**:** “**Tobacco”
    - Assertion: **Never smoker**
    - NER: **Substance\_Quantity: **“less than 100 cigarettes in lifetime“ without Assertion
- “Tobacco: (date); Use: Former smoker, quit more; Smokeless tobacco use: Never; Type: Cigarettes;
    - Both “Tobacco” and “smoker” annotate as **Smoking\_Status **with **Assertion Former smoker**
    - “Cigarettes” in this case annotate as **Smoking\_Type**
    - “Smokeless tobacco” ignore altogether
- “PATIENT WITH 50 PACK YEAR HX OF SMOKING”
    - NER: **Substance\_Quantity: **“50 PACK YEAR” - Assertion skipped
    - NER: **Smoking\_Status **with **Assertion Smoker current status unknown**
- "2 packs per day for 25 years" 
    - NER: **Substance\_Frequency: **“2 packs per day”
    - NER: **Substance\_Duration: **“25 years”
- “He quit smoking over 50 years ago”
    - NER: **Smoking\_Status**: “smoking” with **Assertion Former smoker**
    - “50 years ago” is **NOT** Substance\_Duration — it describes how long ago the patient quit, not how long they smoked, so it should be left unannotated
- “NONSMOKER”
- NER: **~~Smoking\_Status~~**~~:~~**~~~~**~~“NONSMOKER”~~ updated tokenization rule: exceptionally “smoker” in the full word “nonsmoker” should be tagged
- Assertion: **Unknown if ever smoked**
- “non-smoker” or “ex-smoker”
    - NER: **Smoking\_Status**:“smoker”
    - **Unknown if ever smoked**: for “non” and  **Former smoker** for “ex”
- “Social smoker in the past”
    - NER: **Smoking\_Status**:“smoker”
    - NER: **Substance\_Frequency**: “social”
- “female patient who is heavy smoker presented with a burning sensation”
    - NER: **Smoking\_Status**: “smoker” with **Assertion Current smoker**
    - NER: **Substance\_Frequency**: “heavy”
    - “burning sensation” is a symptom, unrelated to smoking - do not annotate
- “Nicotine Polacrilex 2mg Chew 2 mg, Oral, Q2H, PRN: Nicotine Withdrawal”
    - DO NOT LABEL NICOTINE WHEN LISTED AS DRUG
- “He was a chronic smoker of 80 packet years and a social alcoholic.”
    - NER: **Smoking\_Status**: “smoker” with **Assertion Current smoker**
    - NER: **Substance\_Quantity**: “80 packet years” without Assertion
    - “alcoholic” is not smoking-related — ignore
    - **Why Current smoker and not Former smoker**: “chronic” describes an ongoing, habitual smoking behavior, not a discontinued one. The past-tense verb “was” here reflects the tense of the note/sentence (often how a clinical note narrates a patient's history), **not** that the patient quit. Do not rely on verb tense alone to decide current vs. former — look for explicit cues of cessation (“quit”, “ex-”, “former”, “in the past”) before assigning **Former smoker**. Absent such cues, “chronic smoker” should be read as **Current smoker** even when phrased in past tense

 

# Project Status Report

### Link: [Project Status](https://rwhdinc-my.sharepoint.com/:x:/r/personal/swati_ajayan_trinetx_com/Documents/Project%20Tracker.xlsx?d=wc9c64f0d063f473d86b1c6c70607cfd6&csf=1&web=1&e=jVJ616)


# Question Log 

### Link:   [Question Log](https://rwhdinc-my.sharepoint.com/:x:/r/personal/swati_ajayan_trinetx_com/Documents/Query%20collaboration%20Page.xlsx?d=wbe8f3d89ea034b22b63be8e3cbb933a9&csf=1&web=1&e=OLctIg)

### Updates based on question log: ￼

|  |  |  |
| --- | --- | --- |
| **Query point ** | **Context examples ** | **Resolution ** |
| Is "tobacco exposure" treated like "passive exposure" and ignored?    | "Smoking status - Passive smoke exposure"  "No tobacco exposure." “Smoke exposure - Yes”  | Tobacco exposure and passive/secondhand smoking Should be ignored  |
| Does terms like Counseled or advised, along with smoking cessation be considered part of health education?  | “Counseled on smoking cessation” “Advice to stop smoking”  | Ignore all mentions of counseling, advise, cessation regarding to Smoking  |
| How to tag Tobacco Abuse, Nicotine Dependence and Tobacco use disorder will abuse, dependence and use be included in NER/Assertion label  | “Tobacco abuse” "Tobacco use disorder" “Nicotine Dependence - counseled on smoking cessation”  | **Part 1 (NER label)**- Annotate only the first word Tobacco, Nicotine (without use/disorder/ dependence) -- This only applies to SMOKING STATUS. Other labels (section header etc.) can be much longer **Part 2 (Assertion label)** - Smoking status in phrases like Tobacco/nicotine abuse, tobacco/nicotine disorder, tobacco/nicotine dependence can be annotated as Current Smoker. Unless in the sentence it's characterized as history of, hx, past, previous etc.  |
| When Chew is describing smokeless tobacco type, will chew be tagged as Substance type or ignored?  | "Smokeless tobacco: Former User. Types: Chew"  | Although we are ignoring smokeless tobacco as a smoking status, we do annotate chewing tobacco as Type.  |
| Should Frequency, Quantity and Duration labels always have a numeric value, or can we also consider terms like Every day, Occasional etc.?  | “Current every day smoker”   | Frequency, Quantity, and Duration do not have to be numerical. 'Every day', 'occasionally' can be annotated as frequency.  |
| Which is the correct assertion label in situation where patient denies smoking Never smoker or Unknown, if ever smoked?  | "patient denies smoking” "patient reports no tobacco use” "patient does not smoke"  | The assertion for smoking/tobacco should be "**Unknown, if ever smoked**" (not Never smoker -** never smoker will be only when it's explicitly mentioned** that patient has never been smoking)  |

# SBU - Additional comments

Please follow the General guidelines above and additionally the the specific guidelines below:

- in "Tobacco use" - only tag "tobacco" without "use"
- in "Tobacco: \<DATE\>; Use: 10 or more cigarettes" - tag tobacco as current smoker, and DATE as as Date
- in "Tobacco: \<DATE\>; Use: Never (less than 100 in l" - tag tobacco as never smoker, and DATE as Date
- in :  
"Tobacco  
Tobacco use: Former smoker, quit more than 30 days ago."
    - tag first “Tobacco” as section header, second Tobacco as "former smoker"
    - ignore tagging smoking status in such examples, but do tag Dates:  
- "Tobacco: \<DATE\>; Concerns about tobacco use in household:"  
- "Tobacco: \<DATE\>; Use: Refused tobacco status sc"  
- "Smoker in household: No"
- Keep ignoring nicotine when mentioned as a drug
- Keep ignoring smokeless tobacco in terms of smoking status
- in examples like "SMOKING: Never Smoked" - SMOKING can stay Section Header
- do not tag smoking type, duration, quantity or frequency if the assertion is someone else
- do not tag smoking type if it's a negation for example "doesn't smoke cigarettes"
- Current model is already trained (well-enough) on Section headers - please do not correct section header (unless the Reviewer requests it)
- EXCEPTION IN SBU - tag all the dates, examples:
    - *11/12/2025*
    - *March 2023*
    - *23.05.2025*
    - *May 7 2020*
    - *12-Jan-2022*
    - *2024*
    - *5/30*
    - Do not tag stand alone days or months, for example: “*Patient was tested on the 9th*”, “*Next visit in September*”
- RELATION MODEL
    - Relate Smoking Status with Date - only if there is a 100% certainty that the date belong to the status
    - IMPORTANT: Make sure you make link between the Smoking Status tag and Date and NOT between the Assertion tag and Date (this is clearly visible in the Relations sections the “blue” tag color on “Tobacco” and “smoker” in the example below representing Smoking Status tag

# UHCMC - Additional comments

### Section Headers

- ~~ALCOHOL /~~ SMOKING:

- Allergies

- Review of Systems

- Social History

- Recorded by

- Physical Exam
- Social History Problems
- Ordered by
- Medication
    - Allergies Medication are 2 separate headers:
- Occupation
- Family History
- SH
- SocHx
- PSH
- Marital History
- Physical Activity
- Current Meds
- Tobacco Screening


# Carilion - Additional comments

### General Comments

- Data seems to be pre-formatted, similarly to UHCMC, there are multiple white spaces that might point to section headers/sentence bounderies - this has to be taken into account during cleaning.
    - This is how the original text look like for example, note the white spaces:
- There are '?' characters that might point to section end/start
- Important to distinguish Section Header from actual smoking status for example:

“Social History” and “Tobacco Use” are Section\_Headers, “Smoking Status” and “Former Smoker” are Smoking\_Status

### Section Headers

- Social History
- Substance Use Topics
- History of Present Illness
- Medical History
- Past Surgical History
- Occupational History
- Tobacco comment
- Vaping Use (followed by “?”)
- Tobacco Use (followed by “?”)
- Smoking Status (followed by “?”)
- History Smoking Status (followed by “?”)
- Vaping Use (followed by “?”)
- Substance and Sexual Activity
- Assessment & Plan
- Main Topics
- Comment
- Substance Use Topics
- Family History
- Substance and Sexual Activity
- FH
- SH
- VACCINATIONS
- Current Meds
- Other Topics Concern
- Transportation needs
- Social History Narrative
