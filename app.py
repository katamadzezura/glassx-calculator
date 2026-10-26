import uuid, csv, io, json
from datetime import date
from urllib.request import Request, urlopen
from html import escape
import streamlit as st

ROLL_WIDTH = 150.0
st.set_page_config(page_title='GlassX | Calculator', page_icon='🟪', layout='centered', initial_sidebar_state='collapsed')
st.markdown('''<style>
#MainMenu,footer,header[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stAppDeployButton"]{display:none!important}
.block-container{max-width:850px;padding-top:1.15rem;padding-bottom:3rem}
.brand{padding:15px 18px;border-radius:17px;background:linear-gradient(110deg,#28224d,#50429b 65%,#6c56c4);color:white;margin-bottom:14px}
.brand .name{font-size:32px;font-weight:850}.brand .tag{font-size:12px;opacity:.85}
.sectionline{font-size:19px;font-weight:750;margin:20px 0 9px}
.stButton>button[kind="primary"]{background:#6052c9!important;color:white!important}
</style>''', unsafe_allow_html=True)
TEXT = {
'ka':dict(tag='SMART FILM · პროფესიონალური კალკულატორი',settings='ფასი და პარამეტრები',currency='ვალუტა',film_rate='ფირის ფასი / მ²',install_rate='მონტაჟის ფასი / მ²',install_basis='მონტაჟის დათვლა შუშის ფართობით',exchange='USD → GEL კურსი',nbg='ეროვნული ბანკის კურსი',nbg_fail='კურსი ვერ ჩაიტვირთა. 2.60 დროებითი მნიშვნელობაა — გადაამოწმე.',refresh='↻ კურსის განახლება',customer='დამკვეთის მონაცემები',first='სახელი',last='გვარი',phone='ტელეფონი',address='მისამართი',date='თარიღი',glass='შუშები',all_on='↻ ყველას ტრიალის ჩართვა',all_off='⊘ ყველას ტრიალის გამორთვა',pane='შუშა',width='სიგანე (სმ)',height='სიმაღლე (სმ)',quantity='ცალი',rotate='ტრიალის დაშვება',add='＋ შუშის დამატება',remove='შუშის წაშლა',fill='შეავსე ყველა შუშის სიგანე და სიმაღლე.',empty='დაამატე შუშა დასათვლელად.',invalid='შუშა 150 სმ რულონში ვერ ეტევა.',results='ღირებულების შეჯამება',glass_area='შუშების ფართობი',film_area='საჭირო ფირი',length='რულონის სიგრძე',waste='ნარჩენი',count='შუშების რაოდენობა',film_cost='ფირის ღირებულება',install_cost='მონტაჟი',grand='საბოლოო ჯამი',cut='ჭრის განლაგება',cut_note='სქემა წინასწარია; ოპტიმალური ჭრის გარანტია არ აქვს. დამატებითი სანტიმეტრები არ ემატება.',download='↓ შეკვეთის ჩამოტვირთვა (CSV)',download_note='ფაილში შედის დამკვეთი, ზომები და ფასები — ჭრის განდეტალების გარეშე.',rotate_note='თუ მხოლოდ შემოტრიალებით ეტევა, ტრიალი ავტომატურად მოხდება.',required='შეიყვანე',order='შეკვეთა',units='მ²'),
'en':dict(tag='SMART FILM · Professional calculator',settings='Pricing and settings',currency='Currency',film_rate='Film price / m²',install_rate='Installation price / m²',install_basis='Calculate installation by glass area',exchange='USD → GEL exchange rate',nbg='National Bank rate',nbg_fail='Exchange rate unavailable. Verify the temporary 2.60 rate.',refresh='↻ Refresh rate',customer='Customer details',first='First name',last='Last name',phone='Phone',address='Address',date='Date',glass='Glass panels',all_on='↻ Allow rotation for all',all_off='⊘ Disable rotation for all',pane='Panel',width='Width (cm)',height='Height (cm)',quantity='Quantity',rotate='Allow rotation',add='＋ Add panel',remove='Delete panel',fill='Enter width and height for every panel.',empty='Add a panel to calculate.',invalid='A panel cannot fit the 150 cm roll.',results='Price summary',glass_area='Glass area',film_area='Film required',length='Roll length',waste='Offcut',count='Number of panels',film_cost='Film cost',install_cost='Installation',grand='Grand total',cut='Cutting layout',cut_note='Layout is approximate, not guaranteed optimal. No cutting allowance is added.',download='↓ Download order (CSV)',download_note='Contains customer details, panel sizes and prices, without cutting layout.',rotate_note='If a panel only fits when rotated, it rotates automatically.',required='Enter',order='Order',units='m²'),
'ru':dict(tag='SMART FILM · Профессиональный калькулятор',settings='Цены и параметры',currency='Валюта',film_rate='Цена плёнки / м²',install_rate='Стоимость монтажа / м²',install_basis='Рассчитывать монтаж по площади стекла',exchange='Курс USD → GEL',nbg='Курс Нацбанка',nbg_fail='Курс недоступен. Проверьте временное значение 2.60.',refresh='↻ Обновить курс',customer='Данные заказчика',first='Имя',last='Фамилия',phone='Телефон',address='Адрес',date='Дата',glass='Стёкла',all_on='↻ Разрешить поворот всех',all_off='⊘ Запретить поворот всех',pane='Стекло',width='Ширина (см)',height='Высота (см)',quantity='Количество',rotate='Разрешить поворот',add='＋ Добавить стекло',remove='Удалить стекло',fill='Укажите размеры всех стёкол.',empty='Добавьте стекло для расчёта.',invalid='Стекло не помещается в рулон 150 см.',results='Расчёт стоимости',glass_area='Площадь стекла',film_area='Требуется плёнки',length='Длина рулона',waste='Остаток',count='Количество стёкол',film_cost='Стоимость плёнки',install_cost='Монтаж',grand='Итого',cut='Схема раскроя',cut_note='Раскрой предварительный, оптимальность не гарантируется. Припуски не добавлены.',download='↓ Скачать заказ (CSV)',download_note='Данные клиента, размеры и цены, без схемы раскроя.',rotate_note='Если стекло помещается только при повороте, оно будет повернуто автоматически.',required='Введите',order='Заказ',units='м²')}
lang=st.selectbox('Language / ენა / Язык',['ka','en','ru'],format_func=lambda x:{'ka':'🇬🇪 ქართული','en':'🇬🇧 English','ru':'🇷🇺 Русский'}[x],key='language',label_visibility='collapsed')
t=TEXT[lang]
st.markdown(f'<div class="brand"><div class="name">GlassX / Calculator</div><div class="tag">{escape(t["tag"])}</div></div>',unsafe_allow_html=True)

