# Provenance Guard Planning Document

## 1. Detection Signals
We will use two distinct detection signals to classify content:

1. **Signal 1: Groq LLM Classifier (`llama-3.3-70b-versatile`)**
   - **What it measures:** Semantic coherence, stylistic flow, and contextual anomalies typical of LLMs (e.g., specific vocabulary like "delve," "tapestry," or overly structured argumentative paragraphs).
   - **Output:** A float between `0.0` (human) and `1.0` (AI).
   - **Blind spot:** It is vulnerable to prompt-injected "human-like" variations, such as deliberate typos or injected slang, which can trick the model into assessing it as human.

2. **Signal 2: Stylometric Heuristics**
   - **What it measures:** Sentence length variance and type-token ratio (vocabulary diversity). AI-generated text often exhibits highly uniform sentence structures and lower vocabulary diversity compared to humans.
   - **Output:** A float between `0.0` (human, high variance) and `1.0` (AI, low variance).
   - **Blind spot:** Formulaic or highly structured human writing (like technical manuals, legal text, or simple poetry with repetition) might exhibit low variance, leading to false positives.

**Combination:** The final confidence score will be an unweighted average of the two signals: `(Signal 1 + Signal 2) / 2`. 

## 2. Uncertainty Representation
A confidence score of `0.6` means the system detects some AI-like patterns, but it is not overwhelming evidence. We map the raw combined score to a calibrated score, giving the benefit of the doubt to the human writer to minimize false positives.

- **Likely human (`0.0` to `0.40`)**: The text shows high structural variance and lacks typical AI semantic markers.
- **Uncertain (`0.40` to `0.70`)**: The signals conflict (e.g., semantically reads like AI, but structurally varied) or are borderline.
- **Likely AI (`0.70` to `1.0`)**: Both signals strongly indicate uniformity and AI semantic markers.

## 3. Transparency Label Design
- **High-confidence AI:** "High-confidence AI: This content exhibits strong structural and semantic patterns typical of AI generation."
- **Uncertain:** "Uncertain: This content exhibits mixed signals. We cannot confidently determine if it is human-written or AI-generated."
- **High-confidence human:** "High-confidence human: This content exhibits natural stylistic variations and structures typical of human writing."

## 4. Appeals Workflow
- **Who can submit an appeal:** Any creator whose work has been flagged or labeled uncertain.
- **Information provided:** The content's unique `content_id` and the creator's `creator_reasoning` (e.g., explaining their writing style, ESL context, or drafting process).
- **System actions:** 
  1. The DB updates the `status` of the submission to `under_review`.
  2. The appeal and reasoning are logged to the structured audit log.
- **Human reviewer view:** A human reviewer opening the appeal queue would see the original text, the two independent signal scores, the final confidence score, and the creator's reasoning side-by-side to make a final attribution decision.

## 5. Anticipated Edge Cases
- **Technical/Legal Documentation:** A human writing a highly structured privacy policy or software documentation. The stylometric signal will likely score it very close to `1.0` due to low sentence length variance and repeated vocabulary. If Groq also finds it formulaic, it might trigger a false positive "Likely AI."
- **Heavy ESL Editing:** A non-native speaker drafting a story and passing it heavily through an AI grammar checker. The semantics might remain human, but the sentence structures may become artificially uniform, landing in the "Uncertain" bucket.

---

## Architecture

**Narrative:** 
When a submission is made (`POST /submit`), the text passes independently through the Groq signal and the Stylometric signal. Both scores are averaged to produce a confidence score, which maps to one of three transparency labels. The decision is written to an SQLite Audit Log, and the result is returned to the client. If a creator contests the label (`POST /appeal`), they submit their reasoning along with the `content_id`. The database updates the content status to `under_review` and logs the appeal, preparing it for human review.

```text
       [POST /submit]
             |
             v
     +-------+-------+
     |               |
[Signal 1: Groq] [Signal 2: Stylometrics]
     |               |
     +-------+-------+
             v
     [Confidence Scoring]
             |
             v
    [Transparency Label] ----> [Audit Log (SQLite)]
             |
             v
         [Response]
```

## AI Tool Plan
- **M3 (submission endpoint + first signal):** I will use the *Detection Signals* and *Architecture diagram* sections to generate the Flask app skeleton, SQLite setup, and the `analyze_with_groq` function. I will test Groq independently, then wire it into `/submit` and `/log`.
- **M4 (second signal + confidence scoring):** I will use the *Detection Signals*, *Uncertainty Representation*, and *Architecture diagram* to generate the `analyze_with_stylometrics` function and the confidence averaging logic. I'll test the combined scoring on predefined test cases.
- **M5 (production layer):** I will use the *Transparency Label Design*, *Appeals Workflow*, and *Architecture diagram* to map the score to the correct label text, build `POST /appeal`, and implement Flask-Limiter for rate limiting. I will test the endpoints end-to-end to ensure the audit log accurately captures everything.
