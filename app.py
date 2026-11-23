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
    [class*="st-key-page-intro-"]:not(.st-key-page-intro-overview) {animation:page-enter 240ms ease-out both;}
    .stApp:not(:has(.st-key-page-intro-overview)) {
        & [data-testid="stForm"] {animation:form-enter 320ms cubic-bezier(.2,.7,.3,1) both;}
        & [data-testid="stSidebar"] [role="radiogroup"] label {
            transition:background-color 160ms ease;
        }
        & button:is([kind="primary"],[kind="primaryFormSubmit"]) {
            transition:background-color 150ms ease,box-shadow 150ms ease,transform 150ms ease;
        }
        & button:is([kind="primary"],[kind="primaryFormSubmit"]):hover {
            transform:translateY(-1px);box-shadow:0 4px 10px #12655030;
        }
        & button:is([kind="primary"],[kind="primaryFormSubmit"]):active {
            transform:translateY(1px);box-shadow:none;
        }
    }
}
@keyframes page-enter {
    from {opacity:0;transform:translateY(6px);}
    to {opacity:1;transform:translateY(0);}
}
@keyframes form-enter {
    from {opacity:0;transform:translateY(10px);}
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


@st.cache_resource(ttl=300)
def initialize_database(database_key):
    db.init()


database_key = hashlib.sha256(db.DATABASE_URL.encode()).hexdigest() if db.DATABASE_URL else str(db.DB_PATH)
initialize_database(database_key)
st.sidebar.title('☀️ MANONANDA')
st.sidebar.caption('SOLAR ENERGY · OPERATIONS')
pages = {
    'Overview': 'Warehouse stock',
    'Inventory': 'Add product',
    'Issue': 'Send stock',
    'Destinations': 'Sent to',
}
unit_labels = {'Nos': 'Pieces', 'Metres': 'Meters'}
if st.session_state.pop('return_to_overview', False) or st.session_state.get('menu_page') == 'Receipt':
    st.session_state.menu_page = 'Overview'
page = st.sidebar.radio('Menu', list(pages), format_func=pages.get, key='menu_page')
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
    st.success(saved_message)


def show_saved_stock(message):
    st.session_state.record_saved = message
    st.session_state.return_to_overview = True
    st.rerun()

def table(data):
    if data:
        frame = pd.DataFrame(data)
        if 'Unit' in frame:
            frame['Unit'] = frame['Unit'].replace(unit_labels)
        if 'Time (UTC)' in frame:
            india_time = pd.to_datetime(frame.pop('Time (UTC)'), utc=True).dt.tz_convert('Asia/Kolkata')
            frame['Time (IST)'] = india_time.dt.strftime('%Y-%m-%d %I:%M:%S %p')
        st.dataframe(frame, hide_index=True, width='stretch')
    else:
        st.info('No records yet. Add your first record to get started.')


@st.dialog('Delete product')
def confirm_product_deletion(product):
    st.text(product['name'])
    st.caption('Deleting also removes the first delivery. Products with later stock activity can only be renamed.')
    confirmed = st.checkbox('Delete this product and its first delivery')
    if st.button('Delete product', type='primary', disabled=not confirmed):
        try:
            db.delete_mistaken_product(product['id'], product['sku'])
        except ValueError as exc:
            st.error(str(exc))
        except db.IntegrityError:
            st.error('This product is still linked to stock history.')
        else:
            show_saved_stock('Mistaken product deleted.')


def inventory_dashboard():
    products = db.overview_products()
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
            widths = [3, 2, 2, 1.4]
            with st.container(border=True):
                headers = st.columns(widths)
                for column, label in zip(headers, ('Product', 'In stock', 'Received')):
                    column.markdown(f'**{label}**')
                for product in group:
                    name, stock, received, action = st.columns(widths, vertical_alignment='center')
                    unit = unit_labels.get(product['unit'], product['unit'])
                    name.text(product['name'])
                    stock.text(f"{product['stock']:g} {unit}")
                    received.text(f"{product['stock_in']:g} {unit}")
                    if action.button('Delete', key=f"delete-product-{product['id']}",
                                     help=f"Delete {product['name']}"):
                        confirm_product_deletion(product)


def sent_to():
    shipments = db.dispatch_history()
    if shipments:
        table([
            {column: shipment[column] for column in ('Sent to', 'Product', 'Quantity', 'Unit', 'Time (UTC)')}
            for shipment in shipments
        ])
    else:
        st.info('Stock sent to a customer or job site will appear here.')


def correct_product():
    products = db.rows('SELECT id,sku,name,stock FROM products ORDER BY name,sku')
    if not products:
        st.info('There are no products to correct.')
    else:
        options = {p['id']: p for p in products}
        product_id = st.selectbox('Product', list(options),
                                  format_func=lambda pid: f"{options[pid]['name']} · {options[pid]['sku']}")
        product = options[product_id]
        with st.form(f'rename-{product_id}'):
            name = st.text_input('Correct product name', value=product['name']).strip()
            if st.form_submit_button('Save name', type='primary'):
                if not name:
                    st.error('Enter the product name.')
                elif not db.rows('UPDATE products SET name=? WHERE id=? AND sku=? RETURNING id',
                                 (name, product_id, product['sku'])):
                    st.error('That product no longer exists.')
                else:
                    show_saved_stock('Product name updated.')
if page == 'Overview':
    with st.expander('Correct a product name', key='stock-corrections', on_change='rerun') as corrections:
        if corrections.open:
            correct_product()
    inventory_dashboard()

elif page == 'Inventory':
    with st.form('product', clear_on_submit=True):
        name = st.text_input('Product name *', placeholder='For example, Waaree TOPCon panel')
        category = st.selectbox('Category', list(db.CATEGORIES))
        unit = st.selectbox('Count in', ['Nos', 'Metres', 'Sets', 'Kg', 'Rolls', 'Bundles'],
                           format_func=lambda unit: unit_labels.get(unit, unit))
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
                    show_saved_stock(f'Product added with {quantity:g} in stock.')

elif page == 'Destinations':
    sent_to()

elif page == 'Issue':
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
        unit = unit_labels.get(product['unit'], product['unit']).lower()
        st.caption(f"In stock: {product['stock']:g} {unit}")
        with st.form(f'movement-{page}', clear_on_submit=True):
            quantity = st.number_input('How many are going out?', min_value=0.01, value=None,
                                       placeholder=f'Enter quantity in {unit}')
            destination = st.text_input('Where is it going? *', placeholder='Customer name or job site').strip()
            if st.form_submit_button(pages[page], type='primary'):
                if quantity is None:
                    st.error('Enter the quantity.')
                elif not destination:
                    st.error('Enter where the stock is going.')
                else:
                    try:
                        db.move(product_id, page, quantity, 0, None, None, pages[page], '',
                                destination=destination)
                    except (ValueError, db.IntegrityError):
                        st.error('Could not save the stock change. Check how much is in the warehouse.')
                    else:
                        show_saved_stock(f'Stock sent to {destination}.')

