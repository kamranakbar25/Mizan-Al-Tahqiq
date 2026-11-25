import unittest
from research.ocr.scripts.detection.mizan_layout import group_regions

class LayoutGroupingTests(unittest.TestCase):
    def test_merges_adjacent_lines_and_splits_paragraph_gap(self):
        rows = [
            {"line_id":"l1", "bbox":[100,100,900,128]},
            {"line_id":"l2", "bbox":[100,132,900,160]},
            {"line_id":"l3", "bbox":[100,220,900,248]},
        ]
        groups = group_regions(rows, 1000, 1400)
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0]["line_ids"], ["l1", "l2"])
        self.assertEqual(groups[1]["line_ids"], ["l3"])

    def test_splits_unrelated_same_baseline_regions(self):
        rows = [
            {"line_id":"page_no", "bbox":[40,40,90,70]},
            {"line_id":"header", "bbox":[600,40,950,70]},
        ]
        self.assertEqual(len(group_regions(rows, 1000, 1400)), 2)

    def test_empty_input(self):
        self.assertEqual(group_regions([], 1000, 1400), [])

if __name__ == "__main__":
    unittest.main()
