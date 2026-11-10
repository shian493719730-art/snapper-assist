#!/usr/bin/env python3
"""Local discovery, provenance and breadth-first review planning. No network or model calls."""
import argparse
from collections import Counter, defaultdict, deque
from datetime import date
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT/'references' if (ROOT/'references/discovery-index.json').is_file() else ROOT/'skills/agent-learning-loop/references'
STAGES = {'indexed', 'section-reviewed', 'body-reviewed'}
ALIASES = {
    '学术': ['academic', 'research'], '文献': ['literature', 'research'],
    '科研': ['scientific', 'research'], '数据': ['data', 'postgres', 'sql'],
    '数据库': ['postgres', 'sql', 'supabase'], '设计': ['design', 'ui', 'visual'],
    '视频': ['video', 'remotion'], '移动端': ['expo', 'mobile'],
    '复习': ['study', 'tutoring', 'lesson'], '写作': ['writing', 'editing', 'proofread'],
    '自动化': ['automation', 'workflow', 'agent'], '工作流': ['workflow', 'flow'],
    '上下文': ['context', 'memory'], '营销': ['marketing', 'sales'],
    '安全': ['security', 'audit'], '评估': ['eval', 'testing'],
    '产品': ['product', 'discovery'], '知识库': ['knowledge', 'memory', 'retrieval'],
}


def read(path):
    return json.loads(Path(path).read_text())


def validate(d):
    errors = []
    if d.get('schema_version') != 1:
        errors.append('unsupported-schema')
    groups = {k: {x['id']: x for x in d.get(k, [])} for k in ['sources', 'cases']}
    for k, values in groups.items():
        if len(values) != len(d.get(k, [])):
            errors.append('duplicate-'+k)
    paths = set()
    for s in d.get('sources', []):
        if not s.get('license', {}).get('scope') or not s.get('overview_review', {}).get('scope'):
            errors.append(s['id']+':source-provenance')
        if not s.get('url', '').startswith('https://'):
            errors.append(s['id']+':source-url')
    for c in d.get('cases', []):
        cid = c['id']; key = (c.get('source_id'), c.get('path'))
        if key in paths:
            errors.append(cid+':duplicate-path')
        paths.add(key)
        if c.get('source_id') not in groups['sources']:
            errors.append(cid+':unknown-source')
        if not c.get('url', '').startswith('https://') or not c.get('native_labels'):
            errors.append(cid+':case-provenance')
        r = c.get('review', {})
        if r.get('stage') not in STAGES or not r.get('scope') or not r.get('checked_on'):
            errors.append(cid+':review-scope')
        if c.get('execution', {}).get('status') != 'not-run':
            # Runtime evidence belongs to a separate scoped experiment, not a discovery snapshot.
            errors.append(cid+':unsupported-runtime-claim')
        a = c.get('artifact', {})
        if a.get('type') in ['tree', 'blob']:
            if not isinstance(a.get('sha'), str) or not re.fullmatch('[0-9a-f]{40}', a.get('sha', '')):
                errors.append(cid+':artifact-sha')
            if r.get('stage') != 'indexed':
                if not r.get('blob_sha') or not r.get('file_path') or r.get('observed_artifact_sha') != a.get('sha'):
                    errors.append(cid+':review-version')
                ranges = r.get('read_ranges', [])
                end = 0
                for span in ranges:
                    if not 0 <= end <= span['start'] < span['end'] <= r.get('characters', 0):
                        errors.append(cid+':read-ranges')
                    end = span['end']
                if not ranges:
                    errors.append(cid+':missing-read-ranges')
                if r.get('stage') == 'body-reviewed' and ranges != [{'start': 0, 'end': r.get('characters')}]:
                    errors.append(cid+':incomplete-body')
    return errors


def inventory(d):
    return {'revision': d['revision'], 'sources': len(d['sources']), 'entries': len(d['cases']),
            'reading_stages': dict(Counter(c['review']['stage'] for c in d['cases'])),
            'entry_kinds': dict(Counter(c['kind'] for c in d['cases'])),
            'historical_sources': [s['id'] for s in d['sources'] if s.get('maintenance') == 'historical'],
            'runtime_tested': 0, 'model_quality_measured': False}


def search(d, query, limit=15, source=None):
    q = query.casefold().strip()
    if not q:
        return []
    terms = set(re.findall(r'[\w-]+', q))
    for k, values in ALIASES.items():
        if k in q:
            terms.update(values)
    rows = []
    sources = {s['id']: s for s in d['sources']}
    for c in d['cases']:
        if source and c['source_id'] != source:
            continue
        # Don't match every case just because its review disclaimer mentions a query.
        names = ' '.join([c['title'], c['path'], *c['native_labels']]).casefold()
        context = ' '.join([c['source_id'], *c['domain_hints']]).casefold()
        score = sum(3 if t in names else 1 if t in context else 0 for t in terms)
        score += 5 if q in names else 0
        if score:
            rows.append({**c, 'score': score, 'maintenance': sources[c['source_id']]['maintenance'],
                         'license': sources[c['source_id']]['license'], 'recommended': False})
    return sorted(rows, key=lambda c: (-c['score'], c['id']))[:limit]


