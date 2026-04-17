# /summit-review-doc

렌더링이나 최종 제출 전에 Markdown 원고를 먼저 점검합니다.

1. 실제 원고 파일을 확인합니다. 보통 `docs/submissions/proposal.md`입니다.
2. Run `python3 scripts/review_submission_source.py docs/submissions/proposal.md`.
3. `.codex-loop/artifacts/source-review/`에 생성된 리포트를 확인합니다.
4. 레이아웃만이 아니라 원고 자체를 수정합니다.
5. `python3 scripts/context_engine.py refresh --source source-review`로 컨텍스트를 갱신합니다.
