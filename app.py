
import streamlit as st
import sqlite3
import pandas as pd
import requests
import html

from datetime import datetime, date
from io import BytesIO

# ==================================================
# 1. CẤU HÌNH
# ==================================================

st.set_page_config(
    page_title="CafePOS - Quản lý quán nước",
    page_icon="☕",
    layout="wide"
)

DB_NAME = "cafe_pos.db"


# ==================================================
# 2. MENU VÀ GIÁ SẢN PHẨM
# ==================================================

MENU = {
    "Cà phê đen": 20000,
    "Cà phê sữa": 25000,
    "Bạc xỉu": 28000,
    "Cà phê muối": 30000,
    "Cà phê cốt dừa": 35000,
    "Espresso": 30000,
    "Americano": 30000,
    "Cappuccino": 40000,
    "Latte": 40000,
    "Matcha latte": 40000,
    "Trà đào cam sả": 35000,
    "Trà tắc": 20000,
    "Trà vải": 35000,
    "Trà dâu": 35000,
    "Trà chanh": 25000,
    "Trà sữa truyền thống": 30000,
    "Trà sữa matcha": 40000,
    "Ca cao đá": 30000,
    "Sữa tươi trân châu đường đen": 40000,
    "Nước ép cam": 40000,
    "Nước ép dưa hấu": 35000,
    "Nước ép ổi": 35000,
    "Sinh tố bơ": 45000,
    "Sinh tố xoài": 40000,
    "Soda việt quất": 35000,
    "Soda chanh": 30000,
    "Nước suối": 20000
}


# ==================================================
# 3. HÌNH ẢNH SẢN PHẨM ONLINE
# ==================================================
# Ảnh được lấy từ Unsplash.
# Tất cả URL đều yêu cầu ảnh 600x400.
# fit=crop giúp chuẩn hóa tỷ lệ ảnh.

IMAGE_URLS = {
    "coffee": (
        "https://images.unsplash.com/photo-1509042239860-f550ce710b93"
        "?auto=format&fit=crop&w=600&h=400&crop=center&q=85"
    ),

    "milk_coffee": (
        "https://images.unsplash.com/photo-1461023058943-07fcbe16d735"
        "?auto=format&fit=crop&w=600&h=400&crop=center&q=85"
    ),

    "espresso": (
        "https://images.unsplash.com/photo-1510591509098-f4fdc6d0ff04"
        "?auto=format&fit=crop&w=600&h=400&crop=center&q=85"
    ),

    "tea": (
        "https://images.unsplash.com/photo-1556679343-c7306c1976bc"
        "?auto=format&fit=crop&w=600&h=400&crop=center&q=85"
    ),

    "matcha": (
        "https://images.unsplash.com/photo-1515823064-d6e0c04616a7"
        "?auto=format&fit=crop&w=600&h=400&crop=center&q=85"
    ),

    "juice": (
        "https://images.unsplash.com/photo-1600271886742-f049cd451bba"
        "?auto=format&fit=crop&w=600&h=400&crop=center&q=85"
    ),

    "smoothie": (
        "https://images.unsplash.com/photo-1505252585461-04db1eb84625"
        "?auto=format&fit=crop&w=600&h=400&crop=center&q=85"
    ),

    "soda": (
        "https://images.unsplash.com/photo-1513558161293-cdaf765edfd4"
        "?auto=format&fit=crop&w=600&h=400&crop=center&q=85"
    ),

    "water": (
        "https://images.unsplash.com/photo-1523362628745-0c100150b504"
        "?auto=format&fit=crop&w=600&h=400&crop=center&q=85"
    )
}


def get_product_image(name):

    if name in ["Cà phê đen", "Cà phê cốt dừa"]:
        return IMAGE_URLS["coffee"]

    elif name in ["Cà phê sữa", "Bạc xỉu", "Cà phê muối"]:
        return IMAGE_URLS["milk_coffee"]

    elif name in ["Espresso", "Americano"]:
        return IMAGE_URLS["espresso"]

    elif name in ["Cappuccino", "Latte"]:
        return IMAGE_URLS["milk_coffee"]

    elif "Matcha" in name:
        return IMAGE_URLS["matcha"]

    elif name in ["Ca cao đá"]:
        return IMAGE_URLS["milk_coffee"]

    elif "Trà sữa" in name or "Sữa tươi" in name:
        return IMAGE_URLS["matcha"]

    elif "Nước ép" in name:
        return IMAGE_URLS["juice"]

    elif "Sinh tố" in name:
        return IMAGE_URLS["smoothie"]

    elif "Soda" in name:
        return IMAGE_URLS["soda"]

    elif "Trà" in name:
        return IMAGE_URLS["tea"]

    elif name == "Nước suối":
        return IMAGE_URLS["water"]

    return IMAGE_URLS["tea"]


