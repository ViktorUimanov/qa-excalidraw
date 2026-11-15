# Excalidraw: strict, scoped QA assessment

The Excalidraw application is unchanged at upstream `3a317b55f508815d10a4c12acca99df30f026521`. Only QA configuration, fixtures and the QA workflow are changed. Original analysis #32 remains the initial 10-journey onboarding result.

## What is tested

The expanded suite has **19 journeys**:

- Shapes, freehand, exact text, background preference and saved geometry after reload.
- Undo/redo, selective duplicate/delete, erasing/undo, grouping/ungrouping and multiline Unicode persistence.
- SVG, PNG and editable-scene downloads, plus scene import/reload.
- Image import, binary persistence in IndexedDB and actual green image pixels on the rendered canvas after reload.
- A narrow, touch-enabled Chromium browser viewport.
- Explicit accessibility assessments of Library, Preferences, image export and font controls.
- A dedicated Chromium reload-console compatibility journey.

Five read-only probes observe saved elements, preferences, theme, image records and library records in fresh browser contexts. Every journey requires all declared state probes to be available. PNG validation decodes the downloaded pixels and rejects a blank/uniform image, alongside file-format validation. This is a simple visibility oracle, not a general visual-design judge.

The main menu uses its existing test ID because it has no accessible name. Canvas input uses the existing interactive canvas selector. Other controls use roles/names. Firefox exercises its normal download path; Chromium's native save picker is not tested. The mobile case uses desktop-browser emulation and mouse-generated canvas input; no physical-device claim is made.

## Why the console finding is separated

Chromium prints `Permissions policy violation: unload is not allowed in this document.` for three actual app `unload` registrations. The messages were independently reproduced and traced. They do not establish a broken drawing feature; five immediate-reload spot checks retained the rectangle.

Functional journeys allow **only that exact message**, while keeping exceptions, other console errors, failed first-party requests and state checks strict. Sensors still record the message. A separate `compat.reload_console` journey retains the strict `no_errors` assertion and its `known-bug` tag. Broad expected-failure tags were removed from the actual drawing/persistence journeys, so an unrelated state regression cannot be exempted with the old console issue.

## Strict readiness, not permissive onboarding

The workflow uses the **released Assay 0.3.0 scanner**, pinned to public release commit `0f28e57a0876d8d6e844ea09472290cc1bb92e1d`, through `.assay/strict_ci.py`.

This wrapper runs the complete suite and scan without first-analysis or new-code relaxation. It checks that the required suite ran, every required before/after probe is present, and every final/scan accessibility audit completed. Missing evidence makes the assessment INCONCLUSIVE. Confirmed blocking findings make it FAILED. It then publishes the actual strict report through Assay's normal GitHub OIDC client and retains evidence in Actions.

A separate local engine branch fixes the underlying false-pass paths and passes its regression tests. Those core engine changes are **not deployed** or bundled into this repository. The completeness guard and narrow compatibility scenario protect this assessment while keeping the released scanner identifiable.

```sh
corepack enable
yarn install --frozen-lockfile
yarn build:app:docker
# Assay must be importable in this Python environment.
python .assay/strict_ci.py
```

## Interpretation and remaining gaps

Accessibility assertions fail on real unnamed controls, export labels and ARIA structure. Severity and user impact still require contextual triage. Reports contain case-failure records as well as underlying sensor issues; their sum is not the number of distinct bugs.

One discovered URL does not measure feature coverage. Collaboration, cloud sharing, AI generation, actual mobile devices, the native save picker and many advanced editor combinations remain untested. No model/judge is configured. Security and AI grades are not proof that those domains were assessed.

Seven explicitly visited UI surfaces also retain complete axe node details, screenshots and incomplete/manual-review results under `review-surfaces/`. The Firefox export capture omits an additional native accessibility snapshot that crashes when combined with axe; its full axe evidence and screenshot remain required. a clean list of automated violations does not certify accessibility. The suite and its assertions are authored by Codex; this is not a demonstration of autonomous discovery of every product behavior.
