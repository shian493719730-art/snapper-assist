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
LIBRARY = ROOT / 'skills/agent-learning-loop/references/domain-methods.json'
BASE = ROOT / 'skills/agent-learning-loop/references/prompt-recipes.json'
HOME = Path.home() / '.codex/agent-learning-loop'
MARKER = '_snapper_domain_profile'


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
    # Preserve every unrelated recipe and customization. Reject ID collisions.
    retained = [r for r in result['recipes'] if not r.get(MARKER)]
    ids = {r['id'] for r in retained}
    profiles = []
    for d in library['domains']:
        pref = state['preferences'].get(d['id'])
        if not pref or pref.get('status') != 'confirmed': continue
        _, m = domain_and_method(library, d['id'], pref['method'])
        if d['id'] in ids: raise ValueError('Custom recipe ID collision: ' + d['id'])
        profiles.append({'id': d['id'], 'title': d['title'] + ' · ' + m['short_title'],
            'keywords': d['keywords'], 'intent': d['intent'],
            'deliverables': m['deliverables'], 'checks': m['checks'],
            'questions': [], 'source_ids': m['source_ids'],
            MARKER: {'method': m['id'], 'origin': pref['origin'], 'library_revision': library['revision']}})
    result['recipes'] = profiles + retained
    validate_catalog(result)
    digest = hashlib.sha256(json.dumps(result['recipes'], ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    result['revision'] = 'domain-' + library['revision'] + '-' + digest
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
    else: feedback(state, library, args.domain, args.method, args.signal)
    atomic(args.state, state)
    print(json.dumps({'saved': str(args.state), 'command': args.command}, ensure_ascii=False))


if __name__ == '__main__':
    main()
