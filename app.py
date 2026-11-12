
import streamlit as st
import pandas as pd
import sqlite3
import uuid

from io import BytesIO
from datetime import date, datetime
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


# =========================================================
# 1. CẤU HÌNH
# =========================================================

st.set_page_config(
    page_title="CafePOS",
    page_icon="☕",
    layout="wide"
)

DB_NAME = "cafepos.db"

st.title("☕ CafePOS - Quản lý quán cà phê")
st.caption("Quản lý đơn hàng | Nhiều sản phẩm | Thống kê | Xuất Excel")


# =========================================================
# 2. DANH SÁCH SẢN PHẨM
# =========================================================

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


# =========================================================
# 3. HÀM TIỆN ÍCH
# =========================================================

def format_money(value):
    try:
        return f"{float(value):,.0f}".replace(",", ".") + " đ"
    except (ValueError, TypeError):
        return "0 đ"


def format_number(value):
    return f"{int(value):,}".replace(",", ".")


def normalize_date(value):
    """Chuyển ngày cũ và ngày mới về YYYY-MM-DD."""
    if not value:
        return date.today().isoformat()

    try:
        return pd.to_datetime(
            value,
            dayfirst=True
        ).strftime("%Y-%m-%d")
    except Exception:
        return date.today().isoformat()


def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=30)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =========================================================
# 4. KHỞI TẠO VÀ TỰ ĐỘNG SỬA DATABASE
# =========================================================

