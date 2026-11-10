#!/usr/bin/env python3
"""Local, explicit domain preferences compiled to the existing live recipe format.

No model calls, clipboard access, app monitoring, folder scanning or skill code
execution. Inferred feedback produces a candidate, never a confirmed preference.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / 'references' if (ROOT / 'references/domain-methods.json').is_file() else ROOT / 'skills/agent-learning-loop/references'
LIBRARY = REFERENCES / 'domain-methods.json'
BASE = REFERENCES / 'prompt-recipes.json'
HOME = Path.home() / '.codex/agent-learning-loop'
MARKER = '_snapper_domain_profile'
SOURCE_BASE = '_snapper_source_base'


def read(path):
    return json.loads(Path(path).read_text())


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def atomic(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')
            f.flush(); os.fsync(f.fileno())
        os.chmod(temp, 0o600); os.replace(temp, path)
    finally:
        if os.path.exists(temp): os.unlink(temp)


def load_preferences(path):
    if not Path(path).exists():
        return {'schema_version': 1, 'preferences': {}, 'feedback': {}}
    value = read(path)
    if value.get('schema_version') != 1 or not isinstance(value.get('preferences'), dict) or not isinstance(value.get('feedback'), dict):
        raise ValueError('Invalid preferences; refusing to reset or overwrite them')
    return value


def domain_and_method(library, domain, method):
    d = next((x for x in library['domains'] if x['id'] == domain), None)
    m = next((x for x in library['methods'] if x['id'] == method), None)
    if d is None or m is None or method not in d['methods']:
        raise ValueError('Unknown domain/method combination')
    return d, m


def remember(state, library, domain, method, origin):
    domain_and_method(library, domain, method)
    if origin not in ('explicit-user', 'confirmed-candidate'):
        raise ValueError('Only an explicit user statement or confirmed candidate may become a preference')
    if origin == 'confirmed-candidate' and not state['feedback'].get(domain + '/' + method, {}).get('candidate'):
        raise ValueError('No candidate to confirm')
    state['preferences'][domain] = {'method': method, 'status': 'confirmed', 'origin': origin, 'updated_at': now()}


def feedback(state, library, domain, method, signal):
    domain_and_method(library, domain, method)
    key = domain + '/' + method
    item = state['feedback'].setdefault(key, {'accept': 0, 'reject': 0, 'undo': 0, 'candidate': False})
    item[signal] += 1
    # A small local heuristic, not evidence of preference or task quality.
    item['candidate'] = item['accept'] >= 3 and item['accept'] > item['reject'] + item['undo']
    item['updated_at'] = now()
    return item


def compile_catalog(base, state, library):
    if base.get('schema_version') != 1:
        raise ValueError('Unsupported catalog')
    result = copy.deepcopy(base)
    result.setdefault(SOURCE_BASE, copy.deepcopy(read(BASE)['recipes']))
    # Preserve every unrelated recipe and customization. Reject ID collisions.
    retained = base_recipes(result)
    ids = {r['id'] for r in retained}
    retained_by_id = {r['id']:r for r in retained}
    previous_source = {r['id']:r for r in result[SOURCE_BASE]}
    replaced = set()
    profiles = []
    known_sources = {s['id'] for s in library['sources'] if s.get('status') == 'read'}
    for d in library['domains']:
        pref = state['preferences'].get(d['id'])
        confirmed = pref and pref.get('status') == 'confirmed'
        if not confirmed and not state.get('recommendations_enabled', False): continue
        method_id = pref['method'] if confirmed else d.get('default_method')
        if not method_id: continue
        _, m = domain_and_method(library, d['id'], method_id)
        if not confirmed and (m.get('status') != 'source-reviewed' or not m['source_ids'] or not all(s in known_sources for s in m['source_ids'])):
            continue
        native_id = d.get('native_recipe_id',d['id'])
        local_base = None
        if native_id in ids:
            if native_id == d['id'] or native_id not in ['learning','coding','design','research','writing']:
                raise ValueError('Custom recipe ID collision: ' + native_id)
            local_base = retained_by_id[native_id]
            if local_base != previous_source.get(native_id):
                raise ValueError('Method overlay conflicts with local recipe edit: ' + native_id)
            replaced.add(native_id)
        origin = pref['origin'] if confirmed else 'curated-recommendation'
        profiles.append({'id': native_id, 'title': d.get('native_title', d['title']) + ' · ' + m['short_title'] + ('' if confirmed else '·建议'),
            'keywords': d['keywords'], 'intent': d['intent'],
            'deliverables': m['deliverables'], 'checks': m['checks'],
            'questions': [], 'source_ids': m['source_ids'],
            MARKER: {'domain':d['id'],'method': m['id'], 'origin': origin, 'library_revision': library['revision'], 'routing_priority': d.get('routing_priority',0), 'base_recipe':local_base}})
    # Specific task families win keyword ties over broad writing/research lanes.
    profiles.sort(key=lambda r: -r[MARKER]['routing_priority'])
    result['recipes'] = profiles + [r for r in retained if r['id'] not in replaced]
    validate_catalog(result)
    digest = hashlib.sha256(json.dumps(result['recipes'], ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    result['revision'] = 'domain-' + library['revision'] + '-' + digest
    return result


def base_recipes(catalog):
    values=[]
    for r in catalog['recipes']:
        if not r.get(MARKER):values.append(r)
        elif r[MARKER].get('base_recipe'):values.append(r[MARKER]['base_recipe'])
    order={r['id']:i for i,r in enumerate(catalog.get(SOURCE_BASE,values))}
    return sorted(values,key=lambda r:order.get(r['id'],len(order)))


def refresh_base(incoming, existing):
    """Three-way refresh: preserve unrelated/local edits and fail on conflicts."""
    previous = existing.get(SOURCE_BASE)
    if previous is None:
        raise ValueError('No previous source snapshot; review local edits before refreshing')
    old = {r['id']: r for r in previous}
    local = {r['id']: r for r in base_recipes(existing)}
    fresh = {r['id']: r for r in incoming['recipes']}
    merged = []
    for identifier in dict.fromkeys([*fresh, *local]):
        a, b, c = old.get(identifier), local.get(identifier), fresh.get(identifier)
        if b == a: chosen = c
        elif c == a or b == c: chosen = b
        elif a is None and c is None: chosen = b
        else: raise ValueError('Recipe refresh conflicts with local edit: ' + identifier)
        if chosen is not None: merged.append(copy.deepcopy(chosen))
    result = copy.deepcopy(incoming); result['recipes'] = merged
    result[SOURCE_BASE] = copy.deepcopy(incoming['recipes'])
    return result


def validate_catalog(catalog):
    recipes = catalog.get('recipes', [])
    if not 1 <= len(recipes) <= 20 or not any(r.get('id') == 'general' for r in recipes):
        raise ValueError('Native catalog needs a general fallback and at most 20 recipes')
    ids = [r.get('id') for r in recipes]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate recipe IDs')
    for r in recipes:
        if not isinstance(r.get('id'), str) or not 1 <= len(r['id']) <= 64 or not r.get('title') or not r.get('intent'):
            raise ValueError('Invalid native recipe identity')
        for name, limit in [('keywords', 30), ('deliverables', 5), ('checks', 5), ('questions', 2), ('source_ids', 30)]:
            values = r.get(name)
            if not isinstance(values, list) or len(values) > limit or not all(isinstance(x, str) and x and len(x) <= 600 for x in values):
                raise ValueError('Invalid recipe field: ' + name)


def apply_catalog(output, catalog):
    validate_catalog(catalog)
    output = Path(output)
    if output.exists():
        # A stable last-version backup, private and local. No prompt history.
        atomic(output.with_name(output.name + '.before-domain-profiles.json'), read(output))
    atomic(output, catalog)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--state', type=Path, default=HOME / 'domain-preferences.json')
    sub = ap.add_subparsers(dest='command', required=True)
    sub.add_parser('list')
    for name in ['remember', 'feedback']:
        p = sub.add_parser(name); p.add_argument('--domain', required=True); p.add_argument('--method', required=True)
        if name == 'remember': p.add_argument('--origin', choices=['explicit-user', 'confirmed-candidate'], required=True)
        else: p.add_argument('--signal', choices=['accept', 'reject', 'undo'], required=True)
    p = sub.add_parser('forget'); p.add_argument('--domain', required=True)
    p = sub.add_parser('recommendations'); p.add_argument('setting', choices=['on', 'off'])
    p = sub.add_parser('compile'); p.add_argument('--base', type=Path, default=HOME / 'prompt-recipes.json')
    p.add_argument('--output', type=Path, default=HOME / 'prompt-recipes.json'); p.add_argument('--apply', action='store_true')
    args = ap.parse_args(); library = read(LIBRARY); state = load_preferences(args.state)
    if args.command == 'list': print(json.dumps(state, ensure_ascii=False, indent=2)); return
    if args.command == 'compile':
        catalog = compile_catalog(read(args.base if args.base.exists() else BASE), state, library)
        if args.apply:
            apply_catalog(args.output, catalog)
            print(json.dumps({'applied': str(args.output), 'recipes': len(catalog['recipes']), 'revision': catalog['revision'], 'restart_required': False}, ensure_ascii=False))
        else: print(json.dumps(catalog, ensure_ascii=False, indent=2))
        return
    if args.command == 'remember': remember(state, library, args.domain, args.method, args.origin)
    elif args.command == 'forget': state['preferences'].pop(args.domain, None)
    elif args.command == 'recommendations': state['recommendations_enabled'] = args.setting == 'on'
    else: feedback(state, library, args.domain, args.method, args.signal)
    atomic(args.state, state)
    print(json.dumps({'saved': str(args.state), 'command': args.command}, ensure_ascii=False))


if __name__ == '__main__':
    main()