def new_pane():return {'id':uuid.uuid4().hex,'rotate':False}
if 'panes' not in st.session_state:st.session_state.panes=[new_pane()]
@st.cache_data(ttl=3600,show_spinner=False)
def fetch_nbg_rate():
    url='https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/ka/json/?currencies=USD'
    req=Request(url,headers={'User-Agent':'GlassXCalculator/2.0','Accept':'application/json'})
    with urlopen(req,timeout=7) as response: payload=json.load(response)
    entry=payload[0]
    dollar=next(x for x in entry['currencies'] if x['code']=='USD')
    return float(dollar['rate'])/float(dollar.get('quantity',1)),str(entry.get('date',''))
if 'nbg_checked' not in st.session_state:
    try:
        rate,rate_date=fetch_nbg_rate()
        st.session_state.usd_rate=rate;st.session_state.nbg_date=rate_date;st.session_state.nbg_error=False
    except Exception:
        st.session_state.usd_rate=2.60;st.session_state.nbg_date='';st.session_state.nbg_error=True
    st.session_state.nbg_checked=True
with st.expander('⚙  '+t['settings'],expanded=False):
    currency=st.selectbox(t['currency'],['USD','GEL'],key='currency')
    unit_price=st.number_input(t['film_rate'],min_value=0.0,value=150.0,step=1.0,key='film_price')
    installation_rate=st.number_input(t['install_rate'],min_value=0.0,value=30.0,step=1.0,key='installation_price')
    install_by_glass=st.toggle(t['install_basis'],value=False,key='install_by_glass')
    usd_rate=st.number_input(t['exchange'],min_value=0.01,step=0.01,format='%.4f',key='usd_rate')
    if st.session_state.nbg_error:st.warning(t['nbg_fail'])
    else:st.caption(t['nbg']+' · '+st.session_state.nbg_date)
    if st.button(t['refresh'],use_container_width=True):
        fetch_nbg_rate.clear()
        try:
            rate,dt=fetch_nbg_rate();st.session_state.usd_rate=rate;st.session_state.nbg_date=dt;st.session_state.nbg_error=False
        except Exception:st.session_state.nbg_error=True
        st.rerun()
