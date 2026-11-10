"""Rule from CLAUDE.md: ai/, questions/ and systems/ never import pygame."""
import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LOGIC_FILES = [p for folder in ("ai", "questions", "systems") for p in (ROOT / folder).rglob("*.py")]


@pytest.mark.parametrize("path", LOGIC_FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_pygame_import(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        assert not any(n.split(".")[0] == "pygame" for n in names), f"{path.name} imports pygame"