# ==================================================
# 4. TẢI VÀ LƯU CACHE HÌNH ẢNH
# ==================================================

@st.cache_data(ttl=86400, show_spinner=False)
def load_image(url):

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type", ""
        )

        if not content_type.startswith("image/"):
            return None

        return response.content

    except Exception:
        return None


# ==================================================
# 5. CSS GIAO DIỆN
# ==================================================

st.markdown("""
<style>

/* NỀN */
.main {
    background: #f7f8fc;
}

/* TIÊU ĐỀ */
h1 {
    font-weight: 800 !important;
    color: #202938;
}

/* ANIMATION */
@keyframes productAppear {
    from {
        opacity: 0;
        transform: translateY(15px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* THẺ SẢN PHẨM */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 14px !important;
    padding: 10px !important;

    height: 100% !important;
    box-sizing: border-box !important;

    animation: productAppear 0.45s ease both;

    transition:
        transform 0.3s ease,
        box-shadow 0.3s ease,
        border-color 0.3s ease;
}

/* HOVER */
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-5px);

    border-color: #16a34a !important;

    box-shadow:
        0 10px 25px rgba(0, 0, 0, 0.10);
}

/* ẢNH */
div[data-testid="stImage"] {
    width: 100% !important;
    height: 180px !important;

    overflow: hidden !important;
    border-radius: 10px !important;

    display: block !important;
}

/* ÉP TẤT CẢ ẢNH CÙNG KHUNG */
div[data-testid="stImage"] img {
    display: block !important;

    width: 100% !important;
    height: 180px !important;

    min-height: 180px !important;
    max-height: 180px !important;

    object-fit: cover !important;
    object-position: center center !important;

    border-radius: 10px !important;

    transition: transform 0.4s ease !important;
}

/* ZOOM ẢNH */
div[data-testid="stVerticalBlockBorderWrapper"]:hover
div[data-testid="stImage"] img {
    transform: scale(1.06);
}

/* ẢNH LỖI */
.image-fallback {
    width: 100%;
    height: 180px;

    background: linear-gradient(
        135deg,
        #e8f5e9,
        #d1fae5
    );

    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

    border-radius: 10px;
    color: #15803d;
    font-size: 38px;
}

/* TÊN SẢN PHẨM */
.product-name {
    height: 48px;
    min-height: 48px;
    max-height: 48px;

    overflow: hidden;

    display: flex;
    align-items: flex-start;

    font-size: 14px;
    font-weight: 700;
    line-height: 1.5;
    color: #202938;

    margin-top: 10px;
}

/* GIÁ */
.product-price {
    font-size: 19px;
    font-weight: 800;

    color: #16a34a;

    margin-top: 8px;
    margin-bottom: 8px;
}

/* THÀNH TIỀN */
.product-subtotal {
    font-size: 12px;
    color: #888888;

    min-height: 22px;
    margin-top: 5px;
}

/* INPUT */
div[data-testid="stNumberInput"] input {
    border-radius: 8px !important;
}

/* BUTTON */
div.stButton > button {
    border-radius: 9px !important;
    font-weight: 600 !important;

    transition: all 0.25s ease !important;
}

/* BUTTON HOVER */
div.stButton > button:hover {
    transform: translateY(-2px);

    border-color: #16a34a !important;
    color: #16a34a !important;

    box-shadow:
        0 5px 12px rgba(22, 163, 74, 0.15);
}

/* BUTTON CLICK */
div.stButton > button:active {
    transform: scale(0.97);
}

/* CỘT */
div[data-testid="stHorizontalBlock"] {
    align-items: stretch;
}

/* GIÁ TỔNG */
.total-payment {
    background: #e8f5e9;

    border: 1px solid #bbf7d0;

    padding: 20px;
    border-radius: 12px;

    text-align: right;
}

.total-payment .label {
    font-size: 15px;
    color: #374151;
}

.total-payment .amount {
    font-size: 28px;
    font-weight: 800;
    color: #16a34a;
}

/* FOOTER */
.footer {
    text-align: center;
    color: #888;
    font-size: 13px;
}

/* GIẢM ANIMATION NẾU THIẾT BỊ YÊU CẦU */
@media (prefers-reduced-motion: reduce) {
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stImage"] img {
        animation: none !important;
        transition: none !important;
    }
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 6. HÀM HỖ TRỢ
# ==================================================

def format_money(number):
    return f"{int(number):,}".replace(",", ".") + " đ"


def get_connection():

    conn = sqlite3.connect(DB_NAME)

    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ==================================================
# 7. KHỞI TẠO DATABASE
# ==================================================

def init_db():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL,
            total_amount INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pos_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price INTEGER NOT NULL,
            subtotal INTEGER NOT NULL,

            FOREIGN KEY (order_code)
            REFERENCES pos_orders(order_code)
            ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ==================================================
# 8. LẤY ĐƠN HÀNG
# ==================================================

def get_orders():

    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT *
        FROM pos_orders
        ORDER BY id DESC
    """, conn)

    conn.close()

    return df