with st.expander('👤  '+t['customer'],expanded=False):
    customer_first=st.text_input(t['first'],key='customer_first')
    customer_last=st.text_input(t['last'],key='customer_last')
    customer_phone=st.text_input(t['phone'],key='customer_phone')
    customer_address=st.text_input(t['address'],key='customer_address')
    order_date=st.date_input(t['date'],value=date.today(),key='order_date')
st.markdown('<div class="sectionline">'+escape(t['glass'])+'</div>',unsafe_allow_html=True)
a,b=st.columns(2)
if a.button(t['all_on'],use_container_width=True):
    for pane in st.session_state.panes:
        pane['rotate']=True;st.session_state[f"rotate_{pane['id']}"]=True
    st.rerun()
if b.button(t['all_off'],use_container_width=True):
    for pane in st.session_state.panes:
        pane['rotate']=False;st.session_state[f"rotate_{pane['id']}"]=False
    st.rerun()
st.caption(t['rotate_note'])
for index,pane in enumerate(st.session_state.panes):
    pid=pane['id']
    with st.container(border=True):
        title,trash=st.columns([5,1],vertical_alignment='center')
        title.markdown(f'**{t["pane"]} #{index+1}**')
        if trash.button('🗑️',key=f'delete_{pid}',help=t['remove']):
            st.session_state.panes=[p for p in st.session_state.panes if p['id']!=pid]
            for prefix in ('w','h','q','rotate'):st.session_state.pop(f'{prefix}_{pid}',None)
            st.rerun()
        x,y=st.columns(2)
        x.number_input(t['width'],min_value=0.0,value=None,step=1.0,placeholder=t['required'],key=f'w_{pid}')
        y.number_input(t['height'],min_value=0.0,value=None,step=1.0,placeholder=t['required'],key=f'h_{pid}')
        qty,rot=st.columns([1,2],vertical_alignment='bottom')
        qty.number_input(t['quantity'],min_value=1,max_value=100,value=1,step=1,key=f'q_{pid}')
        pane['rotate']=rot.toggle(t['rotate'],value=pane['rotate'],key=f'rotate_{pid}')
if st.button(t['add'],type='primary',use_container_width=True):
    st.session_state.panes.append(new_pane());st.rerun()
pieces=[];incomplete=False
for index,pane in enumerate(st.session_state.panes):
    pid=pane['id'];w,h=st.session_state.get(f'w_{pid}'),st.session_state.get(f'h_{pid}')
    if w is None or h is None or w<=0 or h<=0:
        incomplete=True;continue
    for n in range(st.session_state.get(f'q_{pid}',1)):
        pieces.append({'width':float(w),'height':float(h),'rotate':pane['rotate'],'label':f'{index+1}.{n+1}'})

def pack(order):
    shelves,positions=[],[]
    for piece in order:
        orientations=[(piece['width'],piece['height'],False)]
        if (piece['rotate'] or piece['width']>ROLL_WIDTH) and piece['width']!=piece['height']:
            orientations.append((piece['height'],piece['width'],True))
        best=None
        for w,h,rotated in orientations:
            if w>ROLL_WIDTH+1e-8:continue
            for j,shelf in enumerate(shelves):
                if w<=ROLL_WIDTH-shelf['used']+1e-8 and h<=shelf['height']+1e-8:
                    score=(0,shelf['height']-h,ROLL_WIDTH-shelf['used']-w)
                    if best is None or score<best[0]:best=(score,j,w,h,rotated)
            score=(1,h,ROLL_WIDTH-w)
            if best is None or score<best[0]:best=(score,None,w,h,rotated)
        if best is None:return None
        _,j,w,h,rotated=best
        if j is None:
            yy=sum(s['height'] for s in shelves)
            shelves.append({'used':w,'height':h,'y':yy});xx=0.0
        else:
            shelf=shelves[j];xx,yy=shelf['used'],shelf['y'];shelf['used']+=w
        positions.append((xx,yy,w,h,piece['label'],rotated))
    return sum(s['height'] for s in shelves),positions,shelves

