
# ==================================================
# HIỂN THỊ 5 SẢN PHẨM TRÊN 1 HÀNG
# CÓ GIÁ TIỀN VÀ CHỌN SỐ LƯỢNG
# ==================================================

for row_start in range(0, len(filtered_products), 5):

    row_products = filtered_products[
        row_start:row_start + 5
    ]

    cols = st.columns(5)

    for index, product in enumerate(row_products):

        price = MENU[product]
        image_url = get_product_image(product)

        with cols[index]:

            with st.container(border=True):

                # HÌNH ẢNH
                st.image(
                    image_url,
                    use_container_width=True
                )

                # TÊN SẢN PHẨM
                st.markdown(
                    f"<div class='product-name'>{product}</div>",
                    unsafe_allow_html=True
                )

                # GIÁ TIỀN
                st.markdown(
                    f"""
                    <div class='product-price'>
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

                # THÀNH TIỀN TẠM TÍNH
                st.caption(
                    f"Thành tiền: **{format_money(price * quantity)}**"
                )

                # NÚT THÊM VÀO ĐƠN
                if st.button(
                    "➕ Thêm vào đơn",
                    key=f"add_{product}",
                    use_container_width=True
                ):

                    existing_item = next(
                        (
                            item for item in st.session_state.cart
                            if item["product_name"] == product
                        ),
                        None
                    )

                    if existing_item:

                        existing_item["quantity"] += int(quantity)

                    else:

                        st.session_state.cart.append({
                            "product_name": product,
                            "quantity": int(quantity),
                            "price": price
                        })

                    st.toast(
                        f"Đã thêm {quantity} x {product} vào đơn hàng!",
                        icon="✅"
                    )

                    st.rerun()