# ==================================================
# 9. CHI TIẾT ĐƠN HÀNG
# ==================================================

def get_order_items(order_code):

    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT
            product_name AS 'Tên món',
            quantity AS 'Số lượng',
            price AS 'Đơn giá',
            subtotal AS 'Thành tiền'

        FROM pos_order_items

        WHERE order_code = ?

        ORDER BY id ASC
    """, conn, params=(order_code,))

    conn.close()

    return df


# ==================================================
# 10. LƯU ĐƠN HÀNG
# ==================================================

def save_order(customer_name, phone, note, cart):

    customer_name = customer_name.strip()
    phone = phone.strip()

    if not customer_name:
        return False, "Vui lòng nhập tên khách hàng."

    if not phone:
        return False, "Vui lòng nhập số điện thoại."

    if not cart:
        return False, "Giỏ hàng chưa có sản phẩm."

    total_amount = sum(
        item["quantity"] * item["price"]
        for item in cart
    )

    now = datetime.now()

    order_code = "DH" + now.strftime(
        "%Y%m%d%H%M%S%f"
    )

    created_at = now.strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO pos_orders (
                order_code,
                customer_name,
                phone,
                note,
                created_at,
                total_amount
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            order_code,
            customer_name,
            phone,
            note,
            created_at,
            total_amount
        ))

        for item in cart:

            subtotal = (
                item["quantity"] * item["price"]
            )

            cursor.execute("""
                INSERT INTO pos_order_items (
                    order_code,
                    product_name,
                    quantity,
                    price,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                order_code,
                item["product_name"],
                item["quantity"],
                item["price"],
                subtotal
            ))

        conn.commit()

        return True, order_code

    except Exception as e:

        conn.rollback()

        return False, str(e)

    finally:

        conn.close()


# ==================================================
# 11. XÓA ĐƠN HÀNG
# ==================================================

