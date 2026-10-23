"""VIEW - Giao diện CustomTkinter: panel điều khiển, canvas trực quan hóa, log trung gian."""
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from model.algorithms import ALGORITHMS

COL_DEFAULT = "#cfd8dc"
COL_CLOSED = "#90a4ae"
COL_OPEN = "#ffe082"
COL_CURRENT = "#ff7043"
COL_START = "#66bb6a"
COL_GOAL = "#ef5350"
COL_PATH = "#1e88e5"


class AppView(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title("Tìm kiếm Heuristic: Best-First Search & Hill Climbing")
        self.geometry("1400x800")
        self.minsize(1100, 650)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(0, weight=1)
        self._build_control_panel()
        self._build_canvas()
        self._build_log_panel()
        self.nx_graph = None
        self.pos = None

    # ------------------------------------------------------------------ panel trái
    def _build_control_panel(self):
        p = ctk.CTkScrollableFrame(self, width=250)
        p.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=10)

        def label(t):
            ctk.CTkLabel(p, text=t, anchor="w",
                         font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=12, pady=(10, 2))

        ctk.CTkLabel(p, text="BẢNG ĐIỀU KHIỂN",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(12, 0))

        label("Thuật toán")
        self.cb_algo = ctk.CTkComboBox(p, values=list(ALGORITHMS.keys()), width=230)
        self.cb_algo.pack(padx=12)

        label("Nút xuất phát (Start)")
        self.cb_start = ctk.CTkComboBox(p, values=[""], width=230)
        self.cb_start.pack(padx=12)

        label("Nút đích (Goal)")
        self.cb_goal = ctk.CTkComboBox(p, values=[""], width=230)
        self.cb_goal.pack(padx=12)

        label("Số lần khởi động lại tối đa")
        self.ent_restart = ctk.CTkEntry(p, width=230)
        self.ent_restart.insert(0, "10")
        self.ent_restart.pack(padx=12)

        label("Đồ thị")
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x", padx=12)
        self.btn_sample = ctk.CTkButton(row, text="Đồ thị mẫu", width=105)
        self.btn_sample.pack(side="left")
        self.btn_random = ctk.CTkButton(row, text="Ngẫu nhiên", width=105)
        self.btn_random.pack(side="right")
        row2 = ctk.CTkFrame(p, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(6, 0))
        ctk.CTkLabel(row2, text="Số nút:").pack(side="left")
        self.ent_n = ctk.CTkEntry(row2, width=60)
        self.ent_n.insert(0, "15")
        self.ent_n.pack(side="left", padx=6)
        ctk.CTkLabel(row2, text="Seed:").pack(side="left")
        self.ent_seed = ctk.CTkEntry(row2, width=60)
        self.ent_seed.insert(0, "1")
        self.ent_seed.pack(side="left", padx=6)

        self.cb_kind = ctk.CTkComboBox(p, values=["Ngẫu nhiên k-NN", "Lưới (grid)"], width=230)
        self.cb_kind.pack(padx=12, pady=(6, 0))
        self.var_rw = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(p, text="Trọng số cạnh ngẫu nhiên", variable=self.var_rw
                        ).pack(anchor="w", padx=14, pady=(6, 0))

        label("Chỉnh sửa cạnh (vd: A-B)")
        self.ent_edge = ctk.CTkEntry(p, width=230, placeholder_text="A-B")
        self.ent_edge.pack(padx=12)
        row3 = ctk.CTkFrame(p, fg_color="transparent")
        row3.pack(fill="x", padx=12, pady=(4, 0))
        self.btn_add_edge = ctk.CTkButton(row3, text="Thêm cạnh", width=105)
        self.btn_add_edge.pack(side="left")
        self.btn_del_edge = ctk.CTkButton(row3, text="Xóa cạnh", width=105,
                                          fg_color="#6d4c41", hover_color="#4e342e")
        self.btn_del_edge.pack(side="right")

        label("Tốc độ mô phỏng")
        self.sl_speed = ctk.CTkSlider(p, from_=0, to=1, number_of_steps=20, width=220)
        self.sl_speed.set(0.6)
        self.sl_speed.pack(padx=12)
        r = ctk.CTkFrame(p, fg_color="transparent")
        r.pack(fill="x", padx=14)
        ctk.CTkLabel(r, text="Chậm").pack(side="left")
        ctk.CTkLabel(r, text="Nhanh").pack(side="right")

        self.btn_run = ctk.CTkButton(p, text="▶  Bắt đầu (Run)", fg_color="#2e7d32",
                                     hover_color="#1b5e20")
        self.btn_run.pack(fill="x", padx=12, pady=(18, 4))
        self.btn_pause = ctk.CTkButton(p, text="⏸  Tạm dừng", fg_color="#f9a825",
                                       hover_color="#f57f17", text_color="black")
        self.btn_pause.pack(fill="x", padx=12, pady=4)
        self.btn_step = ctk.CTkButton(p, text="⏭  Chạy từng bước")
        self.btn_step.pack(fill="x", padx=12, pady=4)
        self.btn_reset = ctk.CTkButton(p, text="↺  Đặt lại (Reset)", fg_color="#c62828",
                                       hover_color="#8e0000")
        self.btn_reset.pack(fill="x", padx=12, pady=4)

    # ------------------------------------------------------------------ giữa
    def _build_canvas(self):
        f = ctk.CTkFrame(self)
        f.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        f.grid_rowconfigure(0, weight=1)
        f.grid_columnconfigure(0, weight=1)
        self.fig, self.ax = plt.subplots(figsize=(7, 6))
        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=f)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.lbl_status = ctk.CTkLabel(f, text="Sẵn sàng.", anchor="w")
        self.lbl_status.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))

    # ------------------------------------------------------------------ phải
    def _build_log_panel(self):
        f = ctk.CTkFrame(self)
        f.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
        f.grid_rowconfigure(1, weight=1)
        f.grid_rowconfigure(3, weight=1)
        f.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f, text="NHẬT KÝ CÁC BƯỚC (TRACING)",
                     font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=(8, 2))
        self.txt_log = ctk.CTkTextbox(f, wrap="word", font=("Consolas", 12))
        self.txt_log.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        ctk.CTkLabel(f, text="TRẠNG THÁI Open / Closed HIỆN TẠI",
                     font=ctk.CTkFont(weight="bold")).grid(row=2, column=0, pady=(6, 2))
        self.txt_state = ctk.CTkTextbox(f, wrap="word", font=("Consolas", 12))
        self.txt_state.grid(row=3, column=0, sticky="nsew", padx=8, pady=(4, 8))

    # ================================================================== API cho Controller
    def set_nodes(self, nodes):
        self.cb_start.configure(values=nodes)
        self.cb_goal.configure(values=nodes)

    def get_params(self):
        """Đọc và KIỂM TRA dữ liệu nhập; ném ValueError kèm thông báo tiếng Việt."""
        def to_int(e, name, lo, hi):
            try:
                v = int(e.get().strip())
            except ValueError:
                raise ValueError(f"'{name}' phải là số nguyên.")
            if not lo <= v <= hi:
                raise ValueError(f"'{name}' phải nằm trong khoảng {lo}..{hi}.")
            return v
        return dict(algo=self.cb_algo.get(), start=self.cb_start.get(),
                    goal=self.cb_goal.get(),
                    max_restarts=to_int(self.ent_restart, "Số lần khởi động lại", 0, 1000),
                    n=to_int(self.ent_n, "Số nút", 5, 60),
                    seed=to_int(self.ent_seed, "Seed", 0, 10**9),
                    kind=self.cb_kind.get(), random_weights=self.var_rw.get(),
                    edge=self.ent_edge.get().strip())

    def set_start_goal(self, s, g):
        self.cb_start.set(s)
        self.cb_goal.set(g)

    def delay_ms(self):
        return int(1500 * (1 - self.sl_speed.get())) + 30

    def set_status(self, text):
        self.lbl_status.configure(text=text)

    def clear_log(self):
        self.txt_log.delete("1.0", "end")
        self.txt_state.delete("1.0", "end")

    def append_log(self, step):
        self.txt_log.insert("end", step.message + "\n")
        if step.neighbors:
            nb = ", ".join(f"{n}(h={h})" for n, h in step.neighbors)
            self.txt_log.insert("end", f"      láng giềng: {nb}\n")
        self.txt_log.see("end")
        self.txt_state.delete("1.0", "end")
        op = ", ".join(f"({n}, {h})" for n, h in step.open_list) or "—"
        cl = ", ".join(step.closed_list) or "—"
        self.txt_state.insert("end", f"Bước k = {step.k}\nNút đang xét: {step.current}"
                                     f"  h = {step.h}\n\nOpen  : [{op}]\n\nClosed: [{cl}]\n")
        if step.restart:
            self.txt_state.insert("end", f"\nLần khởi động lại: {step.restart}\n")

    # ------------------------------------------------------------------ vẽ đồ thị
    def draw(self, graph, start=None, goal=None, step=None):
        G = nx.Graph()
        for n in graph.nodes:
            G.add_node(n)
        for a in graph.nodes:
            for b, w in graph.adj[a].items():
                if a < b:
                    G.add_edge(a, b, weight=w)
        pos = {n: graph.pos[n] for n in graph.nodes}
        open_nodes = {n for n, _ in step.open_list} if step else set()
        closed = set(step.closed_list) if step else set()
        path = step.path if (step and step.finished and step.success) else []

        colors = []
        for n in G.nodes:
            c = COL_DEFAULT
            if n in closed:
                c = COL_CLOSED
            if n in open_nodes:
                c = COL_OPEN
            if n == start:
                c = COL_START
            if n == goal:
                c = COL_GOAL
            if step and n == step.current:
                c = COL_CURRENT
            if n in path and n not in (start, goal):
                c = COL_PATH
            colors.append(c)

        path_edges = {tuple(sorted(e)) for e in zip(path, path[1:])}
        e_cols = [COL_PATH if tuple(sorted(e)) in path_edges else "#b0bec5" for e in G.edges]
        e_wid = [4 if tuple(sorted(e)) in path_edges else 1.2 for e in G.edges]

        self.ax.clear()
        nx.draw_networkx_edges(G, pos, ax=self.ax, edge_color=e_cols, width=e_wid)
        nx.draw_networkx_nodes(G, pos, ax=self.ax, node_color=colors, node_size=650,
                               edgecolors="#37474f")
        nx.draw_networkx_labels(G, pos, ax=self.ax, font_size=9, font_weight="bold")
        if len(G) <= 25:
            nx.draw_networkx_edge_labels(
                G, pos, ax=self.ax, font_size=7,
                edge_labels={e: G.edges[e]["weight"] for e in G.edges})
        if goal:
            for n, (x, y) in pos.items():
                self.ax.text(x, y - 5.5, f"h={graph.h(n, goal)}", ha="center",
                             fontsize=7, color="#455a64")
        legend = [("Start", COL_START), ("Goal", COL_GOAL), ("Đang xét", COL_CURRENT),
                  ("Open", COL_OPEN), ("Closed", COL_CLOSED), ("Đường đi", COL_PATH)]
        for t, c in legend:
            self.ax.scatter([], [], c=c, s=80, label=t, edgecolors="#37474f")
        self.ax.legend(loc="upper center", ncol=6, fontsize=8, frameon=False,
                       bbox_to_anchor=(0.5, 1.07))
        self.ax.axis("off")
        self.ax.margins(0.08)
        self.fig.tight_layout()
        self.canvas.draw_idle()
