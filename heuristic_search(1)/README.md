# Tìm kiếm Heuristic: Best-First Search & Hill Climbing (Python GUI)

Bài toán: tìm đường trên đồ thị có toạ độ, heuristic h(n) = khoảng cách Euclid tới đích.
Ba thuật toán: **Best-First Search** (greedy), **Hill Climbing** (steepest, cực tiểu hoá h),
**Random-Restart Hill Climbing**.

## Cài đặt & chạy
```
pip install -r requirements.txt
python main.py                              # giao diện
python benchmark.py [số_mẫu]                # mặc định 200 đồ thị / ô -> CSV + PNG
python -m unittest discover -s tests -v     # kiểm thử tự động (9 test)
```
Cần Python 3.9+ có tkinter (Ubuntu: `sudo apt install python3-tk`).

## Cấu trúc MVC
```
main.py                 khởi chạy
controller.py           CONTROLLER: Run/Step/Pause/Reset, kiểm tra input, sửa cạnh
view/app_view.py        VIEW: CustomTkinter + Matplotlib/NetworkX, log trung gian
model/graph_model.py    MODEL: đồ thị, h(n), Dijkstra (chỉ để đánh giá), đồ thị mẫu/k-NN/lưới
model/algorithms.py     MODEL: 3 thuật toán dạng generator (mỗi bước = một Step), run_to_end
benchmark.py            thực nghiệm; tests/  kiểm thử
```

## Giao diện
Chọn thuật toán, Start, Goal; **Bắt đầu** chạy tự động (thanh trượt chỉnh tốc độ), **Chạy từng bước**,
**Đặt lại**. Màu nút: xanh lá = Start, đỏ = Goal, cam = đang xét, vàng = Open, xám xanh = Closed,
xanh dương = đường đi. Cột phải: nhật ký từng bước và tập Open/Closed. Có thể sinh đồ thị k-NN hoặc
lưới (tuỳ chọn trọng số ngẫu nhiên) và **thêm/xóa cạnh** bằng ô nhập dạng `A-B`. Dữ liệu nhập được kiểm tra
(số nút 5..60, số lần khởi động lại 0..1000, seed là số nguyên, tên nút tồn tại, Start ≠ Goal).

## Cách tính các chỉ số (benchmark)
| Chỉ số | Định nghĩa |
|---|---|
| success | % số đồ thị mà thuật toán tới được Goal; kèm khoảng tin cậy 95% Wilson |
| expanded | số bước "Bước k" (số lần một nút được lấy ra xét); không tính dòng thông báo khởi động lại / dòng kết luận. Với Random-Restart là tổng qua mọi lần khởi động lại |
| time_ms | trung vị của 5 lần chạy liên tiếp (`time.perf_counter`), gồm cả chi phí ghi trace (Step); sau đó lấy trung bình ± SD qua các đồ thị |
| ratio | chi phí đường đi / chi phí tối ưu (Dijkstra) tính từ **chính nút đầu của đường đi**; chỉ trên các lần thành công; trung bình ± CI95 (1.96·s/√n). ratio = 1 là tối ưu |

`ratio` thay cho chi phí tuyệt đối để ba thuật toán so sánh công bằng: Random-Restart có thể thành công
từ nút xuất phát ngẫu nhiên khác Start, nên chi phí tuyệt đối không so sánh được trực tiếp.

Thiết kế: 3 họ đồ thị (`knn` trọng số Euclid; `grid` lưới bỏ bớt cạnh, nhiều ngõ cụt; `knn-rw` k-NN với
trọng số cạnh ngẫu nhiên), 4 cỡ (~10/20/40/80 nút), 200 đồ thị mỗi ô, cùng đồ thị và cặp (Start, Goal)
cho cả ba thuật toán (hạt giống cố định, tái lập được).
Lưu ý: `knn` và `knn-rw` có cùng vị trí nút nên success/expanded giống hệt nhau (các thuật toán chỉ nhìn h,
không nhìn trọng số cạnh); chỉ `ratio` khác. Đó là hệ quả của thiết kế, không phải lỗi.

## Cách kiểm chứng kết quả
- `tests/test_algorithms.py` kiểm tra: đường đi trên đồ thị mẫu; Hill Climbing kẹt cực tiểu cục bộ và cao
  nguyên; Best-First không tối ưu (ví dụ dựng sẵn, ratio > 6); Random-Restart với 0 lần khởi động lại =
  Hill Climbing; các bộ sinh đồ thị luôn liên thông; Dijkstra khớp `networkx.shortest_path_length`
  trên 120 đồ thị; Best-First luôn thành công trên đồ thị liên thông.
- Tự kiểm tay: chạy "Chạy từng bước" trên đồ thị mẫu rồi đối chiếu bảng Open/Closed với ví dụ trong báo cáo.

## Hạn chế đã biết
1. **Best-First** (greedy) không đảm bảo đường đi ngắn nhất (có test minh họa). Nó luôn tìm được đường
   trên đồ thị hữu hạn liên thông nhờ tập Closed.
2. **Hill Climbing** có thể kẹt ở cực tiểu cục bộ hoặc cao nguyên (dừng khi không có láng giềng *tốt hơn hẳn*).
   **Random-Restart** tăng xác suất thành công nhưng không đảm bảo (số lần khởi động lại có giới hạn).
3. Khoảng tin cậy của `ratio` dùng xấp xỉ chuẩn; với ô có ít lần thành công (Hill Climbing ở đồ thị lớn) nó
   kém tin cậy hơn. `expanded` và thời gian là số đo của cài đặt Python này (có ghi trace), không phải
   độ phức tạp tiệm cận; thời gian nhỏ (~0.01-0.1 ms) nên chịu ảnh hưởng của máy và trình thông dịch.
4. Chỉ có 3 họ đồ thị hình học (2D, heuristic Euclid); chưa có đồ thị có hướng, đồ thị thực tế hay heuristic khác.
5. GUI: sửa đồ thị mới ở mức thêm/xóa cạnh (không kéo-thả nút, không đổi trọng số tay). Phần GUI chưa
   được kiểm thử tự động (cần màn hình); phần Model/Controller-logic độc lập với GUI đã được kiểm thử.

## Tiếng Việt / mã hóa
Mọi file `.py`, `README.md` là UTF-8 (có test kiểm tra). `benchmark_results.csv` ghi UTF-8 có BOM để Excel mở
đúng. Matplotlib dùng phông DejaVu Sans nên hiển thị đủ dấu tiếng Việt trong biểu đồ và trên canvas.
