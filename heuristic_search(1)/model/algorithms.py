"""MODEL - Các thuật toán tìm kiếm Heuristic.

Mỗi thuật toán là một GENERATOR: mỗi lần `next()` trả về một `Step` mô tả trạng thái
trung gian (nút đang xét, h, Open, Closed, láng giềng...). Nhờ vậy GUI có thể chạy
từng bước hoặc tự động mà không cần sửa thuật toán, và benchmark có thể chạy "một mạch".
"""
import heapq
import random
import time
from dataclasses import dataclass, field


@dataclass
class Step:
    k: int                      # số thứ tự bước
    current: str                # nút đang xét
    h: float                    # h(current)
    neighbors: list             # [(nút, h)] các láng giềng được xem xét
    open_list: list             # [(nút, h)] tập Open / Frontier
    closed_list: list           # danh sách nút đã duyệt
    message: str                # mô tả bước bằng lời
    path: list = field(default_factory=list)   # đường đi (chỉ có ở bước kết thúc)
    finished: bool = False
    success: bool = False
    restart: int = 0            # lần khởi động lại (Random-Restart)


@dataclass
class Result:
    success: bool
    path: list
    cost: float          # chi phí đường đi tìm được (inf nếu thất bại)
    expanded: int        # số bước 'Bước k' (số lần một nút được lấy ra để xét)
    time_ms: float       # thời gian trung vị của `reps` lần chạy lặp lại
    restarts: int = 0
    optimal: float = float("inf")   # chi phí tối ưu (Dijkstra) từ nút đầu của path
    ratio: float = float("nan")     # cost / optimal  (>= 1; =1 là tối ưu)


ALGORITHMS = {
    "Best-First Search": "best_first",
    "Hill Climbing": "hill_climbing",
    "Random-Restart Hill Climbing": "random_restart",
}


# ----------------------------------------------------------------------------
def best_first(graph, start, goal, **_):
    """Greedy Best-First Search: luôn mở rộng nút trong Open có h nhỏ nhất."""
    counter = 0
    open_heap = [(graph.h(start, goal), counter, start)]
    parent = {start: None}
    in_open = {start}
    closed = []
    k = 0
    while open_heap:
        hn, _, n = heapq.heappop(open_heap)
        in_open.discard(n)
        if n in closed:
            continue
        k += 1
        closed.append(n)
        if n == goal:
            path = _build_path(parent, n)
            yield Step(k, n, hn, [], _snapshot(open_heap, in_open), list(closed),
                       f"Bước {k}: lấy {n} ra khỏi Open (h={hn}) -> ĐÍCH! "
                       f"Đường đi: {' -> '.join(path)}",
                       path=path, finished=True, success=True)
            return
        nbs = []
        for m in graph.neighbors(n):
            if m not in closed and m not in in_open:
                counter += 1
                parent[m] = n
                in_open.add(m)
                heapq.heappush(open_heap, (graph.h(m, goal), counter, m))
            nbs.append((m, graph.h(m, goal)))
        yield Step(k, n, hn, nbs, _snapshot(open_heap, in_open), list(closed),
                   f"Bước {k}: mở rộng {n} (h={hn}); thêm láng giềng vào Open, "
                   f"Open được sắp theo h tăng dần.")
    yield Step(k + 1, start, graph.h(start, goal), [], [], list(closed),
               "Open rỗng -> KHÔNG tìm thấy đường đi.", finished=True, success=False)


def _snapshot(heap, in_open):
    return sorted(((n, h) for h, _, n in heap if n in in_open), key=lambda t: t[1])


def _build_path(parent, n):
    path = []
    while n is not None:
        path.append(n)
        n = parent[n]
    return path[::-1]


