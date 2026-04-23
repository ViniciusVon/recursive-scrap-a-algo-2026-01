"""
Fixtures compartilhadas.

- `client` devolve um `TestClient` do FastAPI com o SQLite redirecionado
  para um arquivo temporário; cada teste começa com banco vazio.
- Como o `DB_PATH` é capturado por valor dentro de `src.db`, patchamos
  o módulo diretamente.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    db_tmp = tmp_path / "teste.db"

    # Patch antes do import do app — qualquer `from src.db import X`
    # que aconteça em routes/services depende desse caminho.
    import src.db as db_mod

    monkeypatch.setattr(db_mod, "DB_PATH", str(db_tmp))

    # Recarrega main para que o lifespan use o DB_PATH patchado na
    # inicialização.
    from backend import main as main_mod

    importlib.reload(main_mod)
    with TestClient(main_mod.app) as c:
        yield c
