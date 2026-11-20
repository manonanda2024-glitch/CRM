import hashlib
import hmac
import os
import re
from collections import Counter
from uuid import uuid4
import pandas as pd
import streamlit as st
import database as db

st.set_page_config(page_title='Manonanda Solar Energy', page_icon='☀️', layout='wide')
st.markdown('''<style>
.stApp {background:linear-gradient(160deg,#eaf3ef 0,#f6f8f7 22rem);color:#18332e;}
[data-testid="stHeader"] {background:transparent;}
[data-testid="stMainBlockContainer"] {padding-top:3.75rem;max-width:94rem;}
[data-testid="stMain"]:has(.st-key-page-intro-overview) {
    background-color:#f6f8f7;
    background-image:radial-gradient(ellipse at 18% 12%,#cce9db 0,transparent 52%),
                     radial-gradient(ellipse at 86% 32%,#dcece7 0,transparent 50%);
    background-size:140% 135%,155% 145%;
    background-position:0% 0%,100% 0%;
    background-repeat:no-repeat;
}
[data-testid="stSidebar"] {background:#102b25;}
[data-testid="stSidebar"] :is(h1,p,label,span,button) {color:#edf7f3;}
[data-testid="stSidebar"] [role="radiogroup"] {gap:.3rem;}
[data-testid="stSidebar"] [role="radiogroup"] label {
    min-height:2.65rem;padding:.5rem .65rem;border-radius:.55rem;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover,
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background:#235347;}
[data-testid="stSidebar"] [role="radiogroup"] input:focus-visible + div {
    outline:2px solid #a3e6ca;outline-offset:3px;
}
[data-testid="stMain"] :is(h1,h2,h3) {color:#16382f;letter-spacing:-.025em;}
[data-testid="stMain"] h1 {font-size:clamp(2.25rem,4vw,3.5rem);line-height:1.08;}
[data-testid="stMain"] h3 {font-size:1.2rem;}
.st-key-page-intro-overview {position:relative;min-height:6.4rem;padding-right:8rem;}
.st-key-page-intro-overview > [data-testid="stElementContainer"]:has(.warehouse-robot) {position:static;}
.warehouse-robot {
    position:absolute;right:1.3rem;top:0;width:6.3rem;height:5.8rem;
    pointer-events:none;
}
.warehouse-robot__shadow {
    position:absolute;bottom:.2rem;left:1.05rem;width:4.3rem;height:.55rem;
    border-radius:50%;background:#145b4529;
}
.warehouse-robot__body {position:absolute;inset:0;}
.warehouse-robot__face {
    position:absolute;left:.4rem;right:.4rem;bottom:1.05rem;height:3.3rem;
    display:flex;align-items:center;justify-content:center;gap:.6rem;
    border:3px solid #195f4c;border-radius:1.1rem;
    background:linear-gradient(155deg,#fcfffd,#bce9d8);
    box-shadow:inset 0 -.32rem #8ccdb8,0 .24rem .55rem #16473920;
}
.warehouse-robot__eye {width:.42rem;height:.63rem;border-radius:1rem;background:#174639;}
.warehouse-robot__smile {
    position:absolute;bottom:.53rem;left:50%;height:.32rem;width:.65rem;
    transform:translateX(-50%);border-bottom:2px solid #174639;border-radius:0 0 1rem 1rem;
}
.warehouse-robot__panel {
    position:absolute;top:.15rem;left:1.78rem;width:2.75rem;height:1.28rem;
    border:2px solid #195f4c;border-radius:.27rem;transform:rotate(-10deg);
    background:linear-gradient(90deg,transparent 47%,#a5dbc8 48% 53%,transparent 54%),
               linear-gradient(transparent 46%,#a5dbc8 47% 55%,transparent 56%),#226e69;
}
.warehouse-robot__sun {
    position:absolute;right:0;top:.16rem;width:.67rem;height:.67rem;border-radius:50%;
    background:#ffbf4f;box-shadow:0 0 0 .21rem #ffc96043;
}
@media (max-width:520px) {
    .st-key-page-intro-overview {padding-right:5.1rem;}
    .warehouse-robot {right:0;transform:scale(.72);transform-origin:top right;}
}
[data-testid="stForm"] {
    max-width:42rem;background:#fff;padding:clamp(1rem,3vw,1.75rem);
    border:1px solid #dbe7e2;border-radius:1rem;box-shadow:0 6px 24px #153b2e0a;
}
[data-testid="stDataFrame"] {border-radius:.65rem;overflow:hidden;}
button[kind="primary"],button[kind="primaryFormSubmit"] {
    background:#126550;border-color:#126550;color:white;min-height:2.75rem;
}
button[kind="primary"]:hover,button[kind="primaryFormSubmit"]:hover {background:#0d503f;border-color:#0d503f;}
@media (prefers-reduced-motion: no-preference) {
    [data-testid="stMain"]:has(.st-key-page-intro-overview) {
        animation:warehouse-background 18s ease-in-out infinite alternate;
    }
    .warehouse-robot__body {animation:robot-hover 3.4s ease-in-out infinite;}
    .warehouse-robot__eye {animation:robot-blink 6.2s ease-in-out infinite;}
    [class*="st-key-page-intro-"] {animation:page-enter 240ms ease-out both;}
    [data-testid="stForm"] {animation:form-enter 320ms cubic-bezier(.2,.7,.3,1) both;}
    .st-key-save-confirmation {animation:confirm-enter 320ms cubic-bezier(.2,.7,.3,1) both;}
    [data-testid="stSidebar"] [role="radiogroup"] label {
        transition:background-color 160ms ease;
    }
    button[kind="primary"],button[kind="primaryFormSubmit"] {
        transition:background-color 150ms ease,box-shadow 150ms ease,transform 150ms ease;
    }
    button[kind="primary"]:hover,button[kind="primaryFormSubmit"]:hover {
        transform:translateY(-1px);box-shadow:0 4px 10px #12655030;
    }
    button[kind="primary"]:active,button[kind="primaryFormSubmit"]:active {
        transform:translateY(1px);box-shadow:none;
    }
}
@keyframes warehouse-background {
    from {background-position:0% 0%,100% 0%;}
    to {background-position:100% 60%,0% 75%;}
}
@keyframes robot-hover {
    0%,100% {transform:translateY(0) rotate(-2deg);}
    50% {transform:translateY(-6px) rotate(2deg);}
}
@keyframes robot-blink {
    0%,45%,51%,100% {transform:scaleY(1);}
    48% {transform:scaleY(.12);}
}
@keyframes page-enter {
    from {opacity:0;transform:translateY(6px);}
    to {opacity:1;transform:translateY(0);}
}
@keyframes form-enter {
    from {opacity:0;transform:translateY(10px);}
    to {opacity:1;transform:translateY(0);}
}
@keyframes confirm-enter {
    from {opacity:0;transform:translateY(-5px);}
    to {opacity:1;transform:translateY(0);}
}
</style>''', unsafe_allow_html=True)

