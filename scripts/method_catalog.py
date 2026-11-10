#!/usr/bin/env python3
"""Read, search, validate and plan review of a source-backed method index.

This operates on local plain data. The research agent must actually browse the
sources; the plan is not a completed search and no skill is installed or run.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'references' if (ROOT/'references/domain-methods.json').is_file() else ROOT/'skills/agent-learning-loop/references'


def validate(d):
    errors=[]
    groups={key:{x['id']:x for x in d.get(key,[])} for key in ['domains','methods','sources']}
    for key in groups:
        if len(groups[key]) != len(d.get(key,[])): errors.append('duplicate-'+key)
    for domain in d.get('domains',[]):
        if not set(domain['methods']) <= set(groups['methods']) or domain.get('default_method') not in domain['methods']:
            errors.append(domain['id']+':method-mapping')
        if not domain.get('example') or not domain.get('artifact_kinds'): errors.append(domain['id']+':missing-usage')
    for m in d.get('methods',[]):
        if not set(m['source_ids']) <= set(groups['sources']): errors.append(m['id']+':unknown-source')
        if not m.get('not_for') or not m.get('validation'): errors.append(m['id']+':missing-boundary')
    for s in d.get('sources',[]):
        if not re.match(r'^https://',s['url']) or not s.get('read_scope') or not s.get('reuse_note') or not s.get('limitations'):
            errors.append(s['id']+':provenance')
    return errors


def search(d, query):
    q=query.casefold(); methods={m['id']:m for m in d['methods']}; sources={s['id']:s for s in d['sources']}
    rows=[]
    for domain in d['domains']:
        # Case-insensitive local lookup, not a claim of semantic classification.
        text=json.dumps(domain,ensure_ascii=False).casefold()
        score=sum(1 for k in domain['keywords'] if k.casefold() in q) + (2 if q in text else 0)
        if not score: continue
        rows.append({'domain':domain['id'],'title':domain['title'],'score':score,
                     'methods':[{'id':mid,'title':methods[mid]['title'],'status':methods[mid]['status'],
                                 'sources':[{'url':sources[sid]['url'],'native_labels':sources[sid]['native_labels']} for sid in methods[mid]['source_ids']]} for mid in domain['methods']]})
    return sorted(rows,key=lambda x:-x['score'])


def plan(d):
    return {'schema_version':1,'kind':'method-source-review-plan','started_on':date.today().isoformat(),
            'library_revision':d['revision'],
            'coverage':[{'source_id':s['id'],'url':s['url'],'previous_read_scope':s['read_scope'],'status':'pending','attempts':[],'note':''} for s in d['sources']],
            'discovery_lanes':['new primary use cases','repository native taxonomies','domain-specific practice and research','migration and license changes','counterexamples and conflicting evidence'],
            'new_sources':[],'changes':[],'limits':['A generated plan is not a completed scan.']}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--library',type=Path,default=REF/'domain-methods.json')
    sub=ap.add_subparsers(dest='cmd',required=True)
    sub.add_parser('validate');sub.add_parser('inventory')
    p=sub.add_parser('search');p.add_argument('query')
    p=sub.add_parser('plan');p.add_argument('--output',type=Path)
    a=ap.parse_args();d=json.loads(a.library.read_text());errors=validate(d)
    if errors: print(json.dumps({'errors':errors}));raise SystemExit(1)
    if a.cmd=='validate': value={'errors':[],'scope':'data/provenance; not model effectiveness'}
    elif a.cmd=='inventory': value={k:len(d[k]) for k in ['domains','methods','sources']}
    elif a.cmd=='search': value=search(d,a.query)
    else: value=plan(d)
    text=json.dumps(value,ensure_ascii=False,indent=2)
    if a.cmd=='plan' and a.output: a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text+'\n')
    else: print(text)


if __name__=='__main__':main()
