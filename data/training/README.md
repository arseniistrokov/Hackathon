# RAG memory and behavior data

## Coverage of Annex 1

`rag_memory/` now contains source-backed pages from the Annex 1 site list. `rag_coverage.json` inventories all 40 configured domains, the captured page URLs, and per-site availability. During the 2026-09-26 crawl, substantive paired pages were captured for 34 sites; the other entries are explicitly marked as unavailable, inactive, or limited to an application/navigation shell. A coverage entry does not imply the site is fully indexed. Several captured documents are old, dynamic, or only provide a limited view; check each page's metadata and source before answering time-sensitive questions.

The RTEC tariff and Botanica audience schedule were manually curated from their official pages. The 2023 Primăria SMS/QR article is historical and does not establish current availability. The Commerce 2026 tax amount is dated and must be verified against the current official decision. Some crawl results were rejected because they contained unrelated SEO spam; those pages are not included.

The memory uses I1 paired-file layout (`.md` plus `.meta.json`) and can be loaded with `fetch.load_raw(Path("data/training/rag_memory"))`. The app's `scripts/index.py` remains a C0 L1 stub, so these files do not yet populate the runtime SQLite index or make the running app retrieve them.

## Training files

- `rag_train.jsonl` contains evidence-grounded response examples from multiple Annex 1 sources, including the earlier RTEC examples.
- `rag_validation.jsonl` includes held-out sources, the earlier historical Proiecte SMS/QR examples, and abstention examples for pages that exposed no substantive text. Keep it out of training.
- `rag_coverage.json` is the 40-site coverage inventory.
- `behavior_seed_train.jsonl` and `behavior_seed_validation.jsonl` are earlier synthetic format-pilot examples; do not mix them with factual training.

Each JSONL record uses Unsloth conversational `messages` and the app's `LLMAnswer` keys (`answer`, `citations`, `enough`). The corpus is still a small seed dataset and cannot establish model quality or justify an adapter training run. Facts that change belong in RAG and need refreshing from their official sources. Exclude every URL in `data/golden/**` from generated training examples.

These files do not select a base model or show that a particular Unsloth checkpoint fits the available GPU. Use a trainable Transformers checkpoint for the chosen Gemma family model, rather than an inference-only GGUF.