def init_db():

    conn = sqlite3.connect(DB_NAME, timeout=30)

    # Tạm tắt khóa ngoại để chuyển đổi cấu trúc bảng an toàn
    conn.execute("PRAGMA foreign_keys = OFF")

    try:
        conn.execute("BEGIN IMMEDIATE")
        cursor = conn.cursor()

        # Kiểm tra các bảng đang tồn tại
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
        """)

        existing_tables = {
            row[0] for row in cursor.fetchall()
        }

        candidate_tables = [
            "orders",
            "orders_new",
            "orders_legacy"
        ]

        # -------------------------------------------------
        # 4.1 Đọc và sao lưu dữ liệu các bảng cũ trong RAM
        # -------------------------------------------------

        saved_orders = {}
        table_id_to_code = {}

        for table_name in candidate_tables:

            if table_name not in existing_tables:
                continue

            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [
                row[1] for row in cursor.fetchall()
            ]

            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            for row in rows:

                data = dict(zip(columns, row))

                old_id = data.get("id")

                if data.get("ma_don"):
                    ma_don = str(data["ma_don"])

                elif old_id is not None:
                    ma_don = f"OLD-{old_id}"

                else:
                    ma_don = "OLD-" + uuid.uuid4().hex[:10]

                table_id_to_code[
                    (table_name, old_id)
                ] = ma_don

                # Chuyển cả hai cấu trúc dữ liệu về một cấu trúc
                saved_orders.setdefault(ma_don, {
                    "ma_don": ma_don,
                    "ngay": normalize_date(
                        data.get("ngay")
                    ),
                    "khach_hang": (
                        data.get("khach_hang") or "Khách lẻ"
                    ),
                    "chiet_khau": int(
                        data.get("chiet_khau") or 0
                    ),
                    "vat": int(
                        data.get("vat") or 0
                    ),
                    "tien_hang": int(
                        data.get("tien_hang") or 0
                    ),
                    "tien_giam": int(
                        data.get("tien_giam") or 0
                    ),
                    "tien_vat": int(
                        data.get("tien_vat") or 0
                    ),
                    "tong_thanh_toan": int(
                        data.get("tong_thanh_toan") or 0
                    ),
                    "legacy_product": data.get("san_pham"),
                    "legacy_quantity": data.get("so_luong"),
                    "legacy_price": data.get("don_gia")
                })

        # -------------------------------------------------
        # 4.2 Đọc chi tiết sản phẩm đã tồn tại
        # -------------------------------------------------

        saved_items = []

        if "order_items" in existing_tables:

            cursor.execute("PRAGMA table_info(order_items)")
            item_columns = [
                row[1] for row in cursor.fetchall()
            ]

            cursor.execute("PRAGMA foreign_key_list(order_items)")
            foreign_keys = cursor.fetchall()

            parent_table = (
                foreign_keys[0][2]
                if foreign_keys
                else "orders"
            )

            cursor.execute("SELECT * FROM order_items")

            for row in cursor.fetchall():

                item = dict(zip(item_columns, row))

                order_code = table_id_to_code.get(
                    (parent_table, item.get("order_id"))
                )

                if not order_code:
                    # Thử tìm trong các bảng khác nếu
                    # database cũ đã tham chiếu sai bảng
                    for table_name in candidate_tables:
                        order_code = table_id_to_code.get(
                            (table_name, item.get("order_id"))
                        )
                        if order_code:
                            break

                if order_code and order_code in saved_orders:

                    saved_items.append({
                        "ma_don": order_code,
                        "san_pham": item.get("san_pham"),
                        "so_luong": int(
                            item.get("so_luong") or 1
                        ),
                        "don_gia": int(
                            item.get("don_gia") or 0
                        ),
                        "tien_hang": int(
                            item.get("tien_hang") or 0
                        )
                    })

        # -------------------------------------------------
        # 4.3 Xóa các bảng cũ theo thứ tự an toàn
        # -------------------------------------------------

        if "order_items" in existing_tables:
            cursor.execute("DROP TABLE order_items")

        for table_name in candidate_tables:
            if table_name in existing_tables:
                cursor.execute(
                    f"DROP TABLE {table_name}"
                )

        # -------------------------------------------------
        # 4.4 Tạo lại hai bảng chuẩn
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ma_don TEXT UNIQUE NOT NULL,
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

        cursor.execute("""
            CREATE TABLE order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                san_pham TEXT NOT NULL,
                so_luong INTEGER NOT NULL,
                don_gia INTEGER NOT NULL,
                tien_hang INTEGER NOT NULL,
                FOREIGN KEY(order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE
            )
        """)

        # -------------------------------------------------
        # 4.5 Khôi phục đơn hàng
        # -------------------------------------------------

        new_order_ids = {}

        for ma_don, data in saved_orders.items():

            cursor.execute("""
                INSERT INTO orders (
                    ma_don,
                    ngay,
                    khach_hang,
                    chiet_khau,
                    vat,
                    tien_hang,
                    tien_giam,
                    tien_vat,
                    tong_thanh_toan
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["ma_don"],
                data["ngay"],
                data["khach_hang"],
                data["chiet_khau"],
                data["vat"],
                data["tien_hang"],
                data["tien_giam"],
                data["tien_vat"],
                data["tong_thanh_toan"]
            ))

            new_order_ids[ma_don] = cursor.lastrowid

        # -------------------------------------------------
        # 4.6 Khôi phục chi tiết sản phẩm
        # -------------------------------------------------

        restored_codes = set()

        for item in saved_items:

            order_id = new_order_ids.get(item["ma_don"])

            if not order_id:
                continue

            if not item["san_pham"]:
                continue

            cursor.execute("""
                INSERT INTO order_items (
                    order_id,
                    san_pham,
                    so_luong,
                    don_gia,
                    tien_hang
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                order_id,
                item["san_pham"],
                item["so_luong"],
                item["don_gia"],
                item["tien_hang"]
            ))

            restored_codes.add(item["ma_don"])

        # Đơn hàng cũ chưa có bảng chi tiết thì tạo lại
        for ma_don, data in saved_orders.items():

            if ma_don in restored_codes:
                continue

            product = data.get("legacy_product")

            if not product:
                continue

            order_id = new_order_ids[ma_don]

            quantity = int(
                data.get("legacy_quantity") or 1
            )

            price = int(
                data.get("legacy_price") or 0
            )

            cursor.execute("""
                INSERT INTO order_items (
                    order_id,
                    san_pham,
                    so_luong,
                    don_gia,
                    tien_hang
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                order_id,
                product,
                quantity,
                price,
                int(data.get("tien_hang") or quantity * price)
            ))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# Chạy kiểm tra database trước khi mở giao diện
try:
    init_db()
except Exception as e:
    st.error(f"Không thể khởi tạo Database: {e}")
    st.stop()


# =========================================================
# 5. LẤY DỮ LIỆU
# =========================================================

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

        df = pd.read_sql_query(
            sql,
            conn,
            params=(order_id,)
        )

    else:

        sql += " ORDER BY i.id DESC"

        df = pd.read_sql_query(sql, conn)

    conn.close()

    return df


