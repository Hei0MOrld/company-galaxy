# public/data/graph.json (what the browser loads) must stay internally consistent after every rebuild.
import json, os, unittest

GRAPH = os.path.join(os.path.dirname(__file__), "..", "public", "data", "graph.json")


class GraphData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = json.load(open(GRAPH))
        cls.n = len(cls.g["nodes"])

    def test_has_data(self):
        self.assertGreater(self.n, 1000)
        self.assertGreater(len(self.g["edges"]), 1000)
        self.assertIn("Wikidata", self.g["source"])

    def test_node_shape(self):
        # [qid, name, ja name or None, country idx, industry idx, sitelinks, enwiki, jawiki]
        for node in self.g["nodes"]:
            q, name, ja, ci, ii, sl, en, jw = node
            self.assertRegex(q, r"^Q\d+$")
            self.assertTrue(name)
            self.assertTrue(-1 <= ci < len(self.g["countries"]), node)
            self.assertTrue(-1 <= ii < len(self.g["industries"]), node)
            self.assertIsInstance(sl, int)
            for w in (en, jw):
                self.assertFalse(w and w.startswith("http"), "wiki fields keep only the page name")

    def test_qids_unique(self):
        qs = [x[0] for x in self.g["nodes"]]
        self.assertEqual(len(qs), len(set(qs)))

    def test_nodes_sorted_by_sitelinks(self):
        sl = [x[5] for x in self.g["nodes"]]
        self.assertEqual(sl, sorted(sl, reverse=True))

    def test_edges_valid(self):
        seen = set()
        for a, b, kind in self.g["edges"]:
            self.assertTrue(0 <= a < self.n and 0 <= b < self.n)
            self.assertNotEqual(a, b, "no company owns itself")
            self.assertIn(kind, (0, 1))
            seen.add((a, b, kind))
        self.assertEqual(len(seen), len(self.g["edges"]), "no duplicate edges")

    def test_filters_point_at_real_nodes(self):
        for group in ("indices", "exchanges"):
            for f in self.g[group]:
                self.assertTrue(f["en"])
                self.assertTrue(all(0 <= m < self.n for m in f["members"]), f["en"])

    def test_japanese_labels_aligned(self):
        for key in ("countries", "industries"):
            self.assertEqual(len(self.g[key + "_ja"]), len(self.g[key]))


class Page(unittest.TestCase):
    def test_page_loads_the_data_file(self):
        html = open(os.path.join(os.path.dirname(GRAPH), "..", "index.html")).read()
        self.assertIn("data/graph.json", html)


if __name__ == "__main__":
    unittest.main()
