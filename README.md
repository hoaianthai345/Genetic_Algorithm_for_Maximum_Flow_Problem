# GA Maximum Flow Solver

Ứng dụng giải bài toán luồng cực đại (maximum flow problem) sử dụng thuật toán di truyền (Genetic Algorithm).

## Tính năng

- Tạo đồ thị luồng có hướng với giao diện đồ họa
- Tạo đồ thị ngẫu nhiên với số lượng lớp và nút tùy chọn
- Giải quyết vấn đề luồng cực đại bằng thuật toán di truyền
- Trực quan hóa kết quả và theo dõi quá trình tiến hóa
- Hiển thị top 5 giải pháp tốt nhất
- Cơ chế đột biến thích nghi để thoát khỏi tối ưu cục bộ

## Cài đặt

1. Clone repository:
```bash
git clone https://github.com/username/ga-maxflow.git
cd ga-maxflow
```

2. Cài đặt các thư viện phụ thuộc:
```bash
pip install -r requirements.txt
```

## Sử dụng

1. Chạy ứng dụng:
```bash
python main.py
```

2. Sử dụng giao diện để:
   - Tạo đồ thị mới bằng cách thêm nút và cạnh
   - Tạo đồ thị ngẫu nhiên với các tham số tùy chỉnh
   - Thiết lập tham số cho thuật toán di truyền
   - Chạy thuật toán và xem kết quả

## Cấu trúc dự án

- `main.py`: Điểm khởi đầu của ứng dụng
- `logic/ga_solver.py`: Thuật toán di truyền để giải bài toán luồng cực đại
- `ui/`: Các thành phần giao diện người dùng
  - `main_window.py`: Cửa sổ chính của ứng dụng
  - `graph_editor.py`: Trình soạn thảo đồ thị tương tác
  - `control_panel.py`: Bảng điều khiển với các tham số thuật toán
  - `result_panel.py`: Hiển thị kết quả và biểu đồ

## Thuật toán di truyền

- **Biểu diễn cá thể**: Từ điển `{(u,v): flow_value}` ánh xạ mỗi cạnh với giá trị luồng
- **Đột biến thích nghi**: Tự động điều chỉnh tỷ lệ đột biến dựa trên quá trình hội tụ
- **Lai ghép dựa trên đường đi**: Kết hợp các đường tăng luồng từ hai cá thể cha mẹ
- **Bảo toàn luồng**: Đảm bảo luồng vào = luồng ra tại mỗi nút trung gian 