"""Preserve complete axe nodes and manual-review results for explicitly visited UI states."""
from pathlib import Path
import json


def capture(profile, run_dir):
    from assay.runner import Browsers, app_running
    from assay.sensors import AXE_JS, AXE_TAGS

    folder = run_dir / 'review-surfaces'
    folder.mkdir(exist_ok=True)
    errors = []
    summary = []
    with app_running(profile, folder) as down:
        if down:
            return [{'case': None, 'reason': f'Review surfaces unavailable: {down}'}]
        with Browsers(profile) as browsers:
            for name in ('home', 'menu', 'preferences', 'library', 'more-tools', 'fonts', 'export'):
                context, _ = browsers.new_context('files' if name == 'export' else 'desktop')
                page = context.new_page()
                page.set_default_timeout(10000)
                try:
                    page.goto(profile.base_url)
                    page.get_by_role('button', name='Rectangle', exact=True).wait_for()
                    if name in ('menu', 'preferences'):
                        page.get_by_test_id('main-menu-trigger').click()
                        if name == 'preferences':
                            page.get_by_role('menuitem', name='Preferences', exact=True).click()
                    elif name == 'library':
                        page.get_by_role('button', name='Library', exact=True).click()
                    elif name == 'more-tools':
                        page.get_by_role('button', name='More tools', exact=True).click()
                    elif name == 'fonts':
                        page.get_by_role('button', name='Text', exact=True).click()
                        page.locator('canvas.interactive').click(position={'x': 500, 'y': 350})
                        page.keyboard.type('Independent font control audit')
                        page.keyboard.press('Escape')
                    elif name == 'export':
                        page.get_by_role('button', name='Rectangle', exact=True).click()
                        page.mouse.move(500, 350)
                        page.mouse.down()
                        page.mouse.move(750, 500, steps=12)
                        page.mouse.up()
                        page.get_by_test_id('main-menu-trigger').click()
                        page.get_by_role('menuitem', name='Export image...', exact=True).click()
                    page.wait_for_timeout(700)
                    page.evaluate(AXE_JS)
                    data = page.evaluate("""async(tags) => {
                        const r=await axe.run(document,{runOnly:{type:'tag',values:tags},resultTypes:['violations','incomplete']});
                        return {violations:r.violations,incomplete:r.incomplete};
                    }""", AXE_TAGS)
                    (folder/f'{name}.json').write_text(json.dumps(data, indent=2))
                    (folder/f'{name}-accessibility.txt').write_text(page.locator('body').aria_snapshot())
                    page.screenshot(path=str(folder/f'{name}.png'))
                    summary.append({'surface': name, 'violations': [{'rule': v['id'], 'nodes': len(v['nodes'])}
                                                                   for v in data['violations']],
                                    'manual_review_rules': [v['id'] for v in data['incomplete']]})
                except Exception as e:
                    errors.append({'case': None, 'reason': f'Review surface {name}: {type(e).__name__}: {e}'})
                finally:
                    context.close()
    (folder/'summary.json').write_text(json.dumps({'surfaces': summary, 'errors': errors}, indent=2))
    return errors
