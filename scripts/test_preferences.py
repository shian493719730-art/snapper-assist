#!/usr/bin/env python3
"""Preference boundaries and optional actual native prompt-construction checks."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import preferences as p

PROBE = None


class Preferences(unittest.TestCase):
    def setUp(self):
        self.base = p.read(p.BASE); self.lib = p.read(p.LIBRARY)
        self.state = {'schema_version': 1, 'preferences': {}, 'feedback': {}}

    def confirm(self, domain='academic-dialogue'):
        p.remember(self.state, self.lib, domain, 'socratic-dialogue', 'explicit-user')

    def test_empty_profile_does_not_assume_socratic_preference(self):
        result = p.compile_catalog(self.base, self.state, self.lib)
        self.assertEqual(result['recipes'], self.base['recipes'])

    def test_domains_are_independent_and_existing_customizations_survive(self):
        self.base['recipes'][0]['deliverables'].append('Preserve this local customization.')
        self.confirm(); result = p.compile_catalog(self.base, self.state, self.lib)
        self.assertEqual(len(result['recipes']), len(self.base['recipes'])+1)
        self.assertEqual(result['recipes'][1:], self.base['recipes'])
        self.assertFalse(any(r['id']=='argument-review' for r in result['recipes']))

    def test_feedback_only_proposes_and_never_confirms(self):
        for _ in range(3): p.feedback(self.state,self.lib,'argument-review','socratic-dialogue','accept')
        self.assertTrue(self.state['feedback']['argument-review/socratic-dialogue']['candidate'])
        self.assertEqual(self.state['preferences'], {})
        self.assertEqual(p.compile_catalog(self.base,self.state,self.lib)['recipes'],self.base['recipes'])

    def test_candidate_needs_deliberate_confirmation(self):
        with self.assertRaises(ValueError): p.remember(self.state,self.lib,'argument-review','socratic-dialogue','confirmed-candidate')
        for _ in range(3): p.feedback(self.state,self.lib,'argument-review','socratic-dialogue','accept')
        p.remember(self.state,self.lib,'argument-review','socratic-dialogue','confirmed-candidate')
        self.assertEqual(self.state['preferences']['argument-review']['status'],'confirmed')

    def test_undo_is_not_treated_as_a_long_term_dislike(self):
        self.confirm(); old = copy.deepcopy(self.state['preferences'])
        p.feedback(self.state,self.lib,'academic-dialogue','socratic-dialogue','undo')
        self.assertEqual(self.state['preferences'],old)
        self.assertNotIn('selected_text',json.dumps(self.state))

    def test_bad_method_and_fake_confirmation_are_rejected(self):
        with self.assertRaises(ValueError): p.remember(self.state,self.lib,'academic-dialogue','run-a-skill','explicit-user')
        with self.assertRaises(ValueError): p.remember(self.state,self.lib,'academic-dialogue','socratic-dialogue','guessed')
        self.assertEqual(self.state['preferences'],{})

    def test_recompile_is_idempotent_and_removal_clears_only_generated_recipe(self):
        self.confirm(); first = p.compile_catalog(self.base,self.state,self.lib)
        self.assertEqual(p.compile_catalog(first,self.state,self.lib),first)
        self.state['preferences'].clear()
        self.assertEqual(p.compile_catalog(first,self.state,self.lib)['recipes'],self.base['recipes'])

    def test_custom_id_collision_is_not_overwritten(self):
        self.confirm(); duplicate = copy.deepcopy(self.base['recipes'][0]);duplicate['id']='academic-dialogue';self.base['recipes'].append(duplicate)
        with self.assertRaises(ValueError): p.compile_catalog(self.base,self.state,self.lib)

    def test_invalid_native_catalog_cannot_replace_working_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'recipes.json';output.write_text(json.dumps(self.base))
            invalid=copy.deepcopy(self.base);invalid['recipes'][0]['questions']=['a','b','c']
            with self.assertRaises(ValueError): p.apply_catalog(output,invalid)
            self.assertEqual(p.read(output),self.base)

    def test_corrupt_preferences_fail_without_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'state.json';output.write_text('{broken')
            with self.assertRaises(ValueError): p.load_preferences(output)
            self.assertEqual(output.read_text(),'{broken')

    def test_private_atomic_write_and_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'recipes.json';output.write_text(json.dumps(self.base))
            self.confirm();p.apply_catalog(output,p.compile_catalog(self.base,self.state,self.lib))
            self.assertEqual(os.stat(output).st_mode & 0o777,0o600)
            self.assertEqual(p.read(output.with_name(output.name+'.before-domain-profiles.json')),self.base)

    def test_actual_native_domain_routing_and_prompt_boundaries(self):
        if not PROBE: self.skipTest('Compile PreferenceProbe for native construction checks')
        self.confirm();self.confirm('argument-review')
        catalog = p.compile_catalog(self.base,self.state,self.lib)
        cases = ['学术讨论：什么算作知识？', '推敲我的观点：效率总是最重要的。',
                 '请优化我的观点，不要提问，直接给改写。', '学术讨论，不用苏格拉底法，直接解释概念。',
                 '期末复习第一章', '请修复软件 bug，不能改数据。', '设计一个页面',
                 '写一封邮件', '论文排版格式怎么调整？', '研究这个市场的资料',
                 '学术讨论：'+('保留我的论证与材料，不编造事实。'*30)]
        with tempfile.TemporaryDirectory() as tmp:
            c=Path(tmp)/'catalog.json';q=Path(tmp)/'cases.json';c.write_text(json.dumps(catalog,ensure_ascii=False));q.write_text(json.dumps(cases,ensure_ascii=False))
            result=json.loads(subprocess.check_output([PROBE,str(c),str(q)],text=True))
        expected=['academic-dialogue','argument-review','argument-review','academic-dialogue','learning','coding','design','writing','writing','research','academic-dialogue']
        self.assertEqual([r['recipe'] for r in result],expected)
        for original,r in zip(cases,result):
            self.assertIn(original,r['text']);self.assertTrue(r['ai_payload_contains_prepared_draft'])
        self.assertIn('每次只问一个',result[0]['text'])
        self.assertEqual(result[2]['questions'],[])
        self.assertIn('禁止提问',result[2]['text'])
        self.assertIn('不用苏格拉底法',result[3]['text'])
        for r in result[4:10]: self.assertNotIn('苏格拉底',r['text'])
        self.assertIn('本次明确要求优先于历史偏好',result[10]['text'])


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--native-probe');args,rest=ap.parse_known_args();PROBE=args.native_probe
    unittest.main(argv=[__file__]+rest)
