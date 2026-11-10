#!/usr/bin/env python3
"""Source/JSON/docs checks; does not claim macOS UI or model verification."""
from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[1]
for relative in ['desktop/knowledge.json', 'skills/agent-learning-loop/references/prompt-recipes.json']:
    assert isinstance(json.loads((root / relative).read_text()), dict)
for path in root.rglob('*.md'):
    if any(part.startswith('.') for part in path.relative_to(root).parts[:-1]):
        continue
    for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if re.match(r'^[a-z]+:', link) or link.startswith('#'):
            continue
        assert (path.parent / link.split('#')[0]).exists(), (path, link)
for required in ['SelectionAssistant.swift', 'SelectionCore.swift', 'PromptPreparation.swift', 'RefinementLaunch.swift', 'SelectionTests.swift', 'render-icons.swift']:
    assert (root / 'desktop/native' / required).is_file()
print('Source layout, JSON and relative documentation links passed; no model calls.')
