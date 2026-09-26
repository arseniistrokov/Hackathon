# Gemma 4 E4B mobile behavior dataset

These JSONL files are a **synthetic format and pipeline pilot**, not a factual Chișinău dataset and not a release-ready fine-tuning corpus. All towns, institutions, documents, schedules, and values in examples are invented. Do not present these examples as real municipal information.

Each row uses Unsloth conversational `messages` and the app's `LLMAnswer` output keys (`answer`, `citations`, `enough`). It demonstrates Romanian and Russian responses, evidence-only answers, citation selection, ignoring instructions embedded in passages, and abstaining when evidence is absent. Validation rows are separate; never merge them into training.

- `behavior_seed_train.jsonl`: 8 synthetic training examples.
- `behavior_seed_validation.jsonl`: 4 separate synthetic validation examples.

## Real training data requirements

At dataset creation time `data/raw` contained no crawled pages and `data/index` had no populated index. Therefore this seed contains no verified Chișinău facts. Before training a useful adapter, collect and review real public corpus examples from non-hidden documents, exclude every URL in `data/golden/**`, deduplicate and split validation by source document/site. Keep factual lookup in RAG; train only response behavior. This seed is suitable only for checking that the chat format and training pipeline work; it is far too small to establish model quality.

Current runtime selection in Unsloth Studio: `Qwen3.5-4B-MTP-GGUF · Q8_0` (as shown in the user-provided screenshot). This GGUF is an inference artifact. For fine-tuning, select a Transformers checkpoint such as `unsloth/Qwen3.5-4B`, then export a GGUF for inference. Unsloth lists about 10 GB VRAM for 4B bf16 LoRA and 5 GB for 2B; its guide discourages QLoRA for Qwen3.5. The available local GPU is an RTX 5060 Laptop with 8 GB VRAM, so this 4B training setup may not fit.
