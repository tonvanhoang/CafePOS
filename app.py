import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
from datetime import date
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="CafePOS Database", page_icon="☕", layout="wide")

st.title("☕ CafePOS – Quản lý đơn hàng (Lưu Database SQLite)")
st.caption("Nhập đơn hàng tự động lưu vào database, tự tính tiền, xem danh sách, thống kê biểu đồ cột.")

# --- CƠ SỞ DỮ LIỆU SQLITE ---
DB_NAME = "cafepos.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stt INTEGER,
            ngay TEXT,
            khach_hang TEXT,
            san_pham TEXT,
            so_luong INTEGER,
            don_gia INTEGER,
            tien_hang INTEGER,
            chiet_khau INTEGER,
            tien_giam INTEGER,
            vat INTEGER,
            tien_vat INTEGER,
            tong_thanh_toan INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

COLUMNS = [
    "STT", "Ngày", "Khách hàng", "Sản phẩm", "Số lượng",
    "Đơn giá", "Tiền hàng", "Chiết khấu (%)", "Tiền giảm",
    "VAT (%)", "Tiền VAT", "Tổng thanh toán"
]

def load_data_from_db():
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql("SELECT stt AS STT, ngay AS Ngày, khach_hang AS `Khách hàng`, san_pham AS `Sản phẩm`, so_luong AS `Số lượng`, don_gia AS `Đơn giá`, tien_hang AS `Tiền hàng`, chiet_khau AS `Chiết khấu (%)`, tien_giam AS `Tiền giảm`, vat AS `VAT (%)`, tien_vat AS `Tiền VAT`, tong_thanh_toan AS `Tổng thanh toán` FROM orders", conn)
    except Exception:
        df = pd.DataFrame(columns=COLUMNS)
    conn.close()
    return df

def save_order_to_db(row):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (stt, ngay, khach_hang, san_pham, so_luong, don_gia, tien_hang, chiet_khau, tien_giam, vat, tien_vat, tong_thanh_toan)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        row["STT"], row["Ngày"], row["Khách hàng"], row["Sản phẩm"], 
        row["Số lượng"], row["Đơn giá"], row["Tiền hàng"], row["Chiết khấu (%)"], 
        row["Tiền giảm"], row["VAT (%)"], row["Tiền VAT"], row["Tổng thanh toán"]
    ))
    conn.commit()
    conn.close()

def clear_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS orders")
    conn.commit()
    conn.close()
    init_db()

# Danh sách 50 món nước phổ biến
DRINK_MENU = [
    "-- Chọn món nước --",
    "Cà phê đen đá", "Cà phê đen nóng", "Cà phê sữa đá", "Cà phê sữa nóng",
    "Bạc xỉu đá", "Bạc xỉu nóng", "Cà phê muối", "Cà phê cốt dừa",
    "Cà phê trứng", "Espresso", "Americano đá", "Americano nóng",
    "Latte đá", "Latte nóng", "Cappuccino", "Mocha",
    "Caramel Macchiato", "Cold Brew truyền thống", "Cold Brew cam sả", "Trà đào cam sả",
    "Trà vải hoa hồng", "Trà dâu tằm", "Trà ổi hồng", "Trà chanh giã tay",
    "Trà tắc mật ong", "Trà gừng mật ong", "Trà sen vàng", "Trà sữa truyền thống",
    "Trà sữa trân châu đường đen", "Trà sữa ô long", "Trà sữa thái xanh", "Trà sữa thái đỏ",
    "Matcha đá xay", "Matcha Latte", "Socola đá xay", "Socola nóng",
    "Cacao sữa đá", "Cacao nóng", "Nước cam ép", "Nước ép dưa hấu",
    "Nước ép thơm (dứa)", "Nước ép cà rốt", "Nước ép táo", "Nước ép ổi",
    "Sinh tố bơ", "Sinh tố xoài", "Sinh tố dâu", "Sinh tố việt quất",
    "Sữa chua đánh đá", "Sữa chua việt quất"
]

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="DonHang")
        ws = writer.book["DonHang"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="234E52")
            cell.alignment = Alignment(horizontal="center")
        widths = [8, 14, 24, 28, 12, 16, 16, 16, 16, 12, 16, 20]
        for idx, width in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(idx)].width = width
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.column in [6, 7, 9, 11, 12]:
                    cell.number_format = '#,##0" đ"'
    output.seek(0)
    return output.getvalue()

# Lấy dữ liệu từ Database lên session state mỗi khi chạy app
if "orders" not in st.session_state:
    st.session_state.orders = load_data_from_db()

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Nhập đơn hàng",
    "📋 Danh sách đơn",
    "📊 Thống kê & Biểu đồ",
    "📤 Xuất Excel"
])