def delete_order(order_code):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM pos_order_items
            WHERE order_code = ?
        """, (order_code,))

        cursor.execute("""
            DELETE FROM pos_orders
            WHERE order_code = ?
        """, (order_code,))

        conn.commit()

        return True

    except Exception:

        conn.rollback()

        return False

    finally:

        conn.close()


# ==================================================
# 12. XUẤT EXCEL
# ==================================================

def create_excel():

    conn = get_connection()

    orders = pd.read_sql_query("""
        SELECT
            order_code AS 'Mã đơn hàng',
            customer_name AS 'Tên khách hàng',
            phone AS 'Số điện thoại',
            note AS 'Ghi chú',
            created_at AS 'Ngày tạo',
            total_amount AS 'Tổng tiền'

        FROM pos_orders

        ORDER BY id DESC
    """, conn)

    items = pd.read_sql_query("""
        SELECT
            order_code AS 'Mã đơn hàng',
            product_name AS 'Tên món',
            quantity AS 'Số lượng',
            price AS 'Đơn giá',
            subtotal AS 'Thành tiền'

        FROM pos_order_items

        ORDER BY id DESC
    """, conn)

    conn.close()

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        orders.to_excel(
            writer,
            sheet_name="Danh sách đơn hàng",
            index=False
        )

        items.to_excel(
            writer,
            sheet_name="Chi tiết sản phẩm",
            index=False
        )

        for sheet in writer.sheets.values():

            sheet.freeze_panes = "A2"

            for column_cells in sheet.columns:

                max_length = max(
                    len(str(cell.value or ""))
                    for cell in column_cells
                )

                column_letter = (
                    column_cells[0].column_letter
                )

                sheet.column_dimensions[
                    column_letter
                ].width = min(
                    max_length + 3,
                    35
                )

    output.seek(0)

    return output


# ==================================================
# 13. KHỞI TẠO SESSION
# ==================================================

init_db()

if "cart" not in st.session_state:
    st.session_state.cart = []

if "success_order" not in st.session_state:
    st.session_state.success_order = None

if "clear_customer_fields" not in st.session_state:
    st.session_state.clear_customer_fields = False


# XÓA THÔNG TIN KHÁCH HÀNG SAU THANH TOÁN
# Phải thực hiện trước khi tạo widget input.

if st.session_state.clear_customer_fields:

    st.session_state.customer_name = ""
    st.session_state.customer_phone = ""
    st.session_state.order_note = ""

    st.session_state.clear_customer_fields = False


if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""

if "customer_phone" not in st.session_state:
    st.session_state.customer_phone = ""

if "order_note" not in st.session_state:
    st.session_state.order_note = ""


# ==================================================
# 14. GIAO DIỆN CHÍNH
# ==================================================

st.title("☕ CafePOS")

st.caption(
    "Phần mềm quản lý bán hàng quán nước"
)

if st.session_state.success_order:

    st.success(
        f"🎉 ORDER THÀNH CÔNG! "
        f"Mã đơn: {st.session_state.success_order}",
        icon="✅"
    )

    st.session_state.success_order = None

st.divider()

tab1, tab2, tab3, tab4 = st.tabs([
    "🛒 Tạo đơn hàng",
    "📋 Danh sách đơn hàng",
    "📊 Thống kê",
    "📥 Xuất Excel"
])


# ==================================================
# TAB 1: TẠO ĐƠN HÀNG
# ==================================================

with tab1:

    st.header("Tạo đơn hàng mới")

    # ----------------------------------------------
    # THÔNG TIN KHÁCH HÀNG
    # ----------------------------------------------

    st.subheader("👤 Thông tin khách hàng")

    col1, col2 = st.columns(2)

    with col1:

        customer_name = st.text_input(
            "Tên khách hàng *",
            placeholder="Bắt buộc nhập tên khách hàng",
            key="customer_name"
        )

    with col2:

        phone = st.text_input(
            "Số điện thoại *",
            placeholder="Bắt buộc nhập số điện thoại",
            key="customer_phone"
        )

    st.caption(
        "🔴 Bắt buộc nhập đầy đủ tên khách hàng và số điện thoại."
    )

    st.divider()

    # ----------------------------------------------
    # DANH MỤC SẢN PHẨM
    # ----------------------------------------------

    st.subheader("🧋 MENU ĐỒ UỐNG")

    categories = [
        "Tất cả",
        "Cà phê",
        "Trà",
        "Trà sữa",
        "Nước ép",
        "Sinh tố",
        "Soda",
        "Khác"
    ]

    selected_category = st.radio(
        "Danh mục sản phẩm",
        categories,
        horizontal=True,
        key="product_category"
    )

    # ----------------------------------------------
    # LỌC SẢN PHẨM
    # ----------------------------------------------

    filtered_products = []

    for product in MENU:

        if selected_category == "Tất cả":
            filtered_products.append(product)

        elif selected_category == "Cà phê":

            if "Cà phê" in product:
                filtered_products.append(product)

        elif selected_category == "Trà":

            if (
                product.startswith("Trà ")
                and "Trà sữa" not in product
            ):
                filtered_products.append(product)

        elif selected_category == "Trà sữa":

            if (
                "Trà sữa" in product
                or "Sữa tươi" in product
            ):
                filtered_products.append(product)

        elif selected_category == "Nước ép":

            if "Nước ép" in product:
                filtered_products.append(product)

        elif selected_category == "Sinh tố":

            if "Sinh tố" in product:
                filtered_products.append(product)

        elif selected_category == "Soda":

            if "Soda" in product:
                filtered_products.append(product)

        elif selected_category == "Khác":

            if product in ["Ca cao đá", "Nước suối"]:
                filtered_products.append(product)

    st.caption(
        f"Đang hiển thị {len(filtered_products)} sản phẩm."
    )

    # ----------------------------------------------
    # HIỂN THỊ 5 SẢN PHẨM MỖI HÀNG
    # ----------------------------------------------

    for row_start in range(
        0,
        len(filtered_products),
        5
    ):

        row_products = filtered_products[
            row_start:row_start + 5
        ]

        cols = st.columns(5)

        for index, product in enumerate(row_products):

            price = MENU[product]
            image_url = get_product_image(product)

            with cols[index]:

                with st.container(border=True):

                    # ẢNH SẢN PHẨM

                    image_data = load_image(image_url)

                    if image_data:

                        st.image(
                            BytesIO(image_data),
                            use_container_width=True
                        )

                    else:

                        st.markdown(
                            f"""
                            <div class="image-fallback">
                                🥤
                                <span style="
                                    font-size:12px;
                                    margin-top:8px;
                                ">
                                    {html.escape(product)}
                                </span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    # TÊN SẢN PHẨM

                    st.markdown(
                        f"""
                        <div class="product-name">
                            {html.escape(product)}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # GIÁ TIỀN

                    st.markdown(
                        f"""
                        <div class="product-price">
                            {format_money(price)}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # CHỌN SỐ LƯỢNG

                    quantity = st.number_input(
                        "Số lượng",
                        min_value=1,
                        max_value=1000,
                        value=1,
                        step=1,
                        key=f"quantity_{product}"
                    )

                    # THÀNH TIỀN

                    subtotal = price * int(quantity)

                    st.markdown(
                        f"""
                        <div class="product-subtotal">
                            Thành tiền: {format_money(subtotal)}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # THÊM VÀO ĐƠN

                    if st.button(
                        "➕ Thêm vào đơn",
                        key=f"add_{product}",
                        use_container_width=True
                    ):

                        existing_item = next(
                            (
                                item
                                for item in st.session_state.cart
                                if item["product_name"] == product
                            ),
                            None
                        )

                        if existing_item:

                            existing_item["quantity"] += int(
                                quantity
                            )

                        else:

                            st.session_state.cart.append({
                                "product_name": product,
                                "quantity": int(quantity),
                                "price": price
                            })

                        st.toast(
                            f"Đã thêm {product} vào đơn hàng!",
                            icon="✅"
                        )

                        st.rerun()

    # ==================================================
    # GIỎ HÀNG
    # ==================================================

    st.divider()

    st.subheader("🧾 GIỎ HÀNG HIỆN TẠI")

    if st.session_state.cart:

        total_order = 0

        # TIÊU ĐỀ

        col1, col2, col3, col4, col5 = st.columns(
            [3, 1, 1.5, 1.5, 1]
        )

        col1.write("**Tên sản phẩm**")
        col2.write("**SL**")
        col3.write("**Đơn giá**")
        col4.write("**Thành tiền**")
        col5.write("**Xóa**")

        st.divider()

        for index, item in enumerate(
            st.session_state.cart
        ):

            subtotal = (
                item["quantity"] * item["price"]
            )

            total_order += subtotal

            col1, col2, col3, col4, col5 = st.columns(
                [3, 1, 1.5, 1.5, 1]
            )

            with col1:
                st.write(f"**{item['product_name']}**")

            with col2:
                st.write(item["quantity"])

            with col3:
                st.write(format_money(item["price"]))

            with col4:
                st.write(f"**{format_money(subtotal)}**")

            with col5:

                if st.button(
                    "🗑️",
                    key=f"remove_cart_{index}"
                ):

                    st.session_state.cart.pop(index)

                    st.rerun()

        st.divider()

        # TỔNG TIỀN

        st.markdown(
            f"""
            <div class="total-payment">
                <div class="label">
                    TỔNG THANH TOÁN
                </div>

                <div class="amount">
                    {format_money(total_order)}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

        # GHI CHÚ

        note = st.text_area(
            "Ghi chú đơn hàng",
            placeholder="Ví dụ: Ít đá, ít đường...",
            key="order_note"
        )

        st.divider()

        col1, col2 = st.columns(2)

        # THANH TOÁN

        with col1:

            if st.button(
                "✅ THANH TOÁN / LƯU ĐƠN",
                type="primary",
                use_container_width=True
            ):

                if not customer_name.strip():

                    st.error(
                        "⚠️ Vui lòng nhập tên khách hàng."
                    )

                elif not phone.strip():

                    st.error(
                        "⚠️ Vui lòng nhập số điện thoại."
                    )

                elif not st.session_state.cart:

                    st.error(
                        "⚠️ Giỏ hàng chưa có sản phẩm."
                    )

                else:

                    success, result = save_order(
                        customer_name,
                        phone,
                        note,
                        st.session_state.cart
                    )

                    if success:

                        # XÓA GIỎ HÀNG

                        st.session_state.cart = []

                        # ĐÁNH DẤU XÓA THÔNG TIN KHÁCH

                        st.session_state.clear_customer_fields = True

                        # THÔNG BÁO THÀNH CÔNG

                        st.session_state.success_order = result

                        st.rerun()

                    else:

                        st.error(
                            f"Không thể lưu đơn hàng: {result}"
                        )

        # XÓA GIỎ HÀNG

        with col2:

            if st.button(
                "🗑️ Xóa toàn bộ giỏ hàng",
                use_container_width=True
            ):

                st.session_state.cart = []

                st.rerun()

    else:

        st.info(
            "Chưa có món nước nào trong đơn hàng. "
            "Hãy chọn sản phẩm phía trên."
        )


# ==================================================
# TAB 2: DANH SÁCH ĐƠN HÀNG
# ==================================================

with tab2:

    st.header("📋 Danh sách đơn hàng")

    orders = get_orders()

    if not orders.empty:

        col1, col2 = st.columns(2)

        with col1:

            search = st.text_input(
                "🔎 Tìm kiếm mã đơn / khách hàng / số điện thoại",
                placeholder="Nhập thông tin cần tìm"
            )

        with col2:

            selected_date = st.date_input(
                "Lọc theo ngày",
                value=None,
                format="DD/MM/YYYY",
                key="filter_order_date"
            )

        filtered_orders = orders.copy()

        # TÌM KIẾM

        if search:

            search_lower = search.lower()

            filtered_orders = filtered_orders[
                filtered_orders["order_code"].astype(str).str.lower().str.contains(
                    search_lower,
                    na=False
                )
                |
                filtered_orders["customer_name"].astype(str).str.lower().str.contains(
                    search_lower,
                    na=False
                )
                |
                filtered_orders["phone"].astype(str).str.lower().str.contains(
                    search_lower,
                    na=False
                )
            ]

        # LỌC NGÀY

        if selected_date:

            order_dates = pd.to_datetime(
                filtered_orders["created_at"],
                format="%d/%m/%Y %H:%M:%S",
                errors="coerce"
            ).dt.date

            filtered_orders = filtered_orders[
                order_dates == selected_date
            ]

        st.write(
            f"Tìm thấy **{len(filtered_orders)} đơn hàng**."
        )

        display_orders = filtered_orders.copy()

        display_orders = display_orders.rename(
            columns={
                "order_code": "Mã đơn hàng",
                "customer_name": "Khách hàng",
                "phone": "Số điện thoại",
                "note": "Ghi chú",
                "created_at": "Ngày tạo",
                "total_amount": "Tổng tiền"
            }
        )

        if not display_orders.empty:

            display_orders["Tổng tiền"] = (
                display_orders["Tổng tiền"].apply(format_money)
            )

        st.dataframe(
            display_orders,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("🔍 Xem chi tiết / Xóa đơn hàng")

        order_options = filtered_orders[
            "order_code"
        ].tolist()

        if order_options:

            selected_order = st.selectbox(
                "Chọn mã đơn hàng",
                options=order_options
            )

            selected_info = filtered_orders[
                filtered_orders["order_code"] == selected_order
            ].iloc[0]

            st.write(
                f"**Mã đơn:** {selected_info['order_code']}"
            )

            st.write(
                f"**Khách hàng:** {selected_info['customer_name']}"
            )

            st.write(
                f"**Số điện thoại:** {selected_info['phone']}"
            )

            st.write(
                f"**Ngày tạo:** {selected_info['created_at']}"
            )

            st.write(
                f"**Ghi chú:** {selected_info['note'] or 'Không có'}"
            )

            details = get_order_items(selected_order)

            if not details.empty:

                display_details = details.copy()

                display_details["Đơn giá"] = (
                    display_details["Đơn giá"].apply(format_money)
                )

                display_details["Thành tiền"] = (
                    display_details["Thành tiền"].apply(format_money)
                )

                st.dataframe(
                    display_details,
                    use_container_width=True,
                    hide_index=True
                )

            st.markdown(
                f"### Tổng đơn: :green[{format_money(selected_info['total_amount'])}]"
            )

            st.divider()

            st.warning(
                f"Bạn đang chọn đơn hàng {selected_order}. "
                "Nếu xóa, toàn bộ sản phẩm thuộc đơn này cũng sẽ bị xóa."
            )

            confirm = st.checkbox(
                "Tôi xác nhận muốn xóa đơn hàng này",
                key=f"confirm_{selected_order}"
            )

            if st.button(
                "🗑️ XÓA ĐƠN HÀNG ĐANG CHỌN",
                type="primary",
                disabled=not confirm,
                use_container_width=True
            ):

                if delete_order(selected_order):

                    st.success(
                        f"Đã xóa đơn hàng {selected_order} thành công."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Không thể xóa đơn hàng. Vui lòng thử lại."
                    )

        else:

            st.info("Không tìm thấy đơn hàng phù hợp.")

    else:

        st.info("Chưa có đơn hàng nào được lưu.")


# ==================================================
# TAB 3: THỐNG KÊ
# ==================================================

with tab3:

    st.header("📊 Thống kê bán hàng")

    orders = get_orders()

    if not orders.empty:

        orders["date_only"] = pd.to_datetime(
            orders["created_at"],
            format="%d/%m/%Y %H:%M:%S",
            errors="coerce"
        ).dt.date

        today = date.today()

        today_orders = orders[
            orders["date_only"] == today
        ]

        today_revenue = today_orders[
            "total_amount"
        ].sum()

        total_revenue = orders[
            "total_amount"
        ].sum()

        total_orders = len(orders)

        conn = get_connection()

        items = pd.read_sql_query("""
            SELECT *
            FROM pos_order_items
        """, conn)

        conn.close()

        total_products = (
            items["quantity"].sum()
            if not items.empty else 0
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Doanh thu hôm nay",
            format_money(today_revenue)
        )

        col2.metric(
            "Tổng doanh thu",
            format_money(total_revenue)
        )

        col3.metric(
            "Tổng số đơn",
            f"{total_orders:,}".replace(",", ".")
        )

        col4.metric(
            "Tổng số món đã bán",
            f"{int(total_products):,}".replace(",", ".")
        )

        st.divider()

        # DOANH THU THEO NGÀY

        st.subheader("📈 Doanh thu theo ngày")

        daily_revenue = (
            orders.groupby("date_only")["total_amount"]
            .sum()
            .sort_index()
        )

        daily_revenue = daily_revenue.dropna()

        daily_revenue.index = (
            daily_revenue.index.astype(str)
        )

        st.bar_chart(daily_revenue)

        st.divider()

        # MÓN BÁN CHẠY

        st.subheader("🏆 Các món bán chạy")

        if not items.empty:

            top_products = (
                items.groupby("product_name")["quantity"]
                .sum()
                .sort_values(ascending=False)
            )

            top_products = top_products.rename(
                "Số lượng bán"
            )

            st.bar_chart(top_products)

            top_table = top_products.reset_index()

            top_table = top_table.rename(
                columns={
                    "product_name": "Tên món"
                }
            )

            st.dataframe(
                top_table,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("Chưa có dữ liệu sản phẩm.")

    else:

        st.info("Chưa có dữ liệu để thống kê.")


# ==================================================
# TAB 4: XUẤT EXCEL
# ==================================================

with tab4:

    st.header("📥 Xuất dữ liệu Excel")

    orders = get_orders()

    if not orders.empty:

        st.write(
            f"Hiện tại có **{len(orders)} đơn hàng** trong hệ thống."
        )

        st.write(
            "File Excel bao gồm danh sách đơn hàng "
            "và chi tiết từng sản phẩm."
        )

        excel_file = create_excel()

        st.download_button(
            label="📥 TẢI FILE EXCEL",
            data=excel_file,
            file_name=(
                f"CafePOS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )

    else:

        st.info("Chưa có đơn hàng để xuất Excel.")


# ==================================================
# 15. CHÂN TRANG
# ==================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        ☕ CafePOS | Phần mềm quản lý bán hàng quán nước
    </div>
    """,
    unsafe_allow_html=True
)
