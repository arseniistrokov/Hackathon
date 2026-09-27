#!/usr/bin/env python3
"""Единый скрипт запуска готового прототипа Chisinau Smart City Assistant с нейросетью.

Запуск:
    uv run python scripts/start_prototype.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNSLOTH_PYTHON = Path(r"C:\Users\Salam\.unsloth\studio\unsloth_studio\Scripts\python.exe")


def main() -> None:
    if not UNSLOTH_PYTHON.exists():
        print(f"[ERROR] Не найден интерпретатор Unsloth: {UNSLOTH_PYTHON}")
        sys.exit(1)

    adapter_dir = ROOT / "models" / "qlora_adapter"
    if not (adapter_dir / "adapter_model.safetensors").exists():
        print(f"[ERROR] Не найден адаптер модели в {adapter_dir}")
        sys.exit(1)

    print("=" * 65)
    print("🚀 Запуск прототипа Chisinau Municipal Assistant с QLoRA нейросетью")
    print("=" * 65)

    # 1. Запуск сервера инференса QLoRA (порт 8001)
    print("[1/2] Запуск сервера QLoRA-модели на http://127.0.0.1:8001...")
    model_proc = subprocess.Popen(
        [str(UNSLOTH_PYTHON), str(ROOT / "scripts" / "serve_qlora.py"), "--port", "8001"],
        cwd=str(ROOT),
    )

    # Ожидание готовности модели
    import httpx

    ready = False
    for _ in range(60):
        try:
            r = httpx.get("http://127.0.0.1:8001/health", timeout=1.0)
            if r.status_code == 200 and r.json().get("loaded"):
                ready = True
                break
        except Exception:
            pass
        time.sleep(1)

    if not ready:
        print("[ERROR] Сервер модели не ответил за 60 секунд.")
        model_proc.terminate()
        sys.exit(1)

    print("      Нейросеть готова к работе!")

    # 2. Запуск веб-приложения FastAPI + Frontend (порт 8000)
    print("[2/2] Запуск веб-сервера на http://127.0.0.1:8000...")
    env = os.environ.copy()
    env["LLM"] = "api"
    env["API_BASE_URL"] = "http://127.0.0.1:8001/v1"
    env["API_KEY"] = "local-qlora"
    env["API_MODEL"] = "qwen2.5-3b-qlora"
    env["LLM_TIMEOUT_S"] = "30.0"

    print("\n" + "=" * 65)
    print("🌐 Сайт доступен по адресу: http://127.0.0.1:8000/")
    print("   Документация API:        http://127.0.0.1:8000/docs")
    print("   Нейросеть (OpenAI API):  http://127.0.0.1:8001/v1")
    print("   Нажмите Ctrl+C для остановки обоих серверов.")
    print("=" * 65 + "\n")

    try:
        subprocess.run(
            ["uv", "run", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(ROOT),
            env=env,
        )
    finally:
        print("\nОстановка сервера модели...")
        model_proc.terminate()
        model_proc.wait(timeout=5)


if __name__ == "__main__":
    main()
