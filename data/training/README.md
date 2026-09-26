# RAG memory and behavior data

## Source-backed starter corpus

`rag_memory/` contains two manually curated `RawPage` pairs (`.md` + `.meta.json`) based on public municipal pages, checked on 2026-09-26. The RTEC page records the tariff and subscription values currently shown by RTEC, including the cited 31 March 2026 disposition. The Primăria page describes a historical SMS/QR pilot launched in March 2023; it must not be presented as proof that the service is currently available. Source URLs and retrieval timestamps are in the metadata.

The memory uses the paired-file layout used by I1 and can be loaded with `fetch.load_raw(Path("data/training/rag_memory"))`. It is a small, manually checked seed corpus, not a complete crawl. The app's `scripts/index.py` is still a C0 L1 stub, so adding these pages here does not by itself populate `data/index/app.sqlite` or make the running app retrieve them.

## Training files

- `rag_train.jsonl`: 8 evidence-grounded Romanian response examples from `rtec.md`.
- `rag_validation.jsonl`: 5 examples from the separate `proiecte.chisinau.md` site, including an abstention case. Keep this file out of training.
- `behavior_seed_train.jsonl` and `behavior_seed_validation.jsonl`: earlier invented format-pilot examples. They are synthetic and should not be mixed into factual training.

Each JSONL record uses Unsloth conversational `messages` and the app's `LLMAnswer` keys (`answer`, `citations`, `enough`). The source-site split avoids putting paraphrases of the same source into both partitions, but five validation examples are only a format check. This corpus is far too small to establish model quality or justify training an adapter. Keep changing facts in RAG; expand with reviewed, non-hidden documents from more sites before a training run. Exclude every URL in `data/golden/**` from generated training examples.

These documents and datasets are deliverable inputs; they do not select a base model or prove that a particular Unsloth checkpoint fits the available GPU. Use a trainable Transformers checkpoint for the chosen Gemma family model, rather than an inference-only GGUF.
