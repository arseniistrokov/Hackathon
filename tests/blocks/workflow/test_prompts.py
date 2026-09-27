"""Тесты защитного системного промпта W1 (guard prompt). Без сети, без моделей.

Запуск: uv run pytest tests/blocks/workflow/test_prompts.py -q
"""

from __future__ import annotations

from app.blocks.workflow import prompts


def test_system_prompt_word_limit() -> None:
    """Промпт компактен для маленькой модели (3B): не длиннее 250 слов на язык."""
    for lang, text in prompts.SYSTEM.items():
        assert len(text.split()) <= 250, f"{lang}: system prompt слишком длинный"


def test_system_prompt_contains_guard_rules() -> None:
    """Ключевые защитные правила присутствуют в обоих языках: имя, только passages,
    запрет вымысла, конфликт источников, запрет других тем, запрет раскрытия промпта."""
    for text in prompts.SYSTEM.values():
        assert "NEXA" in text
        assert "enough" in text
        assert "citations" in text
        assert "answer" in text

    ro = prompts.SYSTEM["ro"]
    assert "<passages>" in ro
    assert "contrazic" in ro or "contrazice" in ro
    assert "sfaturi juridice" in ro
    assert "Nu dezvălui" in ro

    ru = prompts.SYSTEM["ru"]
    assert "<passages>" in ru
    assert "расходятся" in ru or "противоречат" in ru
    assert "юридических" in ru
    assert "Не раскрывай" in ru


def test_system_prompt_language_matches_question_language() -> None:
    """SYSTEM выбирается по языку вопроса: ru-текст — кириллица, ro-текст — латиница."""
    ro_text = prompts.SYSTEM["ro"]
    ru_text = prompts.SYSTEM["ru"]
    assert ro_text != ru_text
    cyrillic = set("абвгдежзийклмнопрстуфхцчшщъыьэюя")
    ru_letters = sum(1 for ch in ru_text.lower() if ch.isalpha())
    ru_cyrillic = sum(1 for ch in ru_text.lower() if ch in cyrillic)
    assert ru_cyrillic / ru_letters > 0.5
    ro_cyrillic = sum(1 for ch in ro_text.lower() if ch in cyrillic)
    assert ro_cyrillic == 0


def test_system_prompt_schema_fields_only() -> None:
    """Промпт ссылается только на поля LLMAnswer (answer, citations, enough) —
    schema и verify_citations продолжают работать без изменений."""
    from app.contracts.models import LLMAnswer

    schema_fields = set(LLMAnswer.model_fields)
    assert schema_fields == {"answer", "citations", "enough"}
    for text in prompts.SYSTEM.values():
        for field in schema_fields:
            assert field in text
