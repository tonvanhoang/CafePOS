import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="CafePOS", page_icon="☕", layout="wide")

st.title("☕ CafePOS – Quản lý đơn hàng")
st.caption("Nhập đơn hàng, tự tính tiền, xem danh sách và tải dữ liệu Excel.")

COLUMNS = [
    "STT", "Ngày", "Khách hàng", "Sản phẩm", "Số lượng",
    "Đơn giá", "Tiền hàng", "Chiết khấu (%)", "Tiền giảm",
    "VAT (%)", "Tiền VAT", "Tổng thanh toán"
]

def new_workbook_df():
    return pd.DataFrame(columns=COLUMNS)

def read_excel(uploaded):
    if uploaded is None:
        return new_workbook_df()
    try:
        df = pd.read_excel(uploaded, sheet_name="DonHang")
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df[COLUMNS]
    except Exception as exc:
        st.error(f"Không đọc được file Excel: {exc}")
        return new_workbook_df()

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
        widths = [8, 14, 24, 24, 12, 16, 16, 16, 16, 12, 16, 20]
        for idx, width in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(idx)].width = width
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.column in [6, 7, 9, 11, 12]:
                    cell.number_format = '#,##0" đ"'
    output.seek(0)
    return output.getvalue()

if "orders" not in st.session_state:
    st.session_state.orders = new_workbook_df()
if "loaded" not in st.session_state:
    st.session_state.loaded = False

with st.sidebar:
    st.header("📁 Dữ liệu Excel")
    uploaded = st.file_uploader("Tải file Excel hiện có để nhập tiếp", type=["xlsx"])
    if st.button("Nạp file Excel", use_container_width=True):
        st.session_state.orders = read_excel(uploaded)
        st.session_state.loaded = True
        st.success(f"Đã nạp {len(st.session_state.orders)} dòng.")
    st.info("Nếu chưa có file, bạn có thể nhập đơn mới ngay. Sau khi nhập, hãy tải file Excel xuống để lưu dữ liệu.")

tab1, tab2, tab3 = st.tabs(["➕ Nhập đơn hàng", "📋 Danh sách đơn", "📤 Xuất Excel"])

with tab1:
    st.subheader("Thông tin đơn hàng")
    with st.form("order_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            order_date = st.date_input("Ngày bán", value=date.today())
            customer = st.text_input("Tên khách hàng", placeholder="Ví dụ: Nguyễn Văn A")
            product = st.text_input("Tên sản phẩm", placeholder="Ví dụ: Cà phê sữa")
            quantity = st.number_input("Số lượng", min_value=1, value=1, step=1)
        with c2:
            unit_price = st.number_input("Đơn giá (VNĐ)", min_value=0, value=25000, step=1000)
            discount = st.number_input("Chiết khấu (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            vat = st.number_input("VAT (%)", min_value=0.0, max_value=100.0, value=8.0, step=0.5)
        submitted = st.form_submit_button("Lưu đơn hàng", type="primary", use_container_width=True)

    if submitted:
        subtotal = int(quantity) * int(unit_price)
        discount_amount = round(subtotal * discount / 100)
        taxable = subtotal - discount_amount
        vat_amount = round(taxable * vat / 100)
        total = taxable + vat_amount
        row = {
            "STT": len(st.session_state.orders) + 1,
            "Ngày": order_date.strftime("%d/%m/%Y"),
            "Khách hàng": customer.strip() or "Khách lẻ",
            "Sản phẩm": product.strip(),
            "Số lượng": int(quantity),
            "Đơn giá": int(unit_price),
            "Tiền hàng": subtotal,
            "Chiết khấu (%)": float(discount),
            "Tiền giảm": discount_amount,
            "VAT (%)": float(vat),
            "Tiền VAT": vat_amount,
            "Tổng thanh toán": total,
        }
        if not product.strip():
            st.error("Vui lòng nhập tên sản phẩm.")
        else:
            st.session_state.orders = pd.concat(
                [st.session_state.orders, pd.DataFrame([row])], ignore_index=True
            )
            st.success(f"Đã thêm đơn hàng. Tổng thanh toán: {total:,.0f} đ")

with tab2:
    st.subheader("Danh sách đơn hàng")
    if len(st.session_state.orders):
        st.dataframe(st.session_state.orders, use_container_width=True, hide_index=True)
        total_revenue = pd.to_numeric(st.session_state.orders["Tổng thanh toán"], errors="coerce").fillna(0).sum()
        m1, m2 = st.columns(2)
        m1.metric("Tổng số đơn", f"{len(st.session_state.orders):,}")
        m2.metric("Tổng doanh thu", f"{total_revenue:,.0f} đ")
        if st.button("Xóa toàn bộ dữ liệu trong phiên này"):
            st.session_state.orders = new_workbook_df()
            st.rerun()
    else:
        st.info("Chưa có đơn hàng. Hãy nhập đơn ở tab “Nhập đơn hàng”.")

with tab3:
    st.subheader("Tải dữ liệu về máy")
    st.write("File Excel gồm toàn bộ đơn hàng hiện có trong phiên làm việc.")
    st.download_button(
        "⬇️ Tải CafePOS.xlsx",
        data=to_excel(st.session_state.orders),
        file_name="CafePOS.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )
    st.warning("Lưu ý: ứng dụng không lưu dữ liệu lâu dài trên máy chủ. Sau mỗi lần làm việc, hãy tải file Excel xuống. Lần sau, tải chính file đó lên ở thanh bên để nhập tiếp.")