password = os.environ.get('APP_PASSWORD')
if password and not st.session_state.get('authenticated'):
    st.title('☀️ Manonanda Solar Energy')
    with st.form('login'):
        entered = st.text_input('Team password', type='password')
        if st.form_submit_button('Sign in', type='primary'):
            if hmac.compare_digest(hashlib.sha256(entered.encode()).digest(), hashlib.sha256(password.encode()).digest()):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error('Incorrect password.')
    st.stop()
if os.environ.get('RENDER') and not password:
    st.error('Set APP_PASSWORD in Render environment settings before using this service.')
    st.stop()
if os.environ.get('RENDER') and not db.DATABASE_URL:
    st.error('Set DATABASE_URL to the PostgreSQL connection URL in Render environment settings.')
    st.stop()


@st.cache_resource
def initialize_local_database():
    db.init()


if db.DATABASE_URL:
    db.init()
else:
    initialize_local_database()
st.sidebar.title('☀️ MANONANDA')
st.sidebar.caption('SOLAR ENERGY · OPERATIONS')
pages = {
    'Overview': 'Warehouse stock',
    'Inventory': 'Add product',
    'Receipt': 'Receive stock',
    'Issue': 'Send stock',
    'Destinations': 'Sent to',
}
page = st.sidebar.radio('Menu', list(pages), format_func=pages.get)
st.sidebar.divider()
if password and st.sidebar.button('Sign out'):
    st.session_state.clear()
    st.rerun()
if not password:
    st.sidebar.caption('Local demo')
with st.container(key=f'page-intro-{page.lower()}'):
    st.title(pages[page])
    if page == 'Overview':
        st.html('''
            <div class="warehouse-robot" aria-hidden="true">
                <div class="warehouse-robot__shadow"></div>
                <div class="warehouse-robot__sun"></div>
                <div class="warehouse-robot__body">
                    <div class="warehouse-robot__panel"></div>
                    <div class="warehouse-robot__face">
                        <span class="warehouse-robot__eye"></span>
                        <span class="warehouse-robot__eye"></span>
                        <span class="warehouse-robot__smile"></span>
                    </div>
                </div>
            </div>
        ''')
if saved_message := st.session_state.pop('record_saved', None):
    with st.container(key='save-confirmation'):
        st.success(saved_message)

