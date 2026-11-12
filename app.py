
import streamlit as st
import pandas as pd
import sqlite3
import uuid
from io import BytesIO
from datetime import date, datetime
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

# =====================================================
# 1. CẤU HÌNH ỨNG DỤNG
# =====================================================

st.set_page_config(
    page_title="CafePOS - Quản lý quán cà phê",
    page_icon="☕",
    layout="wide"
)

DB_NAME = "cafepos.db"

st.title("☕ CafePOS")
st.caption("Hệ thống quản lý đơn hàng quán cà phê")

# =====================================================
# 2. DANH SÁCH SẢN PHẨM
# =====================================================

DRINK_MENU = [
    "-- Chọn món nước --",
    "Cà phê đen đá", "Cà phê đen nóng",
    "Cà phê sữa đá", "Cà phê sữa nóng",
    "Bạc xỉu đá", "Bạc xỉu nóng",
    "Cà phê muối", "Cà phê cốt dừa",
    "Cà phê trứng", "Espresso",
    "Americano đá", "Americano nóng",
    "Latte đá", "Latte nóng",
    "Cappuccino", "Mocha",
    "Caramel Macchiato",
    "Cold Brew truyền thống", "Cold Brew cam sả",
    "Trà đào cam sả", "Trà vải hoa hồng",
    "Trà dâu tằm", "Trà ổi hồng",
    "Trà chanh giã tay", "Trà tắc mật ong",
    "Trà gừng mật ong", "Trà sen vàng",
    "Trà sữa truyền thống",
    "Trà sữa trân châu đường đen",
    "Trà sữa ô long", "Trà sữa thái xanh",
    "Trà sữa thái đỏ",
    "Matcha đá xay", "Matcha Latte",
    "Socola đá xay", "Socola nóng",
    "Cacao sữa đá", "Cacao nóng",
    "Nước cam ép", "Nước ép dưa hấu",
    "Nước ép thơm (dứa)", "Nước ép cà rốt",
    "Nước ép táo", "Nước ép ổi",
    "Sinh tố bơ", "Sinh tố xoài",
    "Sinh tố dâu", "Sinh tố việt quất",
    "Sữa chua đánh đá", "Sữa chua việt quất"
]

# =====================================================
# 3. HÀM ĐỊNH DẠNG TIỀN
# =====================================================

def format_money(value):
    try:
        return f"{float(value):,.0f}".replace(",", ".") + " đ"
    except (ValueError, TypeError):
        return "0 đ"


# =====================================================
# 4. DATABASE SQLITE
# =====================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn



