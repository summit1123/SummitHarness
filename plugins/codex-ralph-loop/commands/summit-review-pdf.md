# /summit-review-pdf

Markdown 원고 점검을 통과한 뒤 최종 PDF 첨부본을 점검합니다.

1. 원고 리뷰가 이미 정리되었는지 확인합니다.
2. Run `python3 scripts/review_submission_pdf.py "output/pdf/proposal.pdf"` or the final attachment path.
3. `.codex-loop/artifacts/pdf-review/`에 생성된 리포트를 확인합니다.
4. 파일명, 용량, 패키징 문제를 수정합니다.
5. `python3 scripts/context_engine.py refresh --source pdf-review`로 컨텍스트를 갱신합니다.
