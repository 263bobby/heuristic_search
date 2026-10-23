"""CONTROLLER - Kết nối View và Model, điều khiển vòng lặp mô phỏng."""
from tkinter import messagebox

from model.algorithms import get_algorithm
from model.graph_model import Graph


class Controller:
    def __init__(self, view):
        self.view = view
        self.graph = None
        self.gen = None
        self.last_step = None
        self.running = False
        self.finished = False
        self._job = None

        v = view
        v.btn_run.configure(command=self.on_run)
        v.btn_pause.configure(command=self.on_pause)
        v.btn_step.configure(command=self.on_step)
        v.btn_reset.configure(command=self.on_reset)
        v.btn_sample.configure(command=self.load_sample)
        v.btn_random.configure(command=self.load_random)
        v.btn_add_edge.configure(command=lambda: self.edit_edge(True))
        v.btn_del_edge.configure(command=lambda: self.edit_edge(False))
        self.load_sample()

    # ------------------------------------------------------------------ đồ thị
    def _set_graph(self, g, start, goal):
        self.graph = g
        self.view.set_nodes(g.nodes)
        self.view.set_start_goal(start, goal)
        self.on_reset()

    def load_sample(self):
        self._set_graph(Graph.sample(), "A", "J")

    def _params(self):
        try:
            return self.view.get_params()
        except ValueError as e:
            messagebox.showwarning("Dữ liệu không hợp lệ", str(e))
            return None

    def load_random(self):
        p = self._params()
        if p is None:
            return
        w = "random" if p["random_weights"] else "euclid"
        if p["kind"].startswith("Lưới"):
            g = Graph.grid_graph(p["n"], seed=p["seed"], weights=w)
        else:
            g = Graph.random_graph(p["n"], seed=p["seed"], weights=w)
        nodes = g.nodes
        # chọn hai nút xa nhau nhất làm start/goal mặc định
        s, t = max(((a, b) for a in nodes for b in nodes if a < b),
                   key=lambda ab: g.euclid(*ab))
        self._set_graph(g, s, t)

    def edit_edge(self, add):
        p = self._params()
        if p is None:
            return
        parts = [x.strip() for x in p["edge"].replace(",", "-").split("-")]
        if len(parts) != 2 or not all(parts):
            messagebox.showwarning("Sai định dạng", "Nhập cạnh dạng A-B (tên hai nút).")
            return
        a, b = parts
        if a not in self.graph.pos or b not in self.graph.pos or a == b:
            messagebox.showwarning("Nút không tồn tại", f"Nút '{a}' hoặc '{b}' không hợp lệ.")
            return
        if add:
            self.graph.add_edge(a, b)
        elif b in self.graph.adj[a]:
            self.graph.remove_edge(a, b)
        else:
            messagebox.showinfo("Không có cạnh", f"Không có cạnh {a}-{b}.")
            return
        self.on_reset()

    # ------------------------------------------------------------------ mô phỏng
    def _cancel_job(self):
        if self._job is not None:
            self.view.after_cancel(self._job)
            self._job = None

    def _ensure_generator(self):
        if self.gen is not None:
            return True
        p = self._params()
        if p is None:
            return False
        if p["start"] not in self.graph.nodes or p["goal"] not in self.graph.nodes:
            messagebox.showwarning("Thiếu dữ liệu", "Hãy chọn nút Start và Goal hợp lệ.")
            return False
        if p["start"] == p["goal"]:
            messagebox.showwarning("Dữ liệu sai", "Start và Goal phải khác nhau.")
            return False
        self.start, self.goal = p["start"], p["goal"]
        fn = get_algorithm(p["algo"])
        self.gen = fn(self.graph, self.start, self.goal,
                      max_restarts=p["max_restarts"], seed=p["seed"])
        self.view.clear_log()
        return True

    def _advance(self):
        """Thực hiện đúng một bước; trả về False nếu đã kết thúc."""
        if self.finished or not self._ensure_generator():
            return False
        try:
            step = next(self.gen)
        except StopIteration:
            self.finished = True
            return False
        self.last_step = step
        self.view.append_log(step)
        self.view.draw(self.graph, self.start, self.goal, step)
        if step.finished:
            self.finished = True
            if step.success:
                cost = self.graph.path_cost(step.path)
                self.view.set_status(
                    f"THÀNH CÔNG | đường đi: {' -> '.join(step.path)} | chi phí = {cost} "
                    f"| số bước = {step.k}")
            else:
                self.view.set_status(f"THẤT BẠI | dừng tại {step.current} | số bước = {step.k}")
            return False
        self.view.set_status(f"Đang chạy... bước {step.k}, nút {step.current}")
        return True

    def _tick(self):
        self._job = None
        if not self.running:
            return
        if self._advance():
            self._job = self.view.after(self.view.delay_ms(), self._tick)
        else:
            self.running = False

    def on_run(self):
        if self.finished:
            self.on_reset(keep_params=True)
        self.running = True
        self._cancel_job()
        self._tick()

    def on_pause(self):
        self.running = False
        self._cancel_job()
        self.view.set_status("Đã tạm dừng.")

    def on_step(self):
        self.running = False
        self._cancel_job()
        if self.finished:
            self.on_reset(keep_params=True)
        self._advance()

    def on_reset(self, keep_params=False):
        self.running = False
        self._cancel_job()
        self.gen = None
        self.finished = False
        self.last_step = None
        self.view.clear_log()
        self.start, self.goal = self.view.cb_start.get(), self.view.cb_goal.get()
        self.view.draw(self.graph, self.start, self.goal)
        self.view.set_status("Sẵn sàng. Chọn thuật toán rồi nhấn Bắt đầu hoặc Chạy từng bước.")