def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = OFF")
    cursor = conn.cursor()

    # Kiểm tra bảng orders hiện tại
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='orders'
    """)
    table = cursor.fetchone()

    if table:
        cursor.execute("PRAGMA table_info(orders)")
        columns = [col[1] for col in cursor.fetchall()]

        # Nếu là database cũ thì chuyển đổi
        if "stt" in columns and "ma_don" not in columns:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ma_don TEXT UNIQUE,
                    ngay TEXT,
                    khach_hang TEXT,
                    chiet_khau INTEGER DEFAULT 0,
                    vat INTEGER DEFAULT 8,
                    tien_hang INTEGER DEFAULT 0,
                    tien_giam INTEGER DEFAULT 0,
                    tien_vat INTEGER DEFAULT 0,
                    tong_thanh_toan INTEGER DEFAULT 0
                )
            """)

            cursor.execute("SELECT * FROM orders")
            rows = cursor.fetchall()

            old_columns = [
                col[1] for col in
                conn.execute("PRAGMA table_info(orders)").fetchall()
            ]

            for row in rows:
                old = dict(zip(old_columns, row))

                ma_don = "OLD-" + str(old["id"])

                cursor.execute("""
                    INSERT OR IGNORE INTO orders_new (
                        ma_don, ngay, khach_hang,
                        chiet_khau, vat, tien_hang,
                        tien_giam, tien_vat, tong_thanh_toan
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ma_don,
                    old.get("ngay"),
                    old.get("khach_hang", "Khách lẻ"),
                    old.get("chiet_khau", 0),
                    old.get("vat", 8),
                    old.get("tien_hang", 0),
                    old.get("tien_giam", 0),
                    old.get("tien_vat", 0),
                    old.get("tong_thanh_toan", 0)
                ))

                cursor.execute("""
                    INSERT INTO order_items (
                        order_id, san_pham,
                        so_luong, don_gia, tien_hang
                    )
                    SELECT
                        n.id, ?, ?, ?, ?
                    FROM orders_new n
                    WHERE n.ma_don = ?
                """, (
                    old.get("san_pham", "Sản phẩm cũ"),
                    old.get("so_luong", 1),
                    old.get("don_gia", 0),
                    old.get("tien_hang", 0),
                    ma_don
                ))

            cursor.execute("DROP TABLE orders")
            cursor.execute("ALTER TABLE orders_new RENAME TO orders")

    # Đảm bảo bảng orders tồn tại
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_don TEXT UNIQUE,
            ngay TEXT,
            khach_hang TEXT,
            chiet_khau INTEGER DEFAULT 0,
            vat INTEGER DEFAULT 8,
            tien_hang INTEGER DEFAULT 0,
            tien_giam INTEGER DEFAULT 0,
            tien_vat INTEGER DEFAULT 0,
            tong_thanh_toan INTEGER DEFAULT 0
        )
    """)

    # Đảm bảo bảng chi tiết tồn tại
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            san_pham TEXT,
            so_luong INTEGER,
            don_gia INTEGER,
            tien_hang INTEGER,
            FOREIGN KEY(order_id)
            REFERENCES orders(id)
            ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()

init_db()


# =====================================================
# 5. CÁC HÀM XỬ LÝ DATABASE
# =====================================================

