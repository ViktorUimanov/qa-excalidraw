# Assay: Excalidraw QA benchmark

The application is unchanged, pinned initially to upstream commit `3a317b55f508815d10a4c12acca99df30f026521`. Only `.assay/` and its own workflow are added.

## Scope

Ten authored UI journeys cover rectangle creation/reload, freehand undo/redo, exact text persistence, duplicate/delete, SVG/PNG/editable-scene download, scene import/reload, a narrow touch-enabled Chromium viewport and background persistence. Browser contexts are fresh per journey. Read-only probes inspect saved scene elements, saved preferences and theme; `allowed_changes` is limited to those probed values.

The profile uses the production build. Canvas interactions use the existing interactive canvas selector. The main menu uses its existing test ID because the current button has no accessible name. Other controls use their accessible roles/names. Download journeys use Firefox's normal file-download behavior; Chromium's native save picker is a separate coverage gap.

The bundled Assay scanner runs these authored journeys and automated sensors. Codex authors and troubleshoots this profile following Assay's shipped connect workflow; this is not evidence that the scanner independently discovered all application behavior. No AI judge/model is configured. Visual meaning, collaboration, cloud sharing, AI generation, native iOS, painting-specific brush engines, and full library/image workflows are outside this initial scope.

## Reproduce

```sh
corepack enable
yarn install --frozen-lockfile
yarn build:app:docker
# Use the Assay CLI supplied by the Assay plugin, or uvx --from its wheel.
assay doctor .assay
assay run .assay --scan
python3 .assay/validate_exports.py .assay/runs
```

`validate_exports.py` independently parses downloaded SVG, PNG and editable-scene files. It supplements Assay's download event/size/name assertions and runs as a separate CI check. It does not modify application data or code.

Raw reports, downloaded files, screenshots and local browser data are ignored by Git and are retained in the CI evidence artifact. No production users, real purchases, model credentials or cloud collaboration services are needed for this scope.

## Existing findings preserved

The first complete run produced 6 PASS / 4 FAIL / 0 INCONCLUSIVE. The four reload journeys (`drawing.rectangle_persists`, `drawing.text_persists`, `mobile.rectangle`, `settings.background`) fail the unchanged `no_errors` requirement on Chromium's `Permissions policy violation: unload is not allowed in this document.` The same console messages were reproduced with plain Playwright, without Assay instrumentation. All state/outcome assertions passed. These cases carry `known-bug`, as prescribed by the shipped onboarding workflow; their assertions and FAIL verdicts are preserved. No data loss or visible editing failure was demonstrated by this console finding.

Automatic accessibility findings include an unnamed main-menu button and unlabeled export controls. Automated ARIA/label/zoom findings require individual review before being counted as distinct confirmed user-facing bugs. The report's `100% of discovered screens` describes one discovered URL in a single-page app, not complete feature coverage.