def diff(old, new):
    left = {c['id']: c for c in old['cases']}; right = {c['id']: c for c in new['cases']}
    changed = [cid for cid in left.keys() & right.keys() if left[cid]['artifact'] != right[cid]['artifact']]
    return {'added': sorted(right.keys()-left.keys()), 'removed': sorted(left.keys()-right.keys()),
            'changed': sorted(changed), 'unchanged': len(left.keys() & right.keys())-len(changed)}


def merge(old, incoming):
    """Carry review only across identical artifacts; a changed tree invalidates old review."""
    result = json.loads(json.dumps(incoming)); previous = {c['id']: c for c in old['cases']}
    for c in result['cases']:
        p = previous.get(c['id'])
        # Web articles without a content hash need a fresh scoped review each time.
        same = p and c['artifact'].get('sha') and p['artifact'] == c['artifact']
        if same and c['review']['stage'] == 'indexed' and p['review']['stage'] != 'indexed':
            c['review'] = p['review']
    return result


def plan(d, limit=24, cycle=0, on=None):
    """Source round-robin, then native-category round-robin. Does not mark work done."""
    today = on or date.today().isoformat()
    groups = defaultdict(lambda: defaultdict(list)); sources = {s['id']: s for s in d['sources']}
    for c in d['cases']:
        if sources[c['source_id']]['maintenance'] == 'historical':
            continue
        r = c['review']
        age = (date.fromisoformat(today)-date.fromisoformat(r['checked_on'])).days
        if r['stage'] == 'body-reviewed' and age < 90:
            continue
        groups[c['source_id']][c['native_category']].append(c)
    per_source = {}
    for sid, cats in groups.items():
        pools = []
        for cat, rows in sorted(cats.items()):
            rows.sort(key=lambda c: (0 if c['review']['stage'] == 'indexed' else 1, c['id']))
            offset = cycle % len(rows)
            pools.append(deque(rows[offset:]+rows[:offset]))
        lane = []
        while any(pools):
            for pool in pools:
                if pool:
                    lane.append(pool.popleft())
        per_source[sid] = deque(lane)
    order = sorted(per_source)
    if order:
        offset = cycle % len(order); order = order[offset:]+order[:offset]
    queue = []
    while len(queue) < limit and any(per_source.values()):
        for sid in order:
            if per_source[sid] and len(queue) < limit:
                c = per_source[sid].popleft()
                queue.append({'id': c['id'], 'url': c['url'], 'kind': c['kind'],
                              'native_category': c['native_category'], 'previous_stage': c['review']['stage'],
                              'artifact': c['artifact'], 'status': 'pending',
                              'license_scope': sources[sid]['license']['scope']})
    return {'kind': 'discovery-review-plan', 'revision': d['revision'], 'planned_on': today, 'cycle': cycle,
            'source_checks': [{'id': s['id'], 'url': s['url'], 'previous_root_tree_sha': s.get('root_tree_sha'),
                               'status': 'pending', 'attempts': []} for s in d['sources']],
            'body_review_queue': queue, 'unresolved_leads': d.get('unresolved_leads', []),
            'limits': ['All work is pending. Reaching a homepage is not checked-no-new.',
                       'The body queue is a rotating sample; it does not cover every indexed entry each week.',
                       'Keep the separate full author-watchlist scan; do not replace it with this plan.']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--index', type=Path, default=REF/'discovery-index.json')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('validate'); sub.add_parser('inventory')
    p = sub.add_parser('search'); p.add_argument('query'); p.add_argument('--limit', type=int, default=15); p.add_argument('--source')
    p = sub.add_parser('plan'); p.add_argument('--limit', type=int, default=24); p.add_argument('--cycle', type=int, default=date.today().toordinal()//7); p.add_argument('--output', type=Path)
    p = sub.add_parser('diff'); p.add_argument('previous', type=Path)
    p = sub.add_parser('merge'); p.add_argument('incoming', type=Path); p.add_argument('--output', type=Path, required=True)
    a = ap.parse_args(); d = read(a.index); errors = validate(d)
    if errors:
        print(json.dumps({'errors': errors}, ensure_ascii=False)); raise SystemExit(1)
    if a.cmd == 'validate': value = {'errors': [], 'scope': 'index/provenance; no runtime or model validation'}
    elif a.cmd == 'inventory': value = inventory(d)
    elif a.cmd == 'search': value = search(d, a.query, max(0, a.limit), a.source)
    elif a.cmd == 'diff': value = diff(read(a.previous), d)
    elif a.cmd == 'merge':
        incoming = read(a.incoming); errors = validate(incoming)
        if errors: raise ValueError(errors)
        value = merge(d, incoming)
    else: value = plan(d, max(0, a.limit), a.cycle)
    text = json.dumps(value, ensure_ascii=False, indent=2)+'\n'
    if a.cmd in ['plan', 'merge'] and a.output:
        if a.output.resolve() == a.index.resolve():
            raise ValueError('Write a reviewed candidate separately; do not overwrite the active index.')
        a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(text)
    else:
        print(text, end='')


if __name__ == '__main__': main()
