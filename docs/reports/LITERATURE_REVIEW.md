# Literature Review Notes

This chapter supports the report sections for Introduction and Literature.

## 1. Civic Grievance Digitization

Government grievance systems often struggle with high manual routing overhead and inconsistent complaint quality. Image-first reporting and structured workflows reduce ambiguity and improve triage speed.

## 2. Vision-Language Models for Civic Scenes

General-purpose vision-language models can identify broad scene context but may underperform on local civic cues without deterministic safeguards. Hybrid pipelines that combine VLM narration with rule-based scoring improve reliability for constrained civic taxonomies.

## 3. Local Inference and Privacy

Local inference via on-prem model runtimes reduces data exposure and can satisfy stricter governance requirements where cloud transfer is restricted. The tradeoff is tighter GPU/memory budgeting and operational observability needs.

## 4. Hybrid Deterministic + LLM Pipelines

A practical pattern for public systems is:

1. Vision extraction.
2. Deterministic rule scoring.
3. Optional small-model reasoning for edge ambiguity.
4. Templated drafting for output consistency.

This pattern minimizes hallucination risk compared with pure end-to-end generation.

## 5. Workflow Governance and Explainability

Status-history trails, role-based controls, and notification logs are critical for trust in civic workflows. Explainable metadata (confidence, rationale, method) supports triage and accountability.

## 6. References

- FastAPI documentation: https://fastapi.tiangolo.com
- React documentation: https://react.dev
- MongoDB documentation: https://www.mongodb.com/docs
- Ollama documentation: https://ollama.com
- Pydantic documentation: https://docs.pydantic.dev
