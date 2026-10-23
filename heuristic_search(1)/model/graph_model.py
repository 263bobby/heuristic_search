"""MODEL - Mô hình đồ thị (không gian trạng thái) và hàm heuristic h(n)."""
import math
import random


class Graph:
    """Đồ thị vô hướng có trọng số; mỗi nút có toạ độ (x, y) để tính heuristic."""

    def __init__(self):
        self.pos = {}   # nút -> (x, y)
        self.adj = {}   # nút -> {nút kề: chi phí cạnh}

    # ---------- xây dựng ----------
    def add_node(self, name, x, y):
        self.pos[name] = (x, y)
        self.adj.setdefault(name, {})

    def add_edge(self, a, b, w=None):
        if w is None:
            w = round(self.euclid(a, b), 1)
        self.adj[a][b] = w
        self.adj[b][a] = w

    # ---------- truy vấn ----------
    @property
    def nodes(self):
        return list(self.pos.keys())

    def neighbors(self, n):
        return list(self.adj[n].keys())

    def euclid(self, a, b):
        (x1, y1), (x2, y2) = self.pos[a], self.pos[b]
        return math.hypot(x1 - x2, y1 - y2)

    def h(self, n, goal):
        """Heuristic: khoảng cách Euclid từ n tới đích."""
        return round(self.euclid(n, goal), 1)

    def path_cost(self, path):
        return round(sum(self.adj[path[i]][path[i + 1]]
                         for i in range(len(path) - 1)), 1)

    def remove_edge(self, a, b):
        self.adj[a].pop(b, None)
        self.adj[b].pop(a, None)

    def shortest_cost(self, start, goal):
        """Dijkstra: chi phí tối ưu thật sự từ start tới goal (inf nếu không tới được).
        Chỉ dùng để ĐÁNH GIÁ chất lượng lời giải, không dùng trong các thuật toán."""
        import heapq
        dist = {start: 0.0}
        pq = [(0.0, start)]
        while pq:
            d, n = heapq.heappop(pq)
            if n == goal:
                return round(d, 1)
            if d > dist.get(n, float("inf")):
                continue
            for m, w in self.adj[n].items():
                nd = d + w
                if nd < dist.get(m, float("inf")):
                    dist[m] = nd
                    heapq.heappush(pq, (nd, m))
        return float("inf")

    # ---------- đồ thị dựng sẵn ----------
    @staticmethod
    def sample():
        """Đồ thị mẫu 10 nút. Từ A -> J, Hill Climbing bị kẹt tại cực tiểu cục bộ C."""
        g = Graph()
        coords = {
            "A": (0, 50), "B": (30, 90), "C": (40, 50), "D": (30, 10),
            "E": (60, 85), "F": (85, 75), "G": (60, 15), "H": (85, 25),
            "I": (55, 50), "J": (100, 50),
        }
        for k, (x, y) in coords.items():
            g.add_node(k, x, y)
        for a, b in [("A", "B"), ("A", "C"), ("A", "D"), ("B", "E"), ("E", "F"),
                     ("F", "J"), ("D", "G"), ("G", "H"), ("H", "J"),
                     ("E", "I"), ("G", "I")]:
            g.add_edge(a, b)
        return g

    @staticmethod
    def grid_graph(n=20, seed=None, drop=0.25, weights="euclid"):
        """Đồ thị lưới ~n nút (ô vuông), ngẫu nhiên bỏ một phần cạnh nhưng luôn liên thông
        (giữ một cây khung ngẫu nhiên). Tạo nhiều 'ngõ cụt' hơn đồ thị k-NN."""
        rnd = random.Random(seed)
        rows = max(2, round(n ** 0.5))
        cols = max(2, -(-n // rows))
        g = Graph()
        name = lambda r, c: f"N{r * cols + c}"
        for r in range(rows):
            for c in range(cols):
                g.add_node(name(r, c), c * 100 / (cols - 1), r * 100 / (rows - 1))
        edges = [(name(r, c), name(r, c + 1)) for r in range(rows) for c in range(cols - 1)]
        edges += [(name(r, c), name(r + 1, c)) for r in range(rows - 1) for c in range(cols)]
        rnd.shuffle(edges)
        parent = {v: v for v in g.nodes}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        keep, rest = [], []
        for a, b in edges:                      # cây khung ngẫu nhiên
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
                keep.append((a, b))
            else:
                rest.append((a, b))
        keep += [e for e in rest if rnd.random() > drop]
        for a, b in keep:
            g.add_edge(a, b, Graph._weight(g, a, b, rnd, weights))
        return g

    @staticmethod
    def _weight(g, a, b, rnd, weights):
        if weights == "random":      # trọng số ngẫu nhiên, KHÔNG liên quan tới Euclid
            return round(rnd.uniform(5, 60), 1)
        return round(g.euclid(a, b), 1)

    @staticmethod
    def random_graph(n=20, seed=None, knn=3, weights="euclid"):
        """Đồ thị ngẫu nhiên liên thông: cây khung nhỏ nhất + k láng giềng gần nhất.
        weights='euclid' (mặc định) hoặc 'random' (trọng số ngẫu nhiên 5..60)."""
        rnd = random.Random(seed)
        g = Graph()
        names = [f"N{i}" for i in range(n)]
        for nm in names:
            g.add_node(nm, rnd.uniform(0, 100), rnd.uniform(0, 100))
        # Kruskal để đảm bảo liên thông
        parent = {nm: nm for nm in names}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        pairs = sorted((g.euclid(a, b), a, b)
                       for i, a in enumerate(names) for b in names[i + 1:])
        def link(a, b):                 # không ghi đè cạnh đã có (giữ nguyên trọng số)
            if b not in g.adj[a]:
                g.add_edge(a, b, Graph._weight(g, a, b, rnd, weights))

        for _, a, b in pairs:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
                link(a, b)
        for a in names:
            near = sorted((b for b in names if b != a), key=lambda b: g.euclid(a, b))
            for b in near[:knn]:
                link(a, b)
        return g
