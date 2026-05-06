# Summit Document Editorial

Inspired by the `DESIGN.md` workflow collected in
[`awesome-design-md`](https://github.com/VoltAgent/awesome-design-md), this
preset is for proposals, PRDs, contest submissions, strategy memos, and other
reviewer-first documents.

Preset: document-editorial

## Intent

Write and render documents that feel reviewed by a serious operator, not poured
out of a demo generator.

## Principles

1. Information first
- Use tables, comparisons, timelines, and evidence panels when structure matters.
- Decorative cards, badges, and ornamental shapes do not count as information.

2. Editorial density
- Every page needs a narrative job.
- Empty lower halves, lonely callout boxes, and repetitive summary cards fail the bar.

3. Reviewer language
- Write for judges, buyers, operators, or approvers.
- Avoid assistant voice, tutorial voice, and self-referential UI narration.

4. Current vs future
- Separate what already exists from what is proposed next.
- Implementation proof supports the argument, but must not swallow the document.

5. Visual restraint
- Black or near-black body text.
- One restrained accent family for hierarchy only.
- Strong rules, table heads, captions, and page rhythm over gradients or blobs.

## Layout Guidance

- Prefer full-width content bands with clear section spacing.
- If content is comparative, render it as a table before considering cards.
- Use diagrams only when the relationship cannot be understood as prose plus a table.
- Keep captions factual and short.

## Tone

- Formal, direct, and specific.
- Prefer `합니다 / 입니다` in Korean proposal writing.
- Replace vague claims with named evidence, scope, or operating assumptions.

## Avoid

- “This document shows...”
- “This page explains...”
- generic hero cards
- four tiny summary cards floating in empty space
- decorative circles, chips, and bento spam
- screenshots without a reason to exist
- filler metrics, fake authority, fake market numbers

## Render Preference

- Source of truth: Markdown
- Review gate: source review first, rendered review second
- Final artifact: PDF only after the Markdown source and design contract are aligned
