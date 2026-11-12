
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="CafePOS", page_icon="☕", layout="wide")

st.title("☕ CafePOS – Quản lý đơn hàng")
st.caption("Quản lý đơn hàng, tính tiền, thống kê doanh thu và xuất Excel.")

# ==============================
# DANH SÁCH MÓN NƯỚC
# ==============================

DRINK_MENU = [
    "-- Chọn món nước --",
    "Cà phê đen đá", "Cà phê đen nóng", "Cà phê sữa đá", "Cà phê sữa nóng",
    "Bạc xỉu đá", "Bạc xỉu nóng", "Cà phê muối", "Cà phê cốt dừa",
    "Cà phê trứng", "Espresso", "Americano đá", "Americano nóng",
    "Latte đá", "Latte nóng", "Cappuccino", "Mocha",
    "Caramel Macchiato", "Cold Brew truyền thống", "Cold Brew cam sả",
    "Trà đào cam sả", "Trà vải hoa hồng", "Trà dâu tằm", "Trà ổi hồng",
    "Trà chanh giã tay", "Trà tắc mật ong", "Trà gừng mật ong",
    "Trà sen vàng", "Trà sữa truyền thống",
    "Trà sữa trân châu đường đen", "Trà sữa ô long",
    "Trà sữa thái xanh", "Trà sữa thái đỏ",
    "Matcha đá xay", "Matcha Latte", "Socola đá xay", "Socola nóng",
    "Cacao sữa đá", "Cacao nóng", "Nước cam ép", "Nước ép dưa hấu",
    "Nước ép thơm (dứa)", "Nước ép cà rốt", "Nước ép táo",
    "Nước ép ổi", "Sinh tố bơ", "Sinh tố xoài", "Sinh tố dâu",
    "Sinh tố việt quất", "Sữa chua đánh đá", "Sữa chua việt quất"
]

COLUMNS = [
    "STT", "Ngày", "Khách hàng", "Sản phẩm", "Số lượng",
    "Đơn giá", "Tiền hàng", "Chiết khấu (%)", "Tiền giảm",
    "VAT (%)", "Tiền VAT", "Tổng thanh toán"
]


# ==============================
# HÀM XỬ LÝ DỮ LIỆU
# ==============================

def new_workbook_df():
    return pd.DataFrame(columns=COLUMNS)


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


# ==============================
# KHỞI TẠO SESSION
# ==============================

if "orders" not in st.session_state:
    st.session_state.orders = new_workbook_df()


# ==============================
# GIAO DIỆN TAB
# ==============================

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Nhập đơn hàng",
    "📋 Danh sách đơn",
    "📊 Thống kê & Biểu đồ",
    "📤 Xuất Excel"
])


# ==============================
# TAB 1: NHẬP ĐƠN HÀNG
# ==============================

with tab1:

    st.subheader("Thông tin đơn hàng")

    with st.form("order_form", clear_on_submit=True):

        c1, c2 = st.columns(2)

        with c1:
            order_date = st.date_input(
                "Ngày bán",
                value=date.today()
            )

            customer = st.text_input(
                "Tên khách hàng",
                placeholder="Ví dụ: Bàn 1 / Anh Nam"
            )

            product = st.selectbox(
                "Chọn món nước",
                options=DRINK_MENU
            )

            quantity = st.number_input(
                "Số lượng",
                min_value=1,
                value=1,
                step=1
            )

        with c2:
            unit_price = st.number_input(
                "Đơn giá (VNĐ) *",
                min_value=0,
                value=None,
                step=1000,
                placeholder="Ví dụ: 25000"
            )

            discount = st.number_input(
                "Chiết khấu (%)",
                min_value=0,
                max_value=100,
                value=0,
                step=1
            )

            vat = st.number_input(
                "VAT (%)",
                min_value=0,
                max_value=100,
                value=8,
                step=1
            )

        submitted = st.form_submit_button(
            "Lưu đơn hàng",
            type="primary",
            use_container_width=True
        )

    if submitted:

        if product == "-- Chọn món nước --":
            st.error("⚠️ Vui lòng chọn món nước!")

        elif unit_price is None or unit_price <= 0:
            st.error("⚠️ Vui lòng nhập đơn giá lớn hơn 0!")

        else:

            subtotal = int(quantity) * int(unit_price)

            discount_amount = round(
                subtotal * int(discount) / 100
            )

            taxable = subtotal - discount_amount

            vat_amount = round(
                taxable * int(vat) / 100
            )

            total = taxable + vat_amount

            row = {
                "STT": len(st.session_state.orders) + 1,
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
                "Tổng thanh toán": total
            }

            st.session_state.orders = pd.concat(
                [
                    st.session_state.orders,
                    pd.DataFrame([row])
                ],
                ignore_index=True
            )

            st.success(
                f"✅ Đã lưu đơn hàng: {quantity} x {product}. "
                f"Tổng thanh toán: {total:,.0f} đ"
            )


# ==============================
# TAB 2: DANH SÁCH ĐƠN HÀNG
# ==============================

