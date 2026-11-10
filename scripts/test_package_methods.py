#!/usr/bin/env python3
"""Release defaults are public, deterministic and usable without a local profile."""
import copy
import json
import unittest
import package_methods as pack
import preferences as p


class PackagedMethods(unittest.TestCase):
    def setUp(self):
        self.base=p.read(p.BASE);self.library=p.read(p.LIBRARY)

    def test_public_defaults_cover_domains_without_personal_choices(self):
        value=pack.assets(self.base,self.library)
        self.assertEqual(len(value['prompt-recipes.json']['recipes']),15)
        self.assertEqual(len(value['domain-presets.json']['domains']),14)
        self.assertTrue(all(r.get(p.MARKER,{}).get('origin') in [None,'curated-recommendation'] for r in value['prompt-recipes.json']['recipes']))
        academic=next(r for r in value['prompt-recipes.json']['recipes'] if r['id']=='academic-dialogue')
        self.assertEqual(academic[p.MARKER]['method'],'argument-map')

    def test_assets_are_deterministic_and_do_not_mutate_sources(self):
        before=copy.deepcopy([self.base,self.library])
        self.assertEqual(pack.assets(self.base,self.library),pack.assets(self.base,self.library))
        self.assertEqual([self.base,self.library],before)

    def test_native_presets_include_every_allowed_domain_choice(self):
        value=pack.assets(self.base,self.library)
        self.assertEqual(sum(len(d['methods']) for d in value['domain-presets.json']['domains']),sum(len(d['methods']) for d in self.library['domains']))
        for domain in value['domain-presets.json']['domains']:
            for method in domain['methods']:
                self.assertEqual(method['recipe']['id'],domain['recipe_id'])
                self.assertFalse(any(k.startswith('_') for k in method['recipe']))
                p.validate_catalog({'recipes':[method['recipe'],next(r for r in self.base['recipes'] if r['id']=='general')]})

    def test_unread_source_cannot_enter_release(self):
        self.library['sources'][0]['status']='pending'
        with self.assertRaises(ValueError):pack.assets(self.base,self.library)


if __name__=='__main__':unittest.main()
