# CafePOS (bản đơn giản)

Ứng dụng nhập đơn hàng, tự tính tiền, hiển thị danh sách và xuất Excel.

## Chạy trên máy tính
1. Cài Python 3.10 trở lên.
2. Mở Terminal tại thư mục dự án.
3. Chạy:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```
4. Trình duyệt sẽ mở ứng dụng.

## Cách dùng
- Vào tab **Nhập đơn hàng** để nhập thông tin và bấm **Lưu đơn hàng**.
- Vào tab **Danh sách đơn** để xem các đơn và doanh thu.
- Vào tab **Xuất Excel** để tải file `CafePOS.xlsx`.
- Lần sử dụng sau, tải file Excel vừa xuất lên ở thanh bên, bấm **Nạp file Excel**, rồi nhập tiếp.

## Công thức
Tiền hàng = Số lượng × Đơn giá  
Tiền giảm = Tiền hàng × Chiết khấu (%)  
Tiền VAT = (Tiền hàng − Tiền giảm) × VAT (%)  
Tổng thanh toán = Tiền hàng − Tiền giảm + Tiền VAT

## Lưu ý quan trọng
Bản này không dùng database. Dữ liệu làm việc nằm trong phiên trình duyệt; cần tải file Excel xuống để lưu. Khi mở ứng dụng lần sau, nạp lại file Excel đã lưu để tiếp tục.