with tab1:
    st.subheader("Thông tin đơn hàng")
    with st.form("order_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            order_date = st.date_input("Ngày bán", value=date.today())
            customer = st.text_input("Tên khách hàng", placeholder="Ví dụ: Bàn 1 / Anh Nam")
            product = st.selectbox("Chọn món nước", options=DRINK_MENU)
            quantity = st.number_input("Số lượng", min_value=1, value=1, step=1)
        with c2:
            unit_price = st.number_input(
                "Đơn giá (VNĐ) *",
                min_value=0,
                value=None,
                step=1000,
                placeholder="Bắt buộc nhập giá (VD: 25000)"
            )
            discount = st.number_input("Chiết khấu (%)", min_value=0, max_value=100, value=0, step=1, format="%d")
            vat = st.number_input("VAT (%)", min_value=0, max_value=100, value=8, step=1, format="%d")
        submitted = st.form_submit_button("Lưu đơn hàng", type="primary", use_container_width=True)

    if submitted:
        if product == "-- Chọn món nước --":
            st.error("⚠️ Vui lòng chọn một món nước trong danh sách!")
        elif unit_price is None or unit_price <= 0:
            st.error("⚠️ Vui lòng nhập đơn giá hợp lệ (lớn hơn 0 đ) trước khi lưu đơn!")
        else:
            subtotal = int(quantity) * int(unit_price)
            discount_amount = round(subtotal * int(discount) / 100)
            taxable = subtotal - discount_amount
            vat_amount = round(taxable * int(vat) / 100)
            total = taxable + vat_amount
            
            current_df = load_data_from_db()
            next_stt = len(current_df) + 1
            
            row = {
                "STT": next_stt,
                "Ngày": order_date.strftime("%d/%m/%Y"),
                "Khách hàng": customer.strip() or "Khách lẻ",
                "Sản phẩm": product,
                "Số lượng": int(quantity),
                "Đơn giá": int(unit_price),
                "Tiền hàng": subtotal,
                "Chiết khấu (%)": int(discount),
                "Tiền giảm": discount_amount,
                "VAT (%)": int(vat),
                "Tiền VAT": vat_amount,
                "Tổng thanh toán": total,
            }
            
            # Lưu vào Database SQLite vật lý
            save_order_to_db(row)
            # Cập nhật lại session state
            st.session_state.orders = load_data_from_db()
            
            st.success(f"✅ Đã lưu vào Database thành công: {quantity} x {product}. Tổng: {total:,.0f} đ")

with tab2:
    st.subheader("Danh sách đơn hàng (Lưu trữ từ Database)")
    if st.button("🔄 Làm mới dữ liệu"):
        st.session_state.orders = load_data_from_db()
        st.rerun()
        
    df_current = load_data_from_db()
    if len(df_current) > 0:
        st.dataframe(df_current, use_container_width=True, hide_index=True)
        total_revenue = pd.to_numeric(df_current["Tổng thanh toán"], errors="coerce").fillna(0).sum()
        m1, m2 = st.columns(2)
        m1.metric("Tổng số đơn", f"{len(df_current):,}")
        m2.metric("Tổng doanh thu", f"{total_revenue:,.0f} đ")
        
        if st.button("🗑️ Xóa sạch toàn bộ Database"):
            clear_db()
            st.session_state.orders = load_data_from_db()
            st.success("Đã xóa sạch dữ liệu trong database!")
            st.rerun()
    else:
        st.info("Chưa có đơn hàng nào trong database.")

with tab3:
    st.subheader("📊 Biểu đồ hình cột Top 10 món nước được order nhiều nhất")
    df_current = load_data_from_db()
    if len(df_current) > 0:
        df_clean = df_current.copy()
        df_clean["Số lượng"] = pd.to_numeric(df_clean["Số lượng"], errors="coerce").fillna(0).clip(lower=0)

        df_top10 = (
            df_clean.groupby("Sản phẩm")["Số lượng"]
            .sum()
            .clip(lower=0)
            .reset_index(name="Tổng số lượng bán")
            .sort_values(by="Tổng số lượng bán", ascending=False)
            .head(10)
            .set_index("Sản phẩm")
        )
        st.bar_chart(df_top10["Tổng số lượng bán"])
        st.caption("Biểu đồ cột thể hiện tổng số lượng bán ra của 10 món nước được gọi nhiều nhất.")

        st.divider()

        st.subheader("📈 Biểu đồ xu hướng số lượng bán ra (Lũy kế)")
        top_products = df_top10.index.tolist()
        df_filtered = df_clean[df_clean["Sản phẩm"].isin(top_products)]

        df_pivot = (
            df_filtered.pivot_table(
                index="STT",
                columns="Sản phẩm",
                values="Số lượng",
                aggfunc="sum"
            )
            .fillna(0)
            .clip(lower=0)
            .cumsum()
        )
        st.line_chart(df_pivot)
    else:
        st.info("Chưa có dữ liệu để vẽ biểu đồ.")

with tab4:
    st.subheader("Tải dữ liệu về máy")
    df_current = load_data_from_db()
    st.download_button(
        "⬇️ Tải CafePOS.xlsx",
        data=to_excel(df_current),
        file_name="CafePOS.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )
