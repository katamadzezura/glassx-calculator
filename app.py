import uuid
import streamlit as st

ROLL_WIDTH = 150.0
st.set_page_config(page_title="GlassX Calculator", page_icon="📐", layout="centered")
st.title("GlassX | ფირის კალკულატორი")
st.caption("150 სმ რულონი • ჭრის წინასწარი დაგეგმვა")


def new_pane():
    return {"id": uuid.uuid4().hex, "rotate": False}


if "panes" not in st.session_state:
    st.session_state.panes = [new_pane()]

with st.expander("ფასი და პარამეტრები", expanded=True):
    currency = st.selectbox("ფასის ვალუტა", ["GEL", "USD"])
    unit_price = st.number_input("გასაყიდი ფასი 1 მ²-ზე", min_value=0.0, value=0.0, step=1.0)
    usd_rate = st.number_input("დოლარის კურსი (1 USD = GEL)", min_value=0.01, value=2.60, step=0.01, format="%.4f")

st.subheader("მინები")
a, b = st.columns(2)
if a.button("🔄 ყველას ტრიალის ჩართვა", use_container_width=True):
    for pane in st.session_state.panes:
        pane["rotate"] = True
        st.session_state[f"rotate_{pane['id']}"] = True
    st.rerun()
if b.button("⛔ ყველას ტრიალის გამორთვა", use_container_width=True):
    for pane in st.session_state.panes:
        pane["rotate"] = False
        st.session_state[f"rotate_{pane['id']}"] = False
    st.rerun()

for index, pane in enumerate(st.session_state.panes):
    pid = pane["id"]
    head, trash = st.columns([5, 1])
    head.markdown(f"**მინა #{index + 1}**")
    if trash.button("🗑️", key=f"delete_{pid}", help="ამ მინის წაშლა"):
        st.session_state.panes = [p for p in st.session_state.panes if p["id"] != pid]
        for prefix in ("w", "h", "q", "rotate"):
            st.session_state.pop(f"{prefix}_{pid}", None)
        st.rerun()
    x, y, z = st.columns(3)
    x.number_input("სიგანე, სმ", min_value=0.0, value=None, step=1.0, placeholder="შეიყვანე", key=f"w_{pid}")
    y.number_input("სიმაღლე, სმ", min_value=0.0, value=None, step=1.0, placeholder="შეიყვანე", key=f"h_{pid}")
    z.number_input("ცალი", min_value=1, max_value=100, value=1, step=1, key=f"q_{pid}")
    pane["rotate"] = st.toggle("90°-ით ტრიალის დაშვება", value=pane["rotate"], key=f"rotate_{pid}")
    st.divider()

if st.button("➕ მინის დამატება", use_container_width=True):
    st.session_state.panes.append(new_pane())
    st.rerun()

pieces = []
incomplete = False
for index, pane in enumerate(st.session_state.panes):
    pid = pane["id"]
    w, h = st.session_state.get(f"w_{pid}"), st.session_state.get(f"h_{pid}")
    if w is None or h is None or w <= 0 or h <= 0:
        incomplete = True
        continue
    for n in range(st.session_state.get(f"q_{pid}", 1)):
        pieces.append({"width": float(w), "height": float(h), "rotate": pane["rotate"], "label": f"{index+1}.{n+1}"})


def pack(order):
    shelves, positions = [], []
    for piece in order:
        orientations = [(piece["width"], piece["height"], False)]
        if piece["rotate"] and piece["width"] != piece["height"]:
            orientations.append((piece["height"], piece["width"], True))
        best = None
        for w, h, rotated in orientations:
            if w > ROLL_WIDTH + 1e-8:
                continue
            for j, shelf in enumerate(shelves):
                if w <= ROLL_WIDTH - shelf["used"] + 1e-8 and h <= shelf["height"] + 1e-8:
                    score = (0, shelf["height"] - h, ROLL_WIDTH - shelf["used"] - w)
                    if best is None or score < best[0]:
                        best = (score, j, w, h, rotated)
            score = (1, h, ROLL_WIDTH - w)
            if best is None or score < best[0]:
                best = (score, None, w, h, rotated)
        if best is None:
            return None
        _, j, w, h, rotated = best
        if j is None:
            yy = sum(s["height"] for s in shelves)
            shelves.append({"used": w, "height": h, "y": yy})
            xx = 0.0
        else:
            shelf = shelves[j]
            xx, yy = shelf["used"], shelf["y"]
            shelf["used"] += w
        positions.append((xx, yy, w, h, piece["label"], rotated))
    return sum(s["height"] for s in shelves), positions, shelves


if not st.session_state.panes:
    st.info("დაამატე მინა დასათვლელად.")
elif incomplete:
    st.info("შეავსე ყველა მინის სიგანე და სიმაღლე შედეგის სანახავად.")
else:
    orders = [
        sorted(pieces, key=lambda p: p["width"] * p["height"], reverse=True),
        sorted(pieces, key=lambda p: max(p["width"], p["height"]), reverse=True),
        sorted(pieces, key=lambda p: min(p["width"], p["height"]), reverse=True),
        sorted(pieces, key=lambda p: p["height"], reverse=True),
    ]
    results = [r for order in orders if (r := pack(order)) is not None]
    if not results:
        st.error("ერთი ან მეტი მინა 150 სმ რულონში ვერ ეტევა დაშვებული ტრიალის პირობებში. შეამოწმე ზომები ან ჩართე შესაბამისი მინის ტრიალი.")
    else:
        length, positions, shelves = min(results, key=lambda r: r[0])
        area = ROLL_WIDTH * length / 10000
        used = sum(p["width"] * p["height"] for p in pieces) / 10000
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
        height_px = max(100, min(900, int(length * min(3.0, 850.0 / max(length, 1)) + 40)))
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 {length+25:.2f}" style="width:100%;max-height:850px;background:#f4f6f8">']
        svg.append(f'<rect x="10" y="5" width="150" height="{length:.2f}" fill="#f2d995" stroke="#9c7833"/>')
        colors = ["#2878b8", "#168b7e", "#7855b7", "#c47735", "#af557e"]
        for i, (x, y, w, h, label, rotated) in enumerate(positions):
            svg.append(f'<rect x="{x+10:.2f}" y="{y+5:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{colors[i % len(colors)]}" stroke="white" stroke-width="0.8"/>')
            if w >= 22 and h >= 16:
                svg.append(f'<text x="{x+10+w/2:.2f}" y="{y+5+h/2:.2f}" fill="white" font-size="7" text-anchor="middle">{w:g}×{h:g}</text>')
        for shelf in shelves:
            leftover = ROLL_WIDTH - shelf["used"]
            if leftover >= 15:
                svg.append(f'<text x="{10+shelf["used"]+leftover/2:.2f}" y="{5+shelf["y"]+shelf["height"]/2:.2f}" fill="#5e4b24" font-size="7" text-anchor="middle">{leftover:g}×{shelf["height"]:g}</text>')
        svg.append(f'<text x="85" y="{length+18:.2f}" fill="#333" font-size="9" text-anchor="middle">150 სმ</text></svg>')
        st.components.v1.html("".join(svg), height=height_px, scrolling=True)
        st.caption("ყვითელი — დარჩენილი ფირი. სქემა წინასწარია; ოპტიმალურობის გარანტია არ აქვს. ჭრის დანაკარგი და ნარჩენების საწყობი ჯერ არ არის ჩართული.")
        lines = ["GlassX - Price Estimate"]
        for index, pane in enumerate(st.session_state.panes):
            pid = pane["id"]
            lines.append(f"Glass {index+1}: {st.session_state[f'w_{pid}']} x {st.session_state[f'h_{pid}']} cm - {st.session_state[f'q_{pid}']} pcs; rotation: {'yes' if pane['rotate'] else 'no'}")
        lines.append(f"Roll length: {length:.2f} cm\nBillable area: {area:.3f} m2\nWaste: {waste:.3f} m2\nPrice: {total:.2f} {currency}\nGEL: {total_gel:.2f}\nUSD: {total_usd:.2f}\nUSD exchange rate: {usd_rate:.4f}\nInstallation: separate estimate")
        st.download_button("📄 შედეგის შენახვა (TXT)", data="\n".join(lines), file_name="glassx-estimate.txt", mime="text/plain")
