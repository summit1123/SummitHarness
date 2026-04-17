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
    parser = argparse.ArgumentParser(description='프로젝트에 SummitHarness 런타임 파일을 초기화합니다.')
    parser.add_argument('target', nargs='?', default='.', help='초기화할 프로젝트 디렉터리')
    parser.add_argument('--force', action='store_true', help='이미 있는 런타임 파일을 덮어씁니다')
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
        'summit_intake.py',
        'summit_research.py',
        'summit_start.py',
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
        'scripts/summit_intake.py',
        'scripts/summit_research.py',
        'scripts/summit_start.py',
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

    print(f'SummitHarness 런타임을 초기화했습니다: {target_root}')
    print('다음 단계:')
    print('  1. `python3 scripts/preflight.py run`으로 환경 점검을 실행합니다.')
    print('  2. 먼저 사용자에게 이번 런에서 무엇을 하고 싶은지와 어디서 멈추고 싶은지 확인합니다.')
    print('  3. Codex 안에서는 `/ralph-start`로 온보딩을 시작하고, CLI라면 `python3 scripts/summit_start.py init --profile <proposal-only|planning-only|build-direct|idea-to-service> --goal "<goal>"` 를 사용합니다.')
    print('  4. `.codex-loop/workflow/ONBOARDING.md`를 채우고, 필요하면 `.codex-loop/workflow/IDEAS.md`도 정리합니다.')
    print('  5. `python3 scripts/summit_intake.py init --mode <proposal|prd|implementation|product-ui>` 를 실행합니다.')
    print('  6. 요청자 Q&A를 `.codex-loop/intake/ANSWERS.md`에 기록하고 `.codex-loop/intake/APPROVAL.md`에서 승인을 잠급니다.')
    print('  7. `python3 scripts/summit_research.py init --mode <proposal|prd|implementation|product-ui>` 를 실행합니다.')
    print('  8. 단계형 리서치 계획을 작성하고 `.codex-loop/research/APPROVAL.md`에서 승인을 잠급니다.')
    print('  9. 승인된 리서치 방향에 맞춰 `.codex-loop/prd/PRD.md`, `SUMMARY.md`, `.codex-loop/design/DESIGN.md`를 확정합니다.')
    print(' 10. `.codex-loop/design/reference-packs/`에서 레퍼런스 팩을 고르거나 커스터마이징하고 `DESIGN.md`에 기록합니다.')
    print(' 11. 제안서/제출 흐름이라면 먼저 `docs/submissions/proposal.md`를 편집합니다.')
    print(' 12. `python3 scripts/review_submission_source.py docs/submissions/proposal.md`로 원고 리뷰를 돌립니다.')
    print(' 13. 원고 게이트를 통과하면 `python3 scripts/render_markdown_submission.py`로 렌더링합니다.')
    print(' 14. `.codex-loop/config.json`에 실제 local build, lint, test, screenshot 명령을 추가합니다.')
    print(' 15. `python3 scripts/context_engine.py refresh --source bootstrap`로 첫 handoff packet을 만듭니다.')
    print(' 16. 기본 실행은 `./ralph.sh`입니다. `--once`는 smoke 또는 디버그용 1회 실행으로만 사용하고, 실제 Ralph 런은 `./ralph.sh` 또는 `/ralph-loop`로 시작합니다.')
    print('     -> 첫 Ralph 실행은 bootstrap template task를 프로젝트 전용 task graph로 교체합니다. 단, intake와 research 승인이 잠겨 있어야 합니다.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
