import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('strict_ci', Path(__file__).parents[1]/'strict_ci.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def healthy(tmp_path):
    directory=tmp_path/'cases'/'sample';directory.mkdir(parents=True)
    evidence={'case_id':'sample','state_before':{'elements':[],'theme':'light'},'state_after':{'elements':[],'theme':'light'},'audit':{'overflowX':False,'a11y':{'violations':[]}}}
    path=directory/'evidence.json';path.write_text(json.dumps(evidence))
    scan=tmp_path/'scan';scan.mkdir()
    (scan/'pages.json').write_text(json.dumps([{'viewport':v,'audit':evidence['audit']} for v in ('desktop','mobile')]))
    return path,evidence


def test_complete_assessment_is_accepted(tmp_path):
    healthy(tmp_path)
    assert module.completeness_errors(tmp_path,['sample'],['elements','theme']) == []


def test_axe_exception_is_unavailable_not_healthy(tmp_path):
    path,ev=healthy(tmp_path);ev['audit']['a11y']={'error':'audit crashed','violations':[]};path.write_text(json.dumps(ev))
    assert module.completeness_errors(tmp_path,['sample'],['elements','theme'])


def test_missing_state_probe_is_not_silently_ignored(tmp_path):
    path,ev=healthy(tmp_path);del ev['state_after']['theme'];path.write_text(json.dumps(ev))
    assert module.completeness_errors(tmp_path,['sample'],['elements','theme'])


def test_empty_or_truncated_suite_is_rejected(tmp_path):
    healthy(tmp_path)
    assert module.completeness_errors(tmp_path,[],['elements','theme'])
    assert module.completeness_errors(tmp_path,['sample'],['elements','theme'],min_cases=2)


def test_missing_mobile_scan_is_rejected(tmp_path):
    healthy(tmp_path);(tmp_path/'scan/pages.json').write_text('[]')
    assert module.completeness_errors(tmp_path,['sample'],['elements','theme'])