# ----------------------------------------------------------------------------
def hill_climbing(graph, start, goal, restart=0, k0=0, **_):
    """Steepest-ascent Hill Climbing (cực tiểu hoá h): nhảy sang láng giềng tốt nhất
    nếu nó TỐT HƠN nút hiện tại, ngược lại dừng (cực trị cục bộ / cao nguyên)."""
    cur = start
    path = [cur]
    visited = [cur]
    k = k0
    while True:
        k += 1
        hc = graph.h(cur, goal)
        if cur == goal:
            yield Step(k, cur, hc, [], [], list(visited),
                       f"Bước {k}: {cur} là ĐÍCH (h=0). Thành công.",
                       path=list(path), finished=True, success=True, restart=restart)
            return
        nbs = sorted(((m, graph.h(m, goal)) for m in graph.neighbors(cur)),
                     key=lambda t: t[1])
        best, hb = nbs[0] if nbs else (None, float("inf"))
        if best is not None and hb < hc:
            yield Step(k, cur, hc, nbs, [], list(visited),
                       f"Bước {k}: tại {cur} (h={hc}); láng giềng tốt nhất {best} "
                       f"(h={hb}) < {hc} -> di chuyển.", restart=restart)
            cur = best
            path.append(cur)
            visited.append(cur)
        else:
            yield Step(k, cur, hc, nbs, [], list(visited),
                       f"Bước {k}: tại {cur} (h={hc}); không có láng giềng nào tốt hơn "
                       f"-> KẸT tại cực tiểu cục bộ / cao nguyên.",
                       path=list(path), finished=True, success=False, restart=restart)
            return


# ----------------------------------------------------------------------------
def random_restart(graph, start, goal, max_restarts=10, seed=None, **_):
    """Chạy Hill Climbing lặp lại; lần 0 từ `start`, các lần sau từ nút ngẫu nhiên."""
    rnd = random.Random(seed)
    nodes = [n for n in graph.nodes if n != goal]
    k = 0
    last = None
    for r in range(max_restarts + 1):
        s = start if r == 0 else rnd.choice(nodes)
        if r > 0:
            k += 1
            yield Step(k, s, graph.h(s, goal), [], [], [],
                       f"=== KHỞI ĐỘNG LẠI lần {r}: chọn ngẫu nhiên nút xuất phát {s} ===",
                       restart=r)
        for st in hill_climbing(graph, s, goal, restart=r, k0=k):
            k = st.k
            last = st
            if st.finished and not st.success and r < max_restarts:
                st = Step(**{**st.__dict__, "finished": False})
            if st.finished and st.success:
                st.message += f"  (sau {r} lần khởi động lại)"
            yield st
            if st.finished:
                break
        if last.success:
            return
    # hết số lần khởi động lại
    yield Step(k + 1, last.current, last.h, [], [], last.closed_list,
               f"Đã dùng hết {max_restarts} lần khởi động lại -> THẤT BẠI.",
               path=last.path, finished=True, success=False, restart=max_restarts)


# ----------------------------------------------------------------------------
def get_algorithm(name):
    return globals()[ALGORITHMS.get(name, name)]


def run_to_end(graph, algo, start, goal, reps=1, **kw):
    """Chạy trọn vẹn thuật toán, trả về (danh sách Step, Result).

    - expanded: số Step có thông điệp bắt đầu bằng "Bước" (không tính dòng thông báo
      khởi động lại và dòng kết luận "Open rỗng"/"hết lần khởi động lại").
    - time_ms: trung vị của `reps` lần chạy (loại nhiễu bộ lập lịch/GC); đo bằng
      time.perf_counter, bao gồm cả việc tạo các Step (ghi trace).
    - ratio: cost / chi phí tối ưu tính từ CHÍNH nút bắt đầu của đường đi trả về. Với
      Random-Restart đó là nút của lần khởi động lại thành công, nhờ vậy ba thuật
      toán được so sánh trên cùng một thước đo, không phụ thuộc điểm xuất phát.
    """
    import statistics
    fn = get_algorithm(algo)
    times, steps = [], None
    for _ in range(max(1, reps)):
        t0 = time.perf_counter()
        steps = list(fn(graph, start, goal, **kw))
        times.append((time.perf_counter() - t0) * 1000)
    last = steps[-1]
    expanded = sum(1 for s in steps if s.message.startswith("Bước"))
    if last.success:
        cost = graph.path_cost(last.path)
        opt = graph.shortest_cost(last.path[0], goal)
        ratio = round(cost / opt, 3) if opt > 0 else 1.0
    else:
        cost, opt, ratio = float("inf"), float("inf"), float("nan")
    return steps, Result(last.success, last.path if last.success else [], cost,
                         expanded, statistics.median(times), last.restart, opt, ratio)