if not st.session_state.panes:st.info(t['empty'])
elif incomplete:st.info(t['fill'])
else:
    orders=[sorted(pieces,key=lambda p:p['width']*p['height'],reverse=True),sorted(pieces,key=lambda p:max(p['width'],p['height']),reverse=True),sorted(pieces,key=lambda p:min(p['width'],p['height']),reverse=True),sorted(pieces,key=lambda p:p['height'],reverse=True)]
    results=[r for order in orders if (r:=pack(order)) is not None]
    if not results:st.error(t['invalid'])
    else:
        length,positions,shelves=min(results,key=lambda r:r[0])
        film_area=ROLL_WIDTH*length/10000
        glass_area=sum(p['width']*p['height'] for p in pieces)/10000
        waste=max(0.0,film_area-glass_area)
        film_total=film_area*unit_price
        installation_area=glass_area if install_by_glass else film_area
        install_total=installation_area*installation_rate
        grand=film_total+install_total
        grand_gel=grand if currency=='GEL' else grand*usd_rate
        grand_usd=grand/usd_rate if currency=='GEL' else grand
        symbol='₾' if currency=='GEL' else '$'
        st.markdown('<div class="sectionline">'+escape(t['results'])+'</div>',unsafe_allow_html=True)
        a,b=st.columns(2);a.metric(t['film_area'],f'{film_area:.3f} {t["units"]}');b.metric(t['glass_area'],f'{glass_area:.3f} {t["units"]}')
        a,b=st.columns(2);a.metric(t['film_cost'],f'{film_total:,.2f} {symbol}');b.metric(t['install_cost'],f'{install_total:,.2f} {symbol}')
        st.metric(t['grand'],f'{grand:,.2f} {symbol}')
        a,b=st.columns(2);a.caption(f'USD: ${grand_usd:,.2f} · GEL: ₾{grand_gel:,.2f}');b.caption(f'{t["count"]}: {len(pieces)} · {t["waste"]}: {waste:.3f} {t["units"]}')
        st.markdown('<div class="sectionline">'+escape(t['cut'])+'</div>',unsafe_allow_html=True)
        st.caption(f'{t["length"]}: {length:.1f} cm · 150 cm')
        svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 {length+25:.2f}" style="width:100%;max-height:850px;background:#f7f5ff">']
        svg.append(f'<rect x="10" y="5" width="150" height="{length:.2f}" fill="#e9e0bc" stroke="#a9925c"/>')
        colors=['#6652c9','#377bbd','#8a56b4','#367f82','#aa618d']
        for i,(x,y,w,h,label,rotated) in enumerate(positions):
            svg.append(f'<rect x="{x+10:.2f}" y="{y+5:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{colors[i%len(colors)]}" stroke="white" stroke-width="0.8"/>')
            if w>=22 and h>=16:svg.append(f'<text x="{x+10+w/2:.2f}" y="{y+5+h/2:.2f}" fill="white" font-size="7" text-anchor="middle">{w:g}×{h:g}</text>')
        svg.append(f'<text x="85" y="{length+18:.2f}" fill="#393053" font-size="9" text-anchor="middle">150 cm</text></svg>')
        height_px=max(110,min(900,int(length*min(3,850/max(length,1))+40)))
        st.components.v1.html(''.join(svg),height=height_px,scrolling=True)
        st.caption(t['cut_note'])
        output=io.StringIO(newline='');writer=csv.writer(output)
        writer.writerow(['GlassX — '+t['order']])
        for label,value in [(t['first'],customer_first),(t['last'],customer_last),(t['phone'],customer_phone),(t['address'],customer_address),(t['date'],order_date.isoformat())]:writer.writerow([label,value])
        writer.writerow([]);writer.writerow([t['pane'],t['width'],t['height'],t['quantity'],t['glass_area']])
        for i,pane in enumerate(st.session_state.panes,1):
            pid=pane['id'];w,h,q=float(st.session_state[f'w_{pid}']),float(st.session_state[f'h_{pid}']),int(st.session_state[f'q_{pid}'])
            writer.writerow([i,w,h,q,round(w*h*q/10000,4)])
        writer.writerow([])
        rows=[(t['glass_area'],round(glass_area,3)),(t['film_area'],round(film_area,3)),(t['film_rate'],round(unit_price,2)),(t['install_rate'],round(installation_rate,2)),(t['install_basis'],t['glass_area'] if install_by_glass else t['film_area']),(t['install_cost'],round(install_total,2)),(t['film_cost'],round(film_total,2)),(t['grand'],round(grand,2)),(t['currency'],currency),(t['exchange'],round(usd_rate,4)),('Total USD',round(grand_usd,2)),('Total GEL',round(grand_gel,2))]
        for label,value in rows:writer.writerow([label,value])
        safe_name='_'.join((customer_first+' '+customer_last).split())
        safe_name=''.join(ch for ch in safe_name if ch.isalnum() or ch in '_-')[:55]
        filename=f'GlassX_{safe_name+"_" if safe_name else ""}{order_date.isoformat()}.csv'
        st.download_button(t['download'],data=('\ufeff'+output.getvalue()).encode('utf-8'),file_name=filename,mime='text/csv',use_container_width=True,type='primary')
        st.caption(t['download_note'])
