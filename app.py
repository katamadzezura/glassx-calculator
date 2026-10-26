import streamlit as st

ROLL_WIDTH = 150.0

st.set_page_config(page_title="GlassX Calculator", page_icon="📐", layout="centered")
st.title("GlassX | ფირის კალკულატორი")
st.caption("150 სმ რულონი • ჭრის წინასწარი დაგეგმვა")

if "panes" not in st.session_state:
    st.session_state.panes = [
        {"width": 60.0, "height": 200.0, "qty": 1},
        {"width": 60.0, "height": 100.0, "qty": 2},
    ]

with st.expander("ფასი და პარამეტრები", expanded=True):
    currency = st.selectbox("ფასის ვალუტა", ["GEL", "USD"])
    unit_price = st.number_input("გასაყიდი ფასი 1 მ²-ზე", min_value=0.0, value=390.0 if currency == "GEL" else 150.0, step=1.0, key=f"price_{currency}")
    usd_rate = st.number_input("დოლარის კურსი (1 USD = GEL)", min_value=0.01, value=2.60, step=0.01)
    margin = st.number_input("დამატებითი მარაგი თითოეულ მხარეს (სმ)", min_value=0.0, value=0.0, step=0.1)

st.subheader("მინები")
for i, pane in enumerate(st.session_state.panes):
    st.markdown(f"**მინა #{i + 1}**")
    a, b, c = st.columns(3)
    pane["width"] = a.number_input("სიგანე, სმ", min_value=0.1, value=float(pane["width"]), step=1.0, key=f"w_{i}")
    pane["height"] = b.number_input("სიმაღლე, სმ", min_value=0.1, value=float(pane["height"]), step=1.0, key=f"h_{i}")
    pane["qty"] = c.number_input("ცალი", min_value=1, max_value=50, value=int(pane["qty"]), step=1, key=f"q_{i}")

left, right = st.columns(2)
if left.button("➕ მინის დამატება", use_container_width=True):
    st.session_state.panes.append({"width": 60.0, "height": 100.0, "qty": 1})
    st.rerun()
if right.button("➖ ბოლო მინის წაშლა", disabled=len(st.session_state.panes) <= 1, use_container_width=True):
    st.session_state.panes.pop()
    st.rerun()

pieces = []
for pane in st.session_state.panes:
    for _ in range(pane["qty"]):
        pieces.append((pane["width"] + 2 * margin, pane["height"] + 2 * margin))

# Shelf packing heuristic: test different piece orders and orientations.
# This is an estimate, not a guaranteed globally optimal cutting plan.
def pack(order):
    shelves = []
    positions = []
    for width, height in order:
        best = None
        for rotated, (w, h) in enumerate(((width, height), (height, width))):
            if w > ROLL_WIDTH:
                continue
            for index, shelf in enumerate(shelves):
                if w <= ROLL_WIDTH - shelf["used"] and h <= shelf["height"]:
                    score = (0, shelf["height"] - h, ROLL_WIDTH - shelf["used"] - w)
                    if best is None or score < best[0]:
                        best = (score, index, w, h, rotated)
            y = sum(s["height"] for s in shelves)
            score = (1, h, ROLL_WIDTH - w)
            if best is None or score < best[0]:
                best = (score, None, w, h, rotated)
        if best is None:
            return None
        _, index, w, h, rotated = best
        if index is None:
            y = sum(s["height"] for s in shelves)
            shelves.append({"used": w, "height": h, "y": y})
            positions.append((0.0, y, w, h))
        else:
            shelf = shelves[index]
            positions.append((shelf["used"], shelf["y"], w, h))
            shelf["used"] += w
    return sum(s["height"] for s in shelves), positions, shelves

orders = [
    sorted(pieces, key=lambda x: x[0] * x[1], reverse=True),
    sorted(pieces, key=lambda x: max(x), reverse=True),
    sorted(pieces, key=lambda x: min(x), reverse=True),
    sorted(pieces, key=lambda x: x[1], reverse=True),
]
results = [pack(order) for order in orders]
results = [result for result in results if result is not None]