# =========================================================
# 6. LƯU ĐƠN HÀNG
# =========================================================

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
            item["tien_hang"]
            for item in items
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
                ma_don,
                ngay,
                khach_hang,
                chiet_khau,
                vat,
                tien_hang,
                tien_giam,
                tien_vat,
                tong_thanh_toan
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
                    order_id,
                    san_pham,
                    so_luong,
                    don_gia,
                    tien_hang
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


# =========================================================
# 7. XÓA DỮ LIỆU
# =========================================================

def delete_order(order_id):

    conn = get_connection()

    conn.execute(
        "DELETE FROM orders WHERE id=?",
        (order_id,)
    )

    conn.commit()
    conn.close()


def clear_database():

    conn = get_connection()

    conn.execute("DELETE FROM order_items")
    conn.execute("DELETE FROM orders")

    conn.commit()
    conn.close()


# =========================================================
# 8. ĐỊNH DẠNG BẢNG
# =========================================================

def format_dataframe(df, money_columns):

    result = df.copy()

    for col in money_columns:

        if col in result.columns:

            result[col] = result[col].apply(
                format_money
            )

    return result


# =========================================================
# 9. XUẤT EXCEL
# =========================================================

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

                letter = get_column_letter(
                    column[0].column
                )

                ws.column_dimensions[letter].width = min(
                    max(max_length + 4, 14),
                    35
                )

            money_columns = (
                [6, 7, 8, 9]
                if sheet_name == "DanhSachDon"
                else [4, 5]
            )

            for row in ws.iter_rows(min_row=2):

                for cell in row:

                    cell.alignment = Alignment(
                        vertical="center"
                    )

                    if cell.column in money_columns:
                        cell.number_format = '#,##0" đ"'

    output.seek(0)

    return output.getvalue()


# =========================================================
# 10. GIAO DIỆN
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Nhập đơn hàng",
    "📋 Danh sách đơn",
    "📊 Thống kê",
    "📤 Xuất Excel"
])


# =========================================================
# TRANG 1: NHẬP ĐƠN HÀNG
# =========================================================

