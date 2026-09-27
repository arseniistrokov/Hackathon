# Qwen2.5 dataset — draft snapshot

This folder contains the last completed export: 300 training rows and 30 validation rows in chat `messages` JSONL format. Its manifest records 10 training document URLs and 20 held-out document URLs. It does not cover all 40 Annex 1 sites in training.

Structural, citation-reference, passage-hash, and split checks passed for this export. These checks do not establish semantic correctness of questions, translations, or missing-answer labels. Rows remain marked `human_review: unreviewed`; review is needed before training.

The later rebuild expanded the candidate split to 26 training documents and 4 held-out documents, but was interrupted at the user's request. The files here are still the earlier completed export, not that expanded rebuild. Current generator code therefore does not describe the split used by this snapshot; consult `manifest.json` for the exported data.

Target: Pasha's existing Qwen2.5 checkpoint; exact checkpoint and size were not supplied. Local `gemma3-nexo` was used to generate questions and translations, not as the target for training. No model training was started.

Related files:

- `../build_nexo_v2.py`: generation script (historical filename), configured for the later split.
- `../validate_nexo_v2.py`: offline dataset validator.
- `../nexo_v2/generation_cache.jsonl`: intermediate generation cache, including interrupted work; not an additional training dataset.

The generator depends on the project corpus under `data/training/rag_memory` and application chunking/prompt code. It does not refresh websites. Exact reproduction also depends on those inputs and the local model; the saved export is the snapshot to inspect.

Dataset generation remains stopped. This commit only preserves work; it does not authorize resuming generation or training.
