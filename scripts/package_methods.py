#!/usr/bin/env python3
"""Build public native assets without reading the builder's personal profile."""
import argparse
import json
from pathlib import Path
import method_catalog
import preferences as p


def assets(base, library):
    errors=method_catalog.validate(library)
    if errors: raise ValueError(errors)
    state={'schema_version':1,'preferences':{},'feedback':{},'recommendations_enabled':True}
    catalog=p.compile_catalog(base,state,library)
    domains=[]
    for d in library['domains']:
        methods=[]
        for mid in d['methods']:
            method=next(m for m in library['methods'] if m['id']==mid)
            if method['status']!='source-reviewed' or any(next(s for s in library['sources'] if s['id']==sid)['status']!='read' for sid in method['source_ids']):
                raise ValueError('Cannot package unread method '+mid)
            personal={'schema_version':1,'preferences':{},'feedback':{}}
            p.remember(personal,library,d['id'],mid,'explicit-user')
            result=p.compile_catalog(base,personal,library)
            recipe=next(r for r in result['recipes'] if r.get(p.MARKER,{}).get('domain')==d['id'])
            recipe={key:value for key,value in recipe.items() if not key.startswith('_')}
            methods.append({'id':mid,'title':method['title'],'recipe':recipe})
        domains.append({'id':d['id'],'title':d['title'],'recipe_id':d.get('native_recipe_id',d['id']),'example':d['example'],
                        'default_method':d['default_method'],'methods':methods})
    return {'prompt-recipes.json':catalog,'domain-presets.json':{'schema_version':1,'revision':library['revision'],'domains':domains},
            'domain-methods.json':library}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    result=assets(p.read(p.BASE),p.read(p.LIBRARY));a.output.mkdir(parents=True,exist_ok=True)
    for name,value in result.items():(a.output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'public_methods':len(result['domain-methods.json']['methods']),'domains':len(result['domain-presets.json']['domains']),
                      'active_recipes':len(result['prompt-recipes.json']['recipes']),'personal_preferences_bundled':False}))


if __name__=='__main__':main()