with tab1:

    st.subheader("➕ Tạo đơn hàng mới")

    if "form_version" not in st.session_state:
        st.session_state.form_version = 0

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

        st.markdown("### 🥤 Danh sách món nước")

        st.caption(
            "Nhấn dấu + ở cuối bảng để thêm sản phẩm. "
            "Một đơn có thể chứa nhiều loại nước."
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
                    required=True
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

            if pd.isna(product) or product == "-- Chọn món nước --":
                continue

            if pd.isna(quantity) or quantity < 1:
                errors.append(
                    f"Dòng {index + 1}: Số lượng không hợp lệ."
                )
                continue

            if pd.isna(price) or price <= 0:
                errors.append(
                    f"Dòng {index + 1}: Đơn giá phải lớn hơn 0."
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

        elif not valid_items:

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
                    f"Có {len(valid_items)} loại nước, "
                    f"tổng số lượng {sum(i['so_luong'] for i in valid_items)}."
                )

                st.session_state.form_version += 1
                st.rerun()

            except Exception as e:

                st.error(f"Lỗi khi lưu đơn hàng: {e}")


# =========================================================
# TRANG 2: DANH SÁCH ĐƠN HÀNG
# =========================================================

with tab2:

    st.subheader("📋 Danh sách đơn hàng")

    df_orders = load_orders()

    if not df_orders.empty:

        col1, col2 = st.columns(2)

        with col1:

            search_customer = st.text_input(
                "🔍 Tìm khách hàng hoặc mã đơn",
                placeholder="Nhập tên hoặc mã đơn..."
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

            all_items = load_items()

            matched_orders = all_items[
                all_items["Sản phẩm"] == search_product
            ]["Mã đơn"].tolist()

            filtered = filtered[
                filtered["Mã đơn"].isin(matched_orders)
            ]

        m1, m2 = st.columns(2)

        m1.metric(
            "Tổng số đơn",
            format_number(len(filtered))
        )

        m2.metric(
            "Tổng doanh thu",
            format_money(
                filtered["Tổng thanh toán"].sum()
            )
        )

        st.divider()

        st.markdown("### Danh sách đơn")

        display_df = filtered.drop(
            columns=["id"]
        ).copy()

        display_df["Ngày"] = display_df["Ngày"].apply(
            lambda x: pd.to_datetime(x).strftime("%d/%m/%Y")
        )

        display_df = format_dataframe(
            display_df,
            [
                "Tiền hàng",
                "Tiền giảm",
                "Tiền VAT",
                "Tổng thanh toán"
            ]
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.markdown("### 🔎 Chi tiết đơn hàng")

        selected_order = st.selectbox(
            "Chọn mã đơn hàng",
            filtered["Mã đơn"].tolist()
        )

        selected_info = filtered[
            filtered["Mã đơn"] == selected_order
        ].iloc[0]

        selected_id = int(selected_info["id"])

        details = load_items(selected_id)

        st.write(f"**Mã đơn:** {selected_order}")
        st.write(f"**Khách hàng:** {selected_info['Khách hàng']}")

        details_display = details.drop(
            columns=["Mã đơn"]
        ).copy()

        details_display = format_dataframe(
            details_display,
            ["Đơn giá", "Tiền hàng"]
        )

        st.dataframe(
            details_display,
            use_container_width=True,
            hide_index=True
        )

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
                f"Bạn có chắc muốn xóa {selected_order}?"
            )

            if st.button(
                "Xác nhận xóa",
                type="primary",
                key="delete_one"
            ):

                delete_order(selected_id)

                st.success("Đã xóa đơn hàng!")
                st.rerun()

        st.divider()

        with st.expander("⚠️ Quản lý dữ liệu"):

            st.warning(
                "Xóa toàn bộ đơn hàng sẽ không thể khôi phục."
            )

            confirm_delete = st.checkbox(
                "Tôi xác nhận muốn xóa toàn bộ dữ liệu"
            )

            if st.button(
                "🗑️ XÓA TOÀN BỘ DATABASE",
                disabled=not confirm_delete
            ):

                clear_database()

                st.success("Đã xóa toàn bộ dữ liệu!")
                st.rerun()

    else:

        st.info(
            "Chưa có đơn hàng nào. "
            "Hãy chuyển sang trang Nhập đơn hàng."
        )


# =========================================================
# TRANG 3: THỐNG KÊ
# =========================================================

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

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Tổng đơn hàng",
            format_number(total_orders)
        )

        c2.metric(
            "Tổng doanh thu",
            format_money(total_revenue)
        )

        c3.metric(
            "Sản phẩm đã bán",
            format_number(total_products)
        )

        c4.metric(
            "Số khách hàng",
            format_number(total_customers)
        )

        st.divider()

        st.markdown("### 🏆 Top 10 món nước bán chạy")

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

        st.markdown("### 📈 Doanh thu theo ngày")

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

        st.markdown("### 🥤 Số lượng sản phẩm bán theo ngày")

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
            "Chưa có dữ liệu thống kê. "
            "Hãy tạo đơn hàng trước!"
        )


# =========================================================
# TRANG 4: XUẤT EXCEL
# =========================================================

with tab4:

    st.subheader("📤 Xuất dữ liệu Excel")

    df_orders = load_orders()
    df_items = load_items()

    if not df_orders.empty:

        st.success(
            f"Hệ thống hiện có {format_number(len(df_orders))} đơn hàng."
        )

        c1, c2 = st.columns(2)

        c1.metric(
            "Tổng số đơn",
            format_number(len(df_orders))
        )

        c2.metric(
            "Tổng doanh thu",
            format_money(
                df_orders["Tổng thanh toán"].sum()
            )
        )

        export_orders = df_orders.drop(
            columns=["id"]
        ).copy()

        export_orders["Ngày"] = pd.to_datetime(
            export_orders["Ngày"]
        ).dt.strftime("%d/%m/%Y")

        export_file = to_excel(
            export_orders,
            df_items
        )

        st.divider()

        st.download_button(
            label="⬇️ TẢI FILE CAFEPOS.XLSX",
            data=export_file,
            file_name=(
                f"CafePOS_{date.today().strftime('%d%m%Y')}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            type="primary",
            use_container_width=True
        )

        st.caption(
            "File gồm 2 sheet: DanhSachDon và ChiTietDon."
        )

        with st.expander("Xem trước dữ liệu Excel"):

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
                    df_items,
                    ["Đơn giá", "Tiền hàng"]
                ),
                use_container_width=True,
                hide_index=True
            )

    else:

        st.info(
            "Chưa có đơn hàng để xuất Excel."
        )


# =========================================================
# 11. FOOTER
# =========================================================

st.divider()

st.caption(
    "☕ CafePOS | Quản lý đơn hàng | SQLite | Excel Export"
)
