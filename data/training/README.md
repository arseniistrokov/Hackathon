# Gemma 4 E4B mobile behavior dataset

These JSONL files are a **synthetic format and pipeline pilot**, not a factual Chișinău dataset and not a release-ready fine-tuning corpus. All towns, institutions, documents, schedules, and values in examples are invented. Do not present these examples as real municipal information.

Each row uses Unsloth conversational `messages` and the app's `LLMAnswer` output keys (`answer`, `citations`, `enough`). It demonstrates Romanian and Russian responses, evidence-only answers, citation selection, ignoring instructions embedded in passages, and abstaining when evidence is absent. Validation rows are separate; never merge them into training.

- `behavior_seed_train.jsonl`: 8 synthetic training examples.
- `behavior_seed_validation.jsonl`: 4 separate synthetic validation examples.

## Real training data requirements

At dataset creation time `data/raw` contained no crawled pages and `data/index` had no populated index. Therefore this seed contains no verified Chișinău facts. Before training a useful adapter, collect and review real public corpus examples from non-hidden documents, exclude every URL in `data/golden/**`, deduplicate and split validation by source document/site. Keep factual lookup in RAG; train only response behavior. This seed is suitable only for checking that the chat format and training pipeline work; it is far too small to establish model quality.

Target runtime artifact: `unsloth/gemma-4-E4B-it-qat-mobile-GGUF`, local snapshot `6a6e7121b977cefd85daa8fbc538fa485e7e8b1b`. The local Q2_K_XL GGUF is for inference. Fine-tune from an Unsloth-compatible Hugging Face checkpoint, then export a quantized mobile-compatible model.
