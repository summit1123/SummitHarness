# SummitHarness User Flow

## 한 줄 요약

사용자는 짧은 명령만 실행하고, 하네스는 내부에서 환경 점검, 제출용 PDF 검토, 컨텍스트 압축, loop 실행, 평가, handoff 갱신을 반복합니다.

현재 이 저장소는 첫 runnable loop slice를 검증하는 단계이므로, `current-state.md`와 `handoff.md`가 같은 상태를 말하는지 함께 확인해야 합니다.

## 1. 설치

사용자:

```bash
git clone https://github.com/summit1123/SummitHarness.git
cd SummitHarness
python3 install.py
```

내부 처리:

1. plugin bundle을 `~/.codex/plugins/codex-ralph-loop`에 복사
2. `~/.agents/plugins/marketplace.json` 갱신
3. `~/.codex/config.toml`에서 `codex_hooks = true` 보장
4. `~/.codex/hooks.json`에 Stop dispatcher 설치
5. 개인 스킬이 있으면 `~/.agents/skills/`에 연결

사용자 체감:

- Codex에서 plugin/skills/commands를 사용할 수 있게 됨
- 경우에 따라 Codex 재시작 필요

## 2. 대상 프로젝트 bootstrap

사용자:

```bash
python3 ~/.codex/plugins/codex-ralph-loop/scripts/bootstrap_project.py .
```

내부 처리:

- `.codex-loop/` 생성
- `scripts/codex_ralph.py` 생성
- `scripts/context_engine.py` 생성
- `scripts/preflight.py` 생성
- `scripts/asset_registry.py` 생성
- `scripts/review_submission_pdf.py` 생성
- `scripts/ralph_session.py` 생성
- `.codex/commands/`와 hook script 생성
- `.gitignore`에 runtime ignore 추가

사용자 체감:

- 이 repo가 SummitHarness-aware 상태가 됨

## 3. 환경 점검

사용자:

```bash
python3 scripts/preflight.py run
```

내부 처리:

- Codex CLI, git, python, node 계열 툴 확인
- hook 활성화 여부 확인
- rmcp_client, Figma 흔적 확인
- `OPENAI_API_KEY`, ffmpeg 등 media 관련 힌트 확인
- 결과를 `.codex-loop/preflight/status.json`, `REPORT.md`에 저장

사용자 체감:

- 지금 바로 돌릴 수 있는지, 뭐가 막히는지 바로 알 수 있음

## 4. 컨텍스트 압축

사용자:

```bash
python3 scripts/context_engine.py refresh --source bootstrap
```

내부 처리:

- PRD, tasks, latest state, logs, review 결과, 승인 자산 읽기
- durable facts / open questions 반영
- `current-state.md`와 `handoff.md` 생성
- `events.jsonl`에 refresh 기록

운영자는 여기서 `current-state.md`를 먼저 보고, 그 다음 `handoff.md`가 그 상태를 정확히 요약하는지 확인합니다.

사용자 체감:

- 긴 로그를 다 읽지 않고도 `handoff.md`만 보면 다음 행동을 이해할 수 있음

## 5. 제출용 PDF 점검

사용자:

```bash
python3 scripts/review_submission_pdf.py path/to/proposal.pdf
```

내부 처리:

- 파일 형식, 용량, 파일명 제약 점검
- 가능하면 `pdfinfo`, `pdftotext`로 메타데이터와 텍스트 preview 추출
- 결과를 `.codex-loop/artifacts/pdf-review/*.json`, `*.md`에 저장
- 다음 Ralph run 전에 고쳐야 할 blocker/warning 정리

사용자 체감:

- 제출 첨부파일이 조건을 어기는지 바로 알 수 있음
- PDF 내용이 현재 PRD/요약과 어긋나면 loop를 다시 돌리기 전에 잡을 수 있음

## 6. 실제 loop 실행

### 외부 worker loop

사용자:

```bash
./ralph.sh -n 6
```

내부 처리:

1. `handoff.md` 포함 prompt 생성
2. worker 실행
3. deterministic checks 실행
4. read-only review gate 실행
5. 결과를 `logs/`, `history/`, `reviews/`, `state.json`에 저장
6. iteration 뒤 context refresh

### same-session hook loop

사용자:

```text
/ralph-loop "..." --completion-promise "<promise>COMPLETE</promise>" --max-iterations 20
```

내부 처리:

1. `ralph-loop.json`에 state 기록
2. assistant가 종료하려 할 때 Stop hook 발동
3. hook이 completion / blocked / decide / max-iteration 판정
4. 완료 아니면 continuation prompt를 다시 넣음
5. context refresh도 같이 수행

## 7. 사용자가 보는 주요 파일

- `.codex-loop/preflight/REPORT.md`: 환경 상태
- `.codex-loop/artifacts/pdf-review/`: 제출용 PDF 점검 결과
- `.codex-loop/context/handoff.md`: 다음 best step
- `.codex-loop/context/current-state.md`: handoff 근거가 되는 최신 상태
- `.codex-loop/tasks.json`: 현재 작업 그래프
- `.codex-loop/logs/LOG.md`: iteration 요약
- `.codex-loop/reviews/`: 리뷰 게이트 결과
- `.codex-loop/assets/registry.json`: 승인된 시각 자산 목록

## 8. 디자인/자산 흐름

사용자는 필요할 때 이미지/영상/Figma 자산을 생성하거나 가져온 뒤 registry에 기록할 수 있습니다.

예:

```bash
python3 scripts/asset_registry.py add   --kind image   --path assets/hero-v1.png   --source imagegen   --status approved   --title "Hero v1"
```

그 다음 context refresh를 하면, 다음 iteration부터는 그 자산이 handoff packet에 반영됩니다.

## 9. 이 구조의 핵심

SummitHarness는 transcript를 계속 길게 먹이는 방식이 아니라:

- repo state 저장
- 필요한 것만 압축
- 다음 iteration에 handoff packet만 재주입

이 구조로 움직입니다.

그래서 사용자는 긴 세션에서도 "지금 어디까지 왔는지"를 계속 확인할 수 있습니다.