def load_orders():
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT
            id,
            ma_don AS 'Mã đơn',
            ngay AS 'Ngày',
            khach_hang AS 'Khách hàng',
            chiet_khau AS 'Chiết khấu (%)',
            vat AS 'VAT (%)',
            tien_hang AS 'Tiền hàng',
            tien_giam AS 'Tiền giảm',
            tien_vat AS 'Tiền VAT',
            tong_thanh_toan AS 'Tổng thanh toán'
        FROM orders
        ORDER BY id DESC
    """, conn)

    conn.close()
    return df


def load_items(order_id=None):
    conn = get_connection()

    sql = """
        SELECT
            o.ma_don AS 'Mã đơn',
            i.san_pham AS 'Sản phẩm',
            i.so_luong AS 'Số lượng',
            i.don_gia AS 'Đơn giá',
            i.tien_hang AS 'Tiền hàng'
        FROM order_items i
        JOIN orders o ON i.order_id = o.id
    """

    if order_id is not None:
        sql += " WHERE i.order_id = ?"
        df = pd.read_sql_query(sql, conn, params=(order_id,))
    else:
        sql += " ORDER BY i.id DESC"
        df = pd.read_sql_query(sql, conn)

    conn.close()
    return df


def save_order(customer, order_date, discount, vat, items):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        ma_don = (
            "DH"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + uuid.uuid4().hex[:4].upper()
        )

        subtotal = sum(
            item["tien_hang"] for item in items
        )

        discount_amount = round(
            subtotal * discount / 100
        )

        taxable = subtotal - discount_amount

        vat_amount = round(
            taxable * vat / 100
        )

        total = taxable + vat_amount

        cursor.execute("""
            INSERT INTO orders (
                ma_don, ngay, khach_hang,
                chiet_khau, vat, tien_hang,
                tien_giam, tien_vat, tong_thanh_toan
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ma_don,
            order_date.isoformat(),
            customer,
            discount,
            vat,
            subtotal,
            discount_amount,
            vat_amount,
            total
        ))

        order_id = cursor.lastrowid

        for item in items:
            cursor.execute("""
                INSERT INTO order_items (
                    order_id, san_pham,
                    so_luong, don_gia, tien_hang
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                order_id,
                item["san_pham"],
                item["so_luong"],
                item["don_gia"],
                item["tien_hang"]
            ))

        conn.commit()

        return ma_don, subtotal, discount_amount, vat_amount, total

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def delete_order(order_id):
    conn = get_connection()
    conn.execute("DELETE FROM orders WHERE id=?", (order_id,))
    conn.commit()
    conn.close()


def clear_database():
    conn = get_connection()
    conn.execute("DELETE FROM order_items")
    conn.execute("DELETE FROM orders")
    conn.commit()
    conn.close()


# =====================================================
# 6. HÀM HIỂN THỊ BẢNG TIỀN
# =====================================================

def format_dataframe(df, money_columns):
    result = df.copy()

    for col in money_columns:
        if col in result.columns:
            result[col] = result[col].apply(format_money)

    return result


# =====================================================
# 7. XUẤT EXCEL
# =====================================================

def to_excel(orders_df, items_df):
    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        orders_df.to_excel(
            writer,
            index=False,
            sheet_name="DanhSachDon"
        )

        items_df.to_excel(
            writer,
            index=False,
            sheet_name="ChiTietDon"
        )

        for sheet_name in writer.book.sheetnames:
            ws = writer.book[sheet_name]

            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions

            for cell in ws[1]:
                cell.font = Font(
                    bold=True,
                    color="FFFFFF"
                )
                cell.fill = PatternFill(
                    "solid",
                    fgColor="234E52"
                )
                cell.alignment = Alignment(
                    horizontal="center",
                    vertical="center"
                )

            for column in ws.columns:
                max_length = max(
                    len(str(cell.value or ""))
                    for cell in column
                )
                letter = get_column_letter(column[0].column)
                ws.column_dimensions[letter].width = min(
                    max(max_length + 4, 14),
                    35
                )

            for row in ws.iter_rows(min_row=2):
                for cell in row:
                    cell.alignment = Alignment(
                        vertical="center"
                    )

                    if isinstance(cell.value, (int, float)):
                        if cell.column in (
                            [7, 8, 9, 10] if sheet_name == "DanhSachDon"
                            else [4, 5]
                        ):
                            cell.number_format = '#,##0" đ"'

    output.seek(0)
    return output.getvalue()


# =====================================================
# 8. SESSION STATE
# =====================================================

if "form_version" not in st.session_state:
    st.session_state.form_version = 0


# =====================================================
# 9. GIAO DIỆN 4 TRANG
# =====================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Nhập đơn hàng",
    "📋 Danh sách đơn",
    "📊 Thống kê",
    "📤 Xuất Excel"
])


# =====================================================
# TRANG 1: NHẬP ĐƠN HÀNG
# =====================================================

with tab1:

    st.subheader("➕ Tạo đơn hàng mới")

    with st.form(
        f"order_form_{st.session_state.form_version}"
    ):

        col1, col2 = st.columns(2)

        with col1:
            order_date = st.date_input(
                "Ngày bán",
                value=date.today()
            )

            customer = st.text_input(
                "Tên khách hàng",
                placeholder="Ví dụ: Anh Nam / Bàn số 1"
            )

        with col2:
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

        st.divider()

        st.markdown("### 🥤 Danh sách món trong đơn")

        st.caption(
            "Bạn có thể thêm nhiều dòng sản phẩm. "
            "Mỗi dòng tương ứng với một loại nước."
        )

        initial_items = pd.DataFrame([{
            "Sản phẩm": "-- Chọn món nước --",
            "Số lượng": 1,
            "Đơn giá": 0
        }])

        items_df = st.data_editor(
            initial_items,
            key=f"items_editor_{st.session_state.form_version}",
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Sản phẩm": st.column_config.SelectboxColumn(
                    "Tên món nước",
                    options=DRINK_MENU,
                    required=True,
                    width="large"
                ),
                "Số lượng": st.column_config.NumberColumn(
                    "Số lượng",
                    min_value=1,
                    step=1,
                    format="%d"
                ),
                "Đơn giá": st.column_config.NumberColumn(
                    "Đơn giá (VNĐ)",
                    min_value=0,
                    step=1000,
                    format="%d"
                )
            }
        )

        st.divider()

        submitted = st.form_submit_button(
            "💾 LƯU ĐƠN HÀNG",
            type="primary",
            use_container_width=True
        )

    if submitted:

        valid_items = []
        errors = []

        for index, item in items_df.iterrows():

            product = item["Sản phẩm"]
            quantity = item["Số lượng"]
            price = item["Đơn giá"]

            # Bỏ qua dòng chưa sử dụng
            if product == "-- Chọn món nước --":
                continue

            if pd.isna(product) or not product:
                continue

            if pd.isna(quantity) or quantity < 1:
                errors.append(
                    f"Dòng {index + 1}: Số lượng không hợp lệ."
                )
                continue

            if pd.isna(price) or price <= 0:
                errors.append(
                    f"Dòng {index + 1}: Vui lòng nhập đơn giá."
                )
                continue

            quantity = int(quantity)
            price = int(price)

            valid_items.append({
                "san_pham": product,
                "so_luong": quantity,
                "don_gia": price,
                "tien_hang": quantity * price
            })

        if errors:
            for error in errors:
                st.error(error)

        elif len(valid_items) == 0:
            st.error("Vui lòng chọn ít nhất một món nước!")

        else:
            try:
                result = save_order(
                    customer.strip() or "Khách lẻ",
                    order_date,
                    int(discount),
                    int(vat),
                    valid_items
                )

                ma_don, subtotal, discount_amount, vat_amount, total = result

                st.success(
                    f"Đã lưu đơn hàng {ma_don} thành công!"
                )

                a, b, c = st.columns(3)

                a.metric(
                    "Tiền hàng",
                    format_money(subtotal)
                )

                b.metric(
                    "Tiền giảm",
                    format_money(discount_amount)
                )

                c.metric(
                    "Tổng thanh toán",
                    format_money(total)
                )

                st.info(
                    f"Đơn hàng có {len(valid_items)} loại nước, "
                    f"tổng số lượng: {sum(i['so_luong'] for i in valid_items)}."
                )

                st.session_state.form_version += 1
                st.rerun()

            except Exception as e:
                st.error(f"Lỗi khi lưu đơn hàng: {e}")


# =====================================================
# TRANG 2: DANH SÁCH ĐƠN HÀNG
# =====================================================

with tab2:

    st.subheader("📋 Danh sách đơn hàng")

    df_orders = load_orders()

    if not df_orders.empty:

        # Bộ lọc
        col1, col2 = st.columns(2)

        with col1:
            search_customer = st.text_input(
                "🔍 Tìm khách hàng hoặc mã đơn",
                placeholder="Nhập tên khách hàng / mã đơn..."
            )

        with col2:
            search_product = st.selectbox(
                "Lọc theo sản phẩm",
                ["Tất cả sản phẩm"] + DRINK_MENU[1:]
            )

        filtered = df_orders.copy()

        if search_customer:
            filtered = filtered[
                filtered["Khách hàng"].str.contains(
                    search_customer,
                    case=False,
                    na=False
                )
                |
                filtered["Mã đơn"].str.contains(
                    search_customer,
                    case=False,
                    na=False
                )
            ]

        if search_product != "Tất cả sản phẩm":

            product_orders = load_items()

            matched_ids = product_orders[
                product_orders["Sản phẩm"] == search_product
            ]["Mã đơn"].tolist()

            filtered = filtered[
                filtered["Mã đơn"].isin(matched_ids)
            ]

        # Thống kê nhanh
        total_revenue = filtered["Tổng thanh toán"].sum()

        m1, m2 = st.columns(2)

        m1.metric(
            "Tổng số đơn",
            f"{len(filtered):,}".replace(",", ".")
        )

        m2.metric(
            "Tổng doanh thu",
            format_money(total_revenue)
        )

        st.divider()

        # Hiển thị bảng
        display_df = filtered.drop(columns=["id"]).copy()

        for col in [
            "Tiền hàng",
            "Tiền giảm",
            "Tiền VAT",
            "Tổng thanh toán"
        ]:
            display_df[col] = display_df[col].apply(format_money)

        display_df["Ngày"] = pd.to_datetime(
            display_df["Ngày"]
        ).dt.strftime("%d/%m/%Y")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("🔎 Xem chi tiết đơn hàng")

        order_options = filtered["Mã đơn"].tolist()

        if order_options:

            selected_order = st.selectbox(
                "Chọn mã đơn hàng",
                order_options
            )

            selected_id = filtered.loc[
                filtered["Mã đơn"] == selected_order,
                "id"
            ].iloc[0]

            details = load_items(selected_id)

            st.markdown(f"**Mã đơn: {selected_order}**")

            details_display = details.drop(
                columns=["Mã đơn"]
            ).copy()

            details_display["Đơn giá"] = (
                details_display["Đơn giá"].apply(format_money)
            )

            details_display["Tiền hàng"] = (
                details_display["Tiền hàng"].apply(format_money)
            )

            st.dataframe(
                details_display,
                use_container_width=True,
                hide_index=True
            )

            selected_info = filtered[
                filtered["Mã đơn"] == selected_order
            ].iloc[0]

            x1, x2, x3 = st.columns(3)

            x1.metric(
                "Tiền hàng",
                format_money(selected_info["Tiền hàng"])
            )

            x2.metric(
                "Tiền VAT",
                format_money(selected_info["Tiền VAT"])
            )

            x3.metric(
                "Tổng thanh toán",
                format_money(selected_info["Tổng thanh toán"])
            )

            with st.popover("🗑️ Xóa đơn hàng này"):
                st.warning(
                    f"Bạn có chắc muốn xóa đơn {selected_order}?"
                )

                if st.button(
                    "Xác nhận xóa đơn",
                    type="primary",
                    key="delete_one"
                ):
                    delete_order(int(selected_id))
                    st.success("Đã xóa đơn hàng!")
                    st.rerun()

        st.divider()

        with st.expander("⚠️ Quản lý dữ liệu"):

            st.warning(
                "Xóa toàn bộ dữ liệu sẽ không thể khôi phục."
            )

            confirm_delete = st.checkbox(
                "Tôi xác nhận muốn xóa toàn bộ đơn hàng"
            )

            if st.button(
                "🗑️ XÓA TOÀN BỘ DATABASE",
                disabled=not confirm_delete
            ):
                clear_database()
                st.success("Đã xóa toàn bộ dữ liệu!")
                st.rerun()

    else:
        st.info("Chưa có đơn hàng nào. Hãy tạo đơn hàng mới!")


# =====================================================
# TRANG 3: THỐNG KÊ VÀ BIỂU ĐỒ
# =====================================================

with tab3:

    st.subheader("📊 Thống kê kinh doanh")

    df_orders = load_orders()
    df_items = load_items()

    if not df_orders.empty:

        total_orders = len(df_orders)

        total_revenue = df_orders[
            "Tổng thanh toán"
        ].sum()

        total_products = df_items[
            "Số lượng"
        ].sum()

        total_customers = df_orders[
            "Khách hàng"
        ].nunique()

        # 4 thẻ tổng quan
        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Tổng đơn hàng",
            f"{total_orders:,}".replace(",", ".")
        )

        c2.metric(
            "Tổng doanh thu",
            format_money(total_revenue)
        )

        c3.metric(
            "Tổng sản phẩm bán",
            f"{total_products:,}".replace(",", ".")
        )

        c4.metric(
            "Số khách hàng",
            f"{total_customers:,}".replace(",", ".")
        )

        st.divider()

        # Top 10 món nước
        st.subheader("🏆 Top 10 món nước bán chạy")

        top10 = (
            df_items.groupby("Sản phẩm")["Số lượng"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        if not top10.empty:
            st.bar_chart(
                top10,
                horizontal=True
            )

        st.divider()

        # Doanh thu theo ngày
        st.subheader("📈 Biểu đồ doanh thu theo ngày")

        revenue_by_day = df_orders.copy()

        revenue_by_day["Ngày"] = pd.to_datetime(
            revenue_by_day["Ngày"]
        )

        revenue_by_day = (
            revenue_by_day.groupby("Ngày")[
                "Tổng thanh toán"
            ]
            .sum()
            .sort_index()
        )

        st.line_chart(revenue_by_day)

        st.divider()

        # Số lượng từng sản phẩm theo ngày
        st.subheader("🥤 Số lượng sản phẩm bán theo ngày")

        product_by_day = df_items.merge(
            df_orders[["Mã đơn", "Ngày"]],
            on="Mã đơn",
            how="left"
        )

        product_by_day["Ngày"] = pd.to_datetime(
            product_by_day["Ngày"]
        )

        product_pivot = product_by_day.pivot_table(
            index="Ngày",
            columns="Sản phẩm",
            values="Số lượng",
            aggfunc="sum"
        ).fillna(0)

        st.line_chart(product_pivot)

    else:
        st.info(
            "Chưa có dữ liệu để thống kê. "
            "Hãy nhập đơn hàng trước!"
        )


# =====================================================
# TRANG 4: XUẤT EXCEL
# =====================================================

with tab4:

    st.subheader("📤 Xuất dữ liệu Excel")

    st.write(
        "Tải toàn bộ dữ liệu đơn hàng và chi tiết sản phẩm "
        "về máy tính."
    )

    df_orders = load_orders()
    df_items = load_items()

    if not df_orders.empty:

        st.success(
            f"Hiện có {len(df_orders)} đơn hàng trong hệ thống."
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Số đơn hàng",
            f"{len(df_orders):,}".replace(",", ".")
        )

        col2.metric(
            "Tổng doanh thu",
            format_money(
                df_orders["Tổng thanh toán"].sum()
            )
        )

        # Chuẩn bị dữ liệu xuất
        export_orders = df_orders.drop(
            columns=["id"]
        ).copy()

        export_orders["Ngày"] = pd.to_datetime(
            export_orders["Ngày"]
        ).dt.strftime("%d/%m/%Y")

        export_items = df_items.copy()

        excel_file = to_excel(
            export_orders,
            export_items
        )

        st.divider()

        st.download_button(
            label="⬇️ TẢI FILE CAFEPOS.XLSX",
            data=excel_file,
            file_name=f"CafePOS_{date.today().strftime('%d%m%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )

        st.caption(
            "File Excel bao gồm 2 sheet: DanhSachDon và ChiTietDon."
        )

        with st.expander("Xem trước dữ liệu xuất"):

            st.markdown("**Danh sách đơn hàng**")
            st.dataframe(
                format_dataframe(
                    export_orders,
                    [
                        "Tiền hàng",
                        "Tiền giảm",
                        "Tiền VAT",
                        "Tổng thanh toán"
                    ]
                ),
                use_container_width=True,
                hide_index=True
            )

            st.markdown("**Chi tiết sản phẩm**")
            st.dataframe(
                format_dataframe(
                    export_items,
                    ["Đơn giá", "Tiền hàng"]
                ),
                use_container_width=True,
                hide_index=True
            )

    else:
        st.info(
            "Chưa có dữ liệu. Hãy nhập đơn hàng trước khi xuất Excel."
        )


# =====================================================
# 10. FOOTER
# =====================================================

st.divider()

st.caption(
    "☕ CafePOS | Quản lý đơn hàng | SQLite Database | Excel Export"
)
