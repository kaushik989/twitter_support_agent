# Golden Evaluation Set: Sampling & Labelling Methodology

## Overview
The Golden Evaluation Set consists of **200 hand-curated and annotated customer support queries** extracted from real `@AppleSupport` interactions in the Thought Vector Twitter Customer Support dataset (`thoughtvector/customer-support-on-twitter`).

---

## 1. Sampling Strategy
To guarantee realistic evaluation reflecting actual enterprise customer support operations, the 200 examples were sampled using a **stratified multi-criterion sampling strategy**:

1. **Brand Filtering**: Filtered to single-turn and multi-turn inbound customer queries directed to `@AppleSupport` with paired historical brand responses.
2. **Noise & Length Filtering**: Filtered out empty tweets, bot spam, raw image links without text, and queries under 10 characters.
3. **Intent Diversity**: Stratified across 8 data-derived intent categories to ensure coverage of both common queries (software updates, how-to) and high-risk edge cases (locked Apple ID, hardware damage, billing disputes).
4. **Complexity & Emotion Variance**: Included diverse query types ranging from calm feature questions ("How to turn off location services?") to frustrated complaints ("My phone screen turned black after update, fix this garbage!").

---

## 2. Intent Distribution Summary

| Intent Category | Golden Set Count | Target Auto-Handle Eligibility | Primary Escalation Trigger |
| :--- | :---: | :---: | :--- |
| `TECHNICAL_TROUBLESHOOTING` | 41 | Conditional | Exhausted basic steps or complex diagnostic |
| `OTHER_OUT_OF_SCOPE` | 47 | Escalate | Ambiguous query / non-standard intent |
| `FEEDBACK_COMPLAINT` | 36 | Escalate | Customer frustration & anger management |
| `HARDWARE_REPAIR_WARRANTY` | 28 | Escalate | Requires physical repair / Genius Bar |
| `FEATURE_HOW_TO` | 25 | Auto-Handle | Standard settings guidance |
| `ORDER_SHIPPING_DELIVERY` | 10 | Auto-Handle | General order tracking |
| `ACCOUNT_APPLE_ID` | 9 | Escalate | Private credentials / PII verification |
| `BILLING_SUBSCRIPTIONS` | 4 | Escalate | Financial charge lookup / refund request |
| **TOTAL** | **200** | **40% Auto / 60% Escalate** | |

---

## 3. Ground Truth Labelling Protocol

Each record in `golden_set.json` contains five core ground-truth annotations:

1. **`gold_intent`**: The primary intent classified according to the 8-class taxonomy.
2. **`gold_escalate`**: Boolean decision (`true` for human escalation tier, `false` for automated AI reply).
3. **`gold_escalation_reason`**: Explicit natural language explanation detailing *why* the message must be escalated (e.g., PII risk, hardware inspection, customer hostility, or low confidence) or auto-handled.
4. **`gold_reference_reply`**: High-quality, brand-aligned ground truth response serving as the gold standard for reply generation scoring.
5. **`human_quality_score`**: Integer rating (1–5) assigned by a human annotator evaluating the historical brand reply quality, used as the benchmark to validate **LLM-as-Judge Alignment**.

---

## 4. Edge Cases & Annotation Guidelines

- **Multi-Intent Queries**: When a customer query contains both a complaint and a technical question (e.g., *"iOS 11 update is trash, my battery drains in 1 hour!"*), the safety-critical intent (`FEEDBACK_COMPLAINT` / escalation trigger) takes precedence over standard troubleshooting.
- **Over-Escalation in Historical Data**: Historical brand support agents frequently defaulted to *"Send us a DM"* even for trivial public questions. In our golden ground truth, we strictly label standard public inquiries (e.g. settings locations) as `AUTO_HANDLE` to prevent unnecessary human support overhead.
