"""Kiểm thử tự động:  python -m unittest discover -s tests -v   (chạy từ thư mục gốc dự án)"""
import pathlib
import random
import unittest

import networkx as nx

from model.algorithms import ALGORITHMS, run_to_end
from model.graph_model import Graph

ROOT = pathlib.Path(__file__).resolve().parent.parent


def to_nx(g):
    G = nx.Graph()
    for a in g.nodes:
        for b, w in g.adj[a].items():
            G.add_edge(a, b, weight=w)
    return G


class SampleGraph(unittest.TestCase):
    def setUp(self):
        self.g = Graph.sample()

    def test_best_first_finds_path(self):
        _, r = run_to_end(self.g, "Best-First Search", "A", "J")
        self.assertTrue(r.success)
        self.assertEqual(r.path, ["A", "B", "E", "F", "J"])

    def test_hill_climbing_stuck_in_local_minimum(self):
        steps, r = run_to_end(self.g, "Hill Climbing", "A", "J")
        self.assertFalse(r.success)
        self.assertEqual(steps[-1].current, "C")

    def test_random_restart_escapes(self):
        _, r = run_to_end(self.g, "Random-Restart Hill Climbing", "A", "J", seed=1)
        self.assertTrue(r.success)

    def test_random_restart_zero_restarts_equals_hill_climbing(self):
        _, r = run_to_end(self.g, "Random-Restart Hill Climbing", "A", "J",
                          max_restarts=0, seed=1)
        self.assertFalse(r.success)


class KnownLimitations(unittest.TestCase):
    def test_best_first_not_optimal(self):
        g = Graph()
        for n, xy in dict(S=(0, 0), X=(5, 1), Y=(5, 8), G=(10, 0)).items():
            g.add_node(n, *xy)
        g.add_edge("S", "X", 100)
        g.add_edge("X", "G", 5)
        g.add_edge("S", "Y", 8)
        g.add_edge("Y", "G", 8)
        _, r = run_to_end(g, "Best-First Search", "S", "G")
        self.assertEqual(r.path, ["S", "X", "G"])
        self.assertEqual(r.cost, 105)
        self.assertEqual(r.optimal, 16)
        self.assertGreater(r.ratio, 6)

    def test_hill_climbing_stops_on_plateau(self):
        g = Graph()
        for n, xy in dict(S=(0, 10), T=(0, -10), G=(10, 0)).items():
            g.add_node(n, *xy)
        g.add_edge("S", "T")
        g.add_edge("T", "G")
        self.assertEqual(g.h("S", "G"), g.h("T", "G"))
        _, r = run_to_end(g, "Hill Climbing", "S", "G")
        self.assertFalse(r.success)


class RandomGraphs(unittest.TestCase):
    def test_generators_connected_and_dijkstra_matches_networkx(self):
        for seed in range(40):
            for g in (Graph.random_graph(25, seed), Graph.grid_graph(25, seed),
                      Graph.random_graph(25, seed, weights="random")):
                G = to_nx(g)
                self.assertTrue(nx.is_connected(G))
                s, t = random.Random(seed).sample(g.nodes, 2)
                self.assertAlmostEqual(
                    g.shortest_cost(s, t),
                    nx.shortest_path_length(G, s, t, weight="weight"), places=1)

    def test_best_first_complete_and_ratio_at_least_one(self):
        for seed in range(60):
            g = Graph.grid_graph(30, seed)
            s, t = random.Random(seed).sample(g.nodes, 2)
            for a in ALGORITHMS:
                _, r = run_to_end(g, a, s, t, seed=seed)
                if a == "Best-First Search":
                    self.assertTrue(r.success, f"BFS phải thành công (seed={seed})")
                if r.success:
                    self.assertGreaterEqual(r.ratio, 1.0)
                    self.assertEqual(r.path[-1], t)


class Encoding(unittest.TestCase):
    def test_all_text_files_are_valid_utf8_vietnamese(self):
        for f in list(ROOT.rglob("*.py")) + [ROOT / "README.md"]:
            txt = f.read_text(encoding="utf-8")          # ném lỗi nếu không phải UTF-8
            self.assertNotIn(chr(0xFFFD), txt, f.name)
        csv_head = (ROOT / "benchmark_results.csv").read_bytes()[:3]
        self.assertEqual(csv_head, b"\xef\xbb\xbf")      # BOM để Excel đọc đúng


if __name__ == "__main__":
    unittest.main()
