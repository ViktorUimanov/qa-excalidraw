"""Run a strict, complete assessment using the released Assay scanner.

Unlike onboarding, findings block this assessment even without a master baseline.
The completeness check compensates for the separately documented scanner bugs.
"""
from argparse import Namespace
from pathlib import Path
import json
import os
import subprocess
import sys
import time


def completeness_errors(run_dir, expected_cases, required_probes, min_cases=1):
    """Missing evidence is an unavailable assessment, never evidence of health."""
    errors = []
    actual = {}
    for p in (run_dir / 'cases').glob('*/evidence.json'):
        ev = json.loads(p.read_text())
        actual[ev['case_id']] = ev
    if len(actual) < min_cases or not expected_cases or set(actual) != set(expected_cases):
        errors.append({'case': None, 'reason': 'Executed case IDs do not match the required nonempty suite'})
    for cid, ev in actual.items():
        for phase in ('before', 'after'):
            if ev.get(f'probe_errors_{phase}') or not set(required_probes) <= set(ev.get(f'state_{phase}') or {}):
                errors.append({'case': cid, 'reason': f'Missing or failed {phase} state probe'})
        audit = ev.get('audit') or {}
        if not audit or audit.get('error') or not audit.get('a11y') or audit['a11y'].get('error'):
            errors.append({'case': cid, 'reason': 'Layout or accessibility audit unavailable'})
    pages_file = run_dir / 'scan/pages.json'
    if not pages_file.exists():
        errors.append({'case': None, 'reason': 'Screen scan evidence is missing'})
    else:
        pages = json.loads(pages_file.read_text())
        if len(pages) < 2:
            errors.append({'case': None, 'reason': 'Desktop/mobile scan is incomplete'})
        for page in pages:
            audit = page.get('audit') or {}
            if page.get('error') or not audit or audit.get('error') or not audit.get('a11y') or audit['a11y'].get('error'):
                errors.append({'case': None, 'reason': f"Scan audit unavailable: {page.get('viewport')}"})
    return errors


def main():
    from assay.cli import cmd_run
    from assay.config import load_profile, load_cases
    from assay.ci import connect, detect_context, comment_markdown, post_comment
    from assay.report import write_all

    root = Path(__file__).resolve().parent
    profile = load_profile(root)
    cases = load_cases(profile)
    ctx = detect_context()
    run_id = os.environ.get('ASSAY_AUDIT_RUN_ID') or time.strftime('%Y%m%d-%H%M%S') + '-strict'
    run_dir = root / 'runs' / run_id
    # This is release readiness, not the non-blocking first onboarding comparison.
    profile.gate.pop('first_analysis', None)
    profile.gate['new_code'] = False
    args = Namespace(project=str(root), profile_obj=profile, k=None, run_id=run_id,
                     out=str(root/'runs'), baseline=None, headed=False, no_start=False,
                     no_reset=False, no_judge=True, scan=True, no_scan=False,
                     scan_only=False, agent=False, ci=ctx)
    code = cmd_run(args)
    analysis = json.loads((run_dir/'analysis.json').read_text())
    errors = completeness_errors(run_dir, [c.id for c in cases], profile.probes, int(profile.gate.get("min_cases", 1)))
    exports = subprocess.run([sys.executable, str(root/'validate_exports.py'), str(run_dir)],
                             capture_output=True, text=True)
    print(exports.stdout, end='')
    if exports.returncode:
        print(exports.stderr, file=sys.stderr)
    audit = {'mode': 'strict release readiness', 'scanner': 'released Assay 0.3.0',
             'required_journeys': len(cases), 'required_probes': list(profile.probes),
             'completeness_errors': errors, 'export_validation_passed': exports.returncode == 0,
             'scope': '19 authored journeys; browser canvas app; no claim of exhaustive feature coverage'}
    (run_dir/'audit-summary.json').write_text(json.dumps(audit, indent=2))
    analysis['assessment'] = audit
    if errors:
        analysis['gate']['status'] = 'INCONCLUSIVE'
        analysis['gate']['conditions'].append({'name': 'Unavailable required evidence', 'actual': len(errors),
                                               'op': '=', 'threshold': 0, 'ok': False, 'soft': True})
    elif exports.returncode:
        analysis['gate']['status'] = 'FAILED'
        analysis['gate']['conditions'].append({'name': 'Export contents valid', 'actual': False,
                                               'op': '=', 'threshold': True, 'ok': False})
    (run_dir/'analysis.json').write_text(json.dumps(analysis, indent=2))
    write_all(run_dir, analysis)
    url = None
    if os.environ.get('ASSAY_HOST_URL'):
        server, key = connect(os.environ['ASSAY_HOST_URL'], ctx, profile.name)
        if server:
            response = server.upload(run_dir, {'project': key, 'title': profile.title, **ctx})
            url = response['url']
            print(f'Analysis published: {url}')
    text = comment_markdown(analysis, url, ctx, profile.name)
    (run_dir/'ci-comment.md').write_text(text)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write('### Strict assessment: existing findings count\n\n' + text)
    if ctx.get('pr'):
        print(post_comment(ctx, text, profile.name))
    print(f"STRICT QUALITY STATUS: {analysis['gate']['status']}")
    return {'PASSED': 0, 'FAILED': 1, 'INCONCLUSIVE': 2}[analysis['gate']['status']]


if __name__ == '__main__':
    raise SystemExit(main())
