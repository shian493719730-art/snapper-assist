#!/usr/bin/env python3
"""Guard evidence labels, changed-artifact review invalidation and discovery breadth."""
import copy
from pathlib import Path
import unittest
import source_index as s


class Discovery(unittest.TestCase):
    def setUp(self):
        self.data=s.read(s.REF/'discovery-index.json')
        self.reviewed=next(c for c in self.data['cases'] if c['review']['stage']=='body-reviewed' and c['artifact']['sha'])

    def test_current_data_contract_and_no_runtime_claim(self):
        self.assertEqual(s.validate(self.data), [])
        inv=s.inventory(self.data)
        self.assertEqual(sum(inv['reading_stages'].values()), inv['entries'])
        self.assertEqual(inv['runtime_tested'], 0)
        self.assertFalse(inv['model_quality_measured'])

    def test_duplicate_canonical_path_is_rejected(self):
        duplicate=copy.deepcopy(self.data['cases'][0]); duplicate['id']='different-id'
        self.data['cases'].append(duplicate)
        self.assertTrue(any('duplicate-path' in x for x in s.validate(self.data)))

    def test_unknown_source_and_unscoped_license_are_rejected(self):
        self.data['cases'][0]['source_id']='unknown'
        self.data['sources'][0]['license'].pop('scope')
        errors=s.validate(self.data)
        self.assertTrue(any('unknown-source' in x for x in errors))
        self.assertTrue(any('source-provenance' in x for x in errors))

    def test_partial_read_cannot_be_called_body_reviewed(self):
        self.reviewed['review']['read_ranges'][0]['end']-=1
        self.assertTrue(any('incomplete-body' in x for x in s.validate(self.data)))

    def test_changed_tree_cannot_keep_current_review_label(self):
        self.reviewed['artifact']['sha']='a'*40
        self.assertTrue(any('review-version' in x for x in s.validate(self.data)))

    def test_discovery_cannot_claim_execution(self):
        self.data['cases'][0]['execution']['status']='passed'
        self.assertTrue(any('runtime-claim' in x for x in s.validate(self.data)))

    def test_chinese_search_and_original_taxonomy(self):
        rows=s.search(self.data,'数据库',limit=100)
        self.assertTrue(any(c['source_id']=='supabase/agent-skills' for c in rows))
        rows=s.search(self.data,'视频',source='remotion-dev/skills')
        self.assertTrue(rows)
        self.assertTrue(all(c['native_category'] and c['recommended'] is False for c in rows))
        self.assertEqual(s.search(self.data,'   '), [])

    def test_queue_covers_sources_before_repeating_and_stays_pending(self):
        before=copy.deepcopy(self.data)
        plan=s.plan(self.data,limit=24,cycle=0,on='2026-11-10')
        queue=plan['body_review_queue']; ids=[c['id'].split(':')[0] for c in queue]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(all(c['status']=='pending' for c in queue))
        self.assertEqual(len(plan['source_checks']),len(self.data['sources']))
        self.assertEqual(before,self.data)
        self.assertFalse(any('crewAIInc/' in c['id'] or 'anthropics/courses:' in c['id'] for c in queue))

    def test_rotation_changes_queue_without_claiming_a_scan(self):
        first=s.plan(self.data,limit=8,cycle=0,on='2026-11-10')
        second=s.plan(self.data,limit=8,cycle=1,on='2026-11-10')
        self.assertNotEqual(first['body_review_queue'],second['body_review_queue'])
        self.assertTrue(all(c['status']=='pending' for c in second['source_checks']))

    def test_merge_keeps_only_same_artifact_review(self):
        incoming=copy.deepcopy(self.data)
        target=next(c for c in incoming['cases'] if c['id']==self.reviewed['id'])
        target['review']={'stage':'indexed','scope':'directory only','checked_on':'2026-11-11'}
        merged=s.merge(self.data,incoming)
        self.assertEqual(next(c for c in merged['cases'] if c['id']==target['id'])['review'],self.reviewed['review'])
        target['artifact']['sha']='b'*40
        merged=s.merge(self.data,incoming)
        self.assertEqual(next(c for c in merged['cases'] if c['id']==target['id'])['review']['stage'],'indexed')
        self.assertEqual(s.validate(merged), [])
        self.assertEqual(s.diff(self.data,incoming)['changed'],[target['id']])

    def test_web_review_without_hash_needs_new_check(self):
        incoming=copy.deepcopy(self.data)
        target=next(c for c in incoming['cases'] if c['artifact']['type']=='web' and c['review']['stage']!='indexed')
        target['review']={'stage':'indexed','scope':'index only','checked_on':'2026-11-11'}
        merged=s.merge(self.data,incoming)
        self.assertEqual(next(c for c in merged['cases'] if c['id']==target['id'])['review']['stage'],'indexed')

    def test_diff_separates_add_remove_and_change(self):
        incoming=copy.deepcopy(self.data); removed=incoming['cases'].pop()
        added=copy.deepcopy(incoming['cases'][0]);added['id']='new';added['path']='new'
        incoming['cases'].append(added)
        result=s.diff(self.data,incoming)
        self.assertEqual(result['added'],['new']);self.assertEqual(result['removed'],[removed['id']])


if __name__=='__main__':unittest.main()
