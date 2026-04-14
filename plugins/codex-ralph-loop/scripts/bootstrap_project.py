#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


IGNORE_NAMES = {'__pycache__', '.DS_Store'}
IGNORE_SUFFIXES = {'.pyc'}

GITIGNORE_BLOCK = '''# Codex Ralph loop
.codex-loop/history/*
!.codex-loop/history/.gitkeep
.codex-loop/reviews/*
!.codex-loop/reviews/.gitkeep
.codex-loop/evals/*
!.codex-loop/evals/.gitkeep
.codex-loop/artifacts/*
!.codex-loop/artifacts/.gitkeep
.codex-loop/state.json
.codex-loop/ralph-loop.json
.codex-loop/logs/iteration-*.log
.codex-loop/logs/ralph-hook.log
.codex-loop/context/current-state.md
.codex-loop/context/handoff.md
.codex-loop/context/events.jsonl
.codex-loop/preflight/status.json
.codex-loop/preflight/REPORT.md
output/html/*
output/pdf/*
'''


def should_ignore(path: Path) -> bool:
    return path.name in IGNORE_NAMES or path.suffix in IGNORE_SUFFIXES


def sync_tree(src: Path, dst: Path, force: bool) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for child in sorted(src.iterdir()):
        if should_ignore(child):
            continue
        target = dst / child.name
        if child.is_dir():
            sync_tree(child, target, force)
            continue
        copy_file(child, target, force)


def copy_file(src: Path, dst: Path, force: bool) -> None:
    if dst.exists() and not force:
        raise FileExistsError(f'refusing to overwrite existing file: {dst}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser(description='Seed a project with SummitHarness runtime files.')
    parser.add_argument('target', nargs='?', default='.', help='Project directory to initialize')
    parser.add_argument('--force', action='store_true', help='Overwrite existing runtime files')
    args = parser.parse_args()

    plugin_root = Path(__file__).resolve().parents[1]
    template_root = plugin_root / 'templates' / 'project'
    target_root = Path(args.target).expanduser().resolve()

    if not template_root.exists():
        print(f'missing template directory: {template_root}', file=sys.stderr)
        return 2

    target_root.mkdir(parents=True, exist_ok=True)

    sync_tree(template_root / '.codex', target_root / '.codex', args.force)
    sync_tree(template_root / '.codex-loop', target_root / '.codex-loop', args.force)
    sync_tree(template_root / 'docs', target_root / 'docs', args.force)
    sync_tree(plugin_root / 'design-reference-packs', target_root / '.codex-loop' / 'design' / 'reference-packs', args.force)

    for name in [
        'codex_ralph.py',
        'import_hwpx_preview.py',
        'ralph_session.py',
        'context_engine.py',
        'preflight.py',
        'asset_registry.py',
        'review_submission_pdf.py',
        'review_submission_source.py',
        'render_markdown_submission.py',
    ]:
        copy_file(template_root / 'scripts' / name, target_root / 'scripts' / name, args.force)

    copy_file(template_root / 'ralph.sh', target_root / 'ralph.sh', args.force)

    for rel in [
        'ralph.sh',
        'scripts/codex_ralph.py',
        'scripts/import_hwpx_preview.py',
        'scripts/ralph_session.py',
        'scripts/context_engine.py',
        'scripts/preflight.py',
        'scripts/asset_registry.py',
        'scripts/review_submission_pdf.py',
        'scripts/review_submission_source.py',
        'scripts/render_markdown_submission.py',
        '.codex/hooks/ralph_stop.py',
    ]:
        target = target_root / rel
        if target.exists():
            target.chmod(0o755)

    gitignore_path = target_root / '.gitignore'
    existing = gitignore_path.read_text(encoding='utf-8') if gitignore_path.exists() else ''
    if '# Codex Ralph loop' not in existing:
        gitignore_path.write_text(
            (existing.rstrip() + '\n\n' if existing.strip() else '') + GITIGNORE_BLOCK + '\n',
            encoding='utf-8',
        )

    print(f'Initialized SummitHarness runtime in {target_root}')
    print('Next steps:')
    print('  1. Run python3 scripts/preflight.py run')
    print('  2. Lock .codex-loop/prd/PRD.md, SUMMARY.md, and .codex-loop/design/DESIGN.md to the real goal')
    print('  3. Pick or customize a reference pack in .codex-loop/design/reference-packs/ and record it in DESIGN.md')
    print('  4. If this is a proposal or submission flow, edit docs/submissions/proposal.md first')
    print('  5. Run python3 scripts/review_submission_source.py docs/submissions/proposal.md')
    print('  6. Render with python3 scripts/render_markdown_submission.py once the source gate passes')
    print('  7. Add real local build, lint, test, or screenshot commands in .codex-loop/config.json')
    print('  8. Use python3 scripts/context_engine.py refresh --source bootstrap to build the first handoff packet')
    print('  9. Run ./ralph.sh --once or start /ralph-loop inside Codex')
    print('     -> the first Ralph run will replace the bootstrap template tasks with a project-specific task graph')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