if not results:
    st.error("ერთი ან მეტი მინის ორივე გვერდი 150 სმ-ზე მეტია. საჭიროა ცალკე ჭრის გადაწყვეტა.")
else:
    length, positions, shelves = min(results, key=lambda r: r[0])
    area = ROLL_WIDTH * length / 10000
    used = sum(w * h for w, h in pieces) / 10000
    waste = max(0.0, area - used)
    total = area * unit_price
    total_gel = total if currency == "GEL" else total * usd_rate
    total_usd = total / usd_rate if currency == "GEL" else total

    st.subheader("შედეგი")
    st.metric("ფირის ფასი", f"{total:,.2f} {'₾' if currency == 'GEL' else '$'}")
    a, b = st.columns(2)
    a.metric("ჯამი ლარში", f"{total_gel:,.2f} ₾")
    b.metric("ჯამი დოლარში", f"{total_usd:,.2f} $")
    a, b = st.columns(2)
    a.metric("საჭირო ფირი", f"{area:.3f} მ²")
    b.metric("რულონის სიგრძე", f"{length:.1f} სმ")
    st.write(f"მინების რაოდენობა: **{len(pieces)}** | დარჩენილი ფართობი: **{waste:.3f} მ²**")
    st.info("მონტაჟი — ინდივიდუალური შეფასებით.")

    st.subheader("ჭრის სქემა")
    from html import escape
    scale = min(3.0, 850.0 / max(length, 1))
    height_px = max(60, length * scale + 30)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 190 {length+25:.2f}" style="width:100%;max-height:850px;background:#f4f6f8">']
    svg.append(f'<rect x="10" y="5" width="150" height="{length:.2f}" fill="#f2d995" stroke="#9c7833"/>')
    colors = ["#2878b8", "#168b7e", "#7855b7", "#c47735", "#af557e"]
    for i, (x, y, w, h) in enumerate(positions):
        svg.append(f'<rect x="{x+10:.2f}" y="{y+5:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{colors[i % len(colors)]}" stroke="white" stroke-width="0.8"/>')
        if w >= 30 and h >= 18:
            svg.append(f'<text x="{x+10+w/2:.2f}" y="{y+5+h/2:.2f}" fill="white" font-size="8" text-anchor="middle">{w:g}×{h:g}</text>')
    for shelf in shelves:
        leftover = ROLL_WIDTH - shelf["used"]
        if leftover >= 1:
            svg.append(f'<text x="{10+shelf["used"]+leftover/2:.2f}" y="{5+shelf["y"]+shelf["height"]/2:.2f}" fill="#5e4b24" font-size="7" text-anchor="middle">{leftover:g}×{shelf["height"]:g}</text>')
    svg.append(f'<text x="85" y="{length+18:.2f}" fill="#333" font-size="9" text-anchor="middle">150 სმ</text></svg>')
    st.components.v1.html("".join(svg), height=min(900, int(height_px)), scrolling=True)
    st.caption("ყვითელი — დარჩენილი ფირი. სქემა წინასწარია; ოპტიმალურობის გარანტია არ აქვს. ჭრის დანაკარგი და ნარჩენების საწყობი ჯერ არ არის ჩართული.")
    st.download_button("📄 შედეგის შენახვა (TXT)", data=(
        "GlassX - Price Estimate\n"
        + "\n".join(f"{p['width']} x {p['height']} cm - {p['qty']} pcs" for p in st.session_state.panes)
        + f"\nRoll length: {length:.2f} cm\nBillable area: {area:.3f} m2\nPrice: {total:.2f} {currency}\nGEL: {total_gel:.2f}\nUSD: {total_usd:.2f}\nInstallation: separate estimate\n"
    ), file_name="glassx-estimate.txt", mime="text/plain")