def table(data):
    if data:
        frame = pd.DataFrame(data)
        if 'Unit' in frame:
            frame['Unit'] = frame['Unit'].replace('Nos', 'Pieces')
        if 'Time (UTC)' in frame:
            india_time = pd.to_datetime(frame.pop('Time (UTC)'), utc=True).dt.tz_convert('Asia/Kolkata')
            frame['Time (IST)'] = india_time.dt.strftime('%Y-%m-%d %I:%M:%S %p')
        st.dataframe(frame, hide_index=True, width='stretch')
    else:
        st.info('No records yet. Add your first record to get started.')


@st.fragment(run_every=5)
def inventory_dashboard():
    products, _, _, _ = db.inventory_snapshot()
    groups = [
        ('Panels', [p for p in products if p['category'] == 'Panels']),
        ('Inverters', [p for p in products if p['category'] == 'Inverters']),
        ('Other products', [p for p in products if p['category'] not in ('Panels', 'Inverters')]),
    ]
    if not products:
        st.info('Go to Add product to get started.')
    for heading, group in groups:
        if group:
            st.subheader(heading)
            table([
                {'Product': p['name'], 'In stock': p['stock'], 'Received': p['stock_in'], 'Unit': p['unit']}
                for p in group
            ])


@st.fragment(run_every=5)
def sent_to():
    shipments = db.dispatch_history()
    if shipments:
        table([
            {column: shipment[column] for column in ('Sent to', 'Product', 'Quantity', 'Unit', 'Time (UTC)')}
            for shipment in shipments
        ])
    else:
        st.info('Stock sent to a customer or job site will appear here.')


if page == 'Overview':
    inventory_dashboard()

elif page == 'Inventory':
    with st.form('product', clear_on_submit=True):
        name = st.text_input('Product name *', placeholder='For example, Waaree TOPCon panel')
        category = st.selectbox('Category', list(db.CATEGORIES))
        unit = st.selectbox('Count in', ['Nos', 'Metres', 'Sets', 'Kg', 'Rolls', 'Bundles'],
                           format_func=lambda unit: 'Pieces' if unit == 'Nos' else unit)
        quantity = st.number_input('How many came in? *', min_value=0.01, value=None, placeholder='Enter quantity')
        if st.form_submit_button('Add product', type='primary'):
            if not name.strip():
                st.error('Enter the product name.')
            elif quantity is None:
                st.error('Enter how many came in.')
            else:
                prefix = {'Panels': 'PNL', 'Inverters': 'INV'}.get(category, 'ITEM')
                name_code = re.sub(r'[\W_]+', '-', name.strip().upper()).strip('-')[:32].rstrip('-') or 'PRODUCT'
                sku = f'{prefix}-{name_code}-{uuid4().hex[:12].upper()}'
                try:
                    db.add_product(sku, name.strip(), category, unit, quantity)
                except db.IntegrityError:
                    st.error('Could not add the product. Try again.')
                else:
                    st.session_state.record_saved = f'Product added with {quantity:g} in stock.'
                    st.rerun()

elif page == 'Destinations':
    sent_to()

elif page in ('Receipt', 'Issue'):
    sending = page == 'Issue'
    products = db.rows('SELECT id,sku,name,unit,stock FROM products ORDER BY name,sku')
    if not products:
        st.info('Go to Add product first.')
    else:
        labels = {p['id']: p['name'] for p in products}
        label_counts = Counter(labels.values())
        for p in products:
            if label_counts[labels[p['id']]] > 1:
                labels[p['id']] += f" · {p['sku']}"
        product_id = st.selectbox('Product', list(labels), format_func=labels.get)
        product = next(p for p in products if p['id'] == product_id)
        unit = 'pieces' if product['unit'] == 'Nos' else product['unit'].lower()
        st.caption(f"In stock: {product['stock']:g} {unit}")
        with st.form(f'movement-{page}', clear_on_submit=True):
            question = 'How many are going out?' if sending else 'How many came in?'
            quantity = st.number_input(question, min_value=0.01, value=None, placeholder=f'Enter quantity in {unit}')
            destination = st.text_input('Where is it going? *', placeholder='Customer name or job site').strip() if sending else None
            if st.form_submit_button(pages[page], type='primary'):
                if quantity is None:
                    st.error('Enter the quantity.')
                elif sending and not destination:
                    st.error('Enter where the stock is going.')
                else:
                    try:
                        db.move(product_id, page, quantity, 0, None, None, pages[page], '',
                                destination=destination)
                    except (ValueError, db.IntegrityError):
                        st.error('Could not save the stock change. Check how much is in the warehouse.')
                    else:
                        st.session_state.record_saved = f'Stock sent to {destination}.' if sending else 'Stock received.'
                        st.rerun()

