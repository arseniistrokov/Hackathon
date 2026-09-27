"""Validate Qwen2.5 SFT files, source provenance, split leakage, and dataset mix."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app.contracts.models import LLMAnswer  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_nexo_v2 import near, source_guards  # noqa: E402

OUT = ROOT / "data/training/qwen2_5_v1"
QUESTION = re.compile(r"<question>\s*(.*?)\s*</question>", re.S)
PASSAGES = re.compile(r"^\[(\d+)\] \((.*?)\)\n(.*?)(?=^\[\d+\] \(|\Z)", re.M | re.S)


def fail(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def duplicate_count(questions: list[str], threshold: float = 0.78) -> tuple[int, list[list[str]]]:
    examples = []
    total = 0
    for i, question in enumerate(questions):
        for previous in questions[:i]:
            if near(question, previous, threshold):
                total += 1
                if len(examples) < 12:
                    examples.append([previous, question])
    return total, examples


def main() -> None:
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_by_hash = {}
    for document in manifest["corpus_split"]["train_document_urls"]:
        fail(document not in manifest["corpus_split"]["validation_document_urls"], "Document split overlaps")
    for split in ("train", "validation"):
        spec = manifest["distribution"][split]
        path = OUT / f"{split}.jsonl"
        raw = path.read_bytes()
        fail(hashlib.sha256(raw).hexdigest() == spec["sha256"], f"Stale {split} SHA256")
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
        metadata = spec["rows_meta"]
        fail(len(rows) == len(metadata) == spec["rows"], f"{split} row/metadata count mismatch")
        fail(
            len({json.dumps(row, sort_keys=True, ensure_ascii=False) for row in rows}) == len(rows),
            f"Exact duplicate complete examples in {split}",
        )
        questions = []
        langs, enoughs, kinds, citation_counts, cross = Counter(), Counter(), Counter(), Counter(), Counter()
        urls, row_hashes = set(), set()
        for index, (row, meta) in enumerate(zip(rows, metadata, strict=True), 1):
            messages = row.get("messages")
            fail(
                isinstance(messages, list)
                and [m.get("role") for m in messages] == ["system", "user", "assistant"],
                f"Invalid messages roles at {split}:{index}",
            )
            lang = meta["language"]
            fail(lang in {"ru", "ro"}, f"Invalid language at {split}:{index}")
            user = messages[1]["content"]
            match = QUESTION.search(user)
            fail(match is not None and bool(match.group(1).strip()), f"Empty question at {split}:{index}")
            question = match.group(1).strip()
            questions.append(question)
            evidence_block = re.search(r"(?m)^<passages>\s*(.*?)\s*</passages>\s*$", user, re.S)
            fail(evidence_block is not None, f"Missing passages at {split}:{index}")
            parsed = list(PASSAGES.finditer(evidence_block.group(1).strip()))
            fail(bool(parsed), f"Empty passage list at {split}:{index}")
            fail(
                "".join(item.group(0) for item in parsed) == evidence_block.group(1).strip(),
                f"Malformed passage text at {split}:{index}",
            )
            numbers = [int(item.group(1)) for item in parsed]
            fail(
                numbers == list(range(1, len(numbers) + 1)),
                f"Passage IDs are not contiguous at {split}:{index}",
            )
            passage_texts = [item.group(3).strip() for item in parsed]
            source_rows = meta.get("sources", [])
            fail(len(source_rows) == len(parsed), f"Provenance count mismatch at {split}:{index}")
            for source, text in zip(source_rows, passage_texts, strict=True):
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                fail(digest == source["text_sha256"], f"Source passage hash mismatch at {split}:{index}")
                source_by_hash[digest] = source
                fail(source["url"].startswith(("http://", "https://")), f"Non-site source at {split}:{index}")
                urls.add(source["url"].rstrip("/"))
            raw_answer = messages[2]["content"]
            answer_json = json.loads(raw_answer)
            fail(
                set(answer_json) == {"answer", "citations", "enough"},
                f"Unexpected answer schema keys at {split}:{index}",
            )
            answer = LLMAnswer.model_validate(answer_json)
            fail(
                len(set(answer.citations)) == len(answer.citations), f"Duplicate citation at {split}:{index}"
            )
            fail(
                set(answer.citations) <= set(numbers),
                f"Citation references missing passage at {split}:{index}",
            )
            fail(bool(answer.answer.strip()) == answer.enough, f"Answer/enough mismatch at {split}:{index}")
            fail(bool(answer.citations) == answer.enough, f"Citation/enough mismatch at {split}:{index}")
            kind = meta["kind"]
            fail(meta.get("human_review") == "unreviewed", f"Missing review provenance at {split}:{index}")
            if answer.enough:
                fail(bool(answer.citations), f"Answered sample lacks citations at {split}:{index}")
                targets = [source_rows[n - 1] for n in answer.citations]
                quotes = meta.get("source_quotes") or [meta.get("source_quote")]
                if kind in {"answered", "heldout"}:
                    fail(len(answer.citations) == 1 and quotes[0], f"Missing source quote at {split}:{index}")
                    quote = quotes[0]
                    cited_text = passage_texts[answer.citations[0] - 1]
                    fail(quote in cited_text, f"Target quote absent from cited source at {split}:{index}")
                    if lang == "ro":
                        fail(
                            " ".join(answer.answer.split()) == " ".join(quote.split()),
                            f"Romanian answer is not verbatim source text at {split}:{index}",
                        )
                elif kind == "multi_document":
                    fail(
                        len(answer.citations) == 2 and len(quotes) == 2,
                        f"Multi-source answer needs two mapped citations at {split}:{index}",
                    )
                    for quote, n in zip(quotes, answer.citations, strict=True):
                        fail(
                            quote in passage_texts[n - 1],
                            f"Multi-source quote not in cited passage at {split}:{index}",
                        )
                        if lang == "ro":
                            fail(
                                quote in answer.answer,
                                f"Multi-source Romanian answer lost quote at {split}:{index}",
                            )
                if lang == "ru":

                    def digits(text: str) -> str:
                        return "".join(re.findall(r"\d", text))

                    for quote in quotes:
                        fail(
                            not digits(quote) or digits(quote) in digits(answer.answer),
                            f"Russian translation changed source digits at {split}:{index}",
                        )
                cross[lang] += any(source["language"] == "ro" for source in targets) and lang == "ru"
            else:
                fail(answer.answer == "" and answer.citations == [], f"Invalid abstention at {split}:{index}")
                if kind == "hard_negative":
                    target = meta.get("target_fact_source")
                    fail(
                        target is not None and target["quote"],
                        "Hard negative lacks its hidden target provenance",
                    )
                    fail(
                        target["quote"] not in " ".join(passage_texts),
                        f"Hard-negative target quote leaked into evidence at {split}:{index}",
                    )
            expected_lang = bool(re.search(r"[А-Яа-яЁё]", question))
            fail((lang == "ru") == expected_lang, f"Question language mismatch at {split}:{index}")
            langs[lang] += 1
            enoughs[answer.enough] += 1
            kinds[kind] += 1
            citation_counts[len(answer.citations)] += 1
            row_hashes.add(
                hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            )
        near_count, near_pairs = duplicate_count(questions)
        spec["checked_distribution"] = {
            "languages": dict(langs),
            "enough": dict(enoughs),
            "cross_language_ru_from_ro": cross["ru"],
            "types": dict(kinds),
            "citation_count": dict(citation_counts),
            "near_duplicate_questions_jaccard_0_78": near_count,
            "near_duplicate_examples": near_pairs,
        }
        spec["questions"] = questions
        spec["source_urls"] = sorted(urls)
        print(split, spec["rows"], spec["checked_distribution"])

    train = manifest["distribution"]["train"]
    validation = manifest["distribution"]["validation"]
    fail(
        not (set(train["source_urls"]) & set(validation["source_urls"])),
        "Train and validation share a source URL",
    )
    old_blocked, guards = source_guards()
    fail(
        not (set(train["source_urls"]) & {u.rstrip("/") for u in old_blocked}),
        "Train includes an old validation or golden source URL",
    )
    for question in train["questions"]:
        fail(
            not any(near(question, g["question"], 0.70) for g in guards if g["question"]),
            f"Train question is too close to old validation/golden: {question}",
        )
    train_q = train["questions"]
    leak_count = sum(near(question, old, 0.78) for question in validation["questions"] for old in train_q)
    validation["near_duplicate_vs_train"] = leak_count
    fail(leak_count == 0, "Near-duplicate question across train/validation")

    report_path = OUT / "validation_report.json"
    report_path.write_text(
        json.dumps(
            {
                "model": manifest["question_generation_model"],
                "train_rows": train["rows"],
                "validation_rows": validation["rows"],
                "train": train["checked_distribution"],
                "validation": validation["checked_distribution"],
                "train_validation_near_duplicates": leak_count,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"All structural, citation, provenance, and split checks passed. Report: {report_path}")


if __name__ == "__main__":
    main()