with tab2:

    st.subheader("📋 Danh sách đơn hàng")

    if not st.session_state.orders.empty:

        df = st.session_state.orders.copy()

        total_revenue = pd.to_numeric(
            df["Tổng thanh toán"], errors="coerce"
        ).fillna(0).sum()

        total_orders = len(df)

        total_quantity = pd.to_numeric(
            df["Số lượng"], errors="coerce"
        ).fillna(0).sum()

        c1, c2, c3 = st.columns(3)

        c1.metric("Tổng số đơn", f"{total_orders:,}")
        c2.metric("Tổng số lượng bán", f"{total_quantity:,}")
        c3.metric("Tổng doanh thu", f"{total_revenue:,.0f} đ")

        st.divider()

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        if st.button(
            "🗑️ Xóa toàn bộ dữ liệu trong phiên này",
            type="secondary"
        ):
            st.session_state.orders = new_workbook_df()
            st.rerun()

    else:
        st.info("Chưa có đơn hàng. Hãy nhập đơn ở tab Nhập đơn hàng.")


# ==============================
# TAB 3: THỐNG KÊ VÀ BIỂU ĐỒ
# ==============================

with tab3:

    st.subheader("📊 Thống kê tổng quan")

    if not st.session_state.orders.empty:

        # Chuẩn hóa dữ liệu số
        df = st.session_state.orders.copy()

        numeric_columns = [
            "Số lượng",
            "Đơn giá",
            "Tiền hàng",
            "Tiền giảm",
            "Tiền VAT",
            "Tổng thanh toán"
        ]

        for col in numeric_columns:
            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            ).fillna(0)

        # Tổng quan
        total_revenue = df["Tổng thanh toán"].sum()
        total_quantity = df["Số lượng"].sum()
        total_orders = len(df)
        total_products = df["Sản phẩm"].nunique()

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("💰 Tổng doanh thu", f"{total_revenue:,.0f} đ")
        c2.metric("🧾 Tổng đơn hàng", f"{total_orders:,}")
        c3.metric("🥤 Số lượng đã bán", f"{total_quantity:,}")
        c4.metric("📦 Số món đã bán", f"{total_products:,}")

        st.divider()

        # --------------------------------
        # BIỂU ĐỒ 1: TOP 10 MÓN BÁN CHẠY
        # --------------------------------

        st.subheader("🏆 Top 10 món nước bán chạy nhất")

        df_top10 = (
            df.groupby("Sản phẩm")["Số lượng"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        df_top10_chart = df_top10.to_frame(
            name="Tổng số lượng bán"
        )

        st.bar_chart(
            df_top10_chart,
            horizontal=False,
            use_container_width=True
        )

        st.caption(
            "So sánh số lượng bán ra của 10 món nước được gọi nhiều nhất."
        )

        st.divider()

        # --------------------------------
        # BIỂU ĐỒ 2: DOANH THU THEO SẢN PHẨM
        # --------------------------------

        st.subheader("💰 Doanh thu theo từng sản phẩm")

        df_revenue_product = (
            df.groupby("Sản phẩm")["Tổng thanh toán"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        df_revenue_chart = df_revenue_product.to_frame(
            name="Doanh thu (VNĐ)"
        )

        st.bar_chart(
            df_revenue_chart,
            horizontal=False,
            use_container_width=True
        )

        st.caption(
            "Top 10 sản phẩm mang lại doanh thu cao nhất."
        )

        st.divider()

        # --------------------------------
        # BIỂU ĐỒ 3: DOANH THU THEO NGÀY
        # --------------------------------

        st.subheader("📅 Doanh thu theo ngày")

        df["Ngày"] = pd.to_datetime(
            df["Ngày"],
            format="%d/%m/%Y",
            errors="coerce"
        )

        df_daily = (
            df.dropna(subset=["Ngày"])
            .groupby("Ngày")["Tổng thanh toán"]
            .sum()
            .sort_index()
        )

        if not df_daily.empty:

            df_daily_chart = df_daily.to_frame(
                name="Doanh thu (VNĐ)"
            )

            st.bar_chart(
                df_daily_chart,
                horizontal=False,
                use_container_width=True
            )

            st.caption(
                "Theo dõi doanh thu từng ngày để biết ngày nào bán tốt nhất."
            )

        else:
            st.info("Chưa có dữ liệu ngày hợp lệ để thống kê.")

        st.divider()

        # --------------------------------
        # BIỂU ĐỒ 4: XU HƯỚNG SỐ LƯỢNG BÁN
        # --------------------------------

        st.subheader("📈 Xu hướng số lượng bán ra (Lũy kế)")

        # Lấy Top 10 món bán chạy
        top_products = df_top10.index.tolist()

        df_filtered = df[
            df["Sản phẩm"].isin(top_products)
        ].copy()

        # Sắp xếp theo thứ tự đơn hàng
        df_filtered = df_filtered.sort_values("STT")

        # Tính số lượng theo từng đơn
        df_pivot = (
            df_filtered.pivot_table(
                index="STT",
                columns="Sản phẩm",
                values="Số lượng",
                aggfunc="sum"
            )
            .fillna(0)
            .cumsum()
        )

        if not df_pivot.empty:

            st.line_chart(
                df_pivot,
                use_container_width=True
            )

            st.caption(
                "Biểu đồ đường thể hiện số lượng bán lũy kế "
                "của Top 10 món theo thứ tự đơn hàng."
            )

    else:

        st.info(
            "Chưa có dữ liệu để thống kê. "
            "Vui lòng nhập đơn hàng ở tab đầu tiên."
        )


# ==============================
# TAB 4: XUẤT EXCEL
# ==============================

with tab4:

    st.subheader("📤 Tải dữ liệu về máy")

    st.write(
        "File Excel bao gồm toàn bộ đơn hàng hiện có trong phiên làm việc."
    )

    st.download_button(
        "⬇️ Tải CafePOS.xlsx",
        data=to_excel(st.session_state.orders),
        file_name="CafePOS.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )
