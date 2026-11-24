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
    'Receipt': 'Receive stock',
    'Issue': 'Send stock',
    'Sources': 'Received from',
    'Destinations': 'Sent to',
}
unit_labels = {'Nos': 'Pieces', 'Metres': 'Meters'}
if st.session_state.pop('return_to_overview', False):
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
    st.caption('Deleting also removes the first delivery. Products with later stock activity cannot be deleted.')
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


@st.dialog('Edit product')
def edit_product_details(product):
    categories = list(dict.fromkeys([*db.CATEGORIES, product['category']]))
    with st.form(f"edit-product-{product['id']}"):
        name = st.text_input('Product name', value=product['name'])
        category = st.selectbox('Category', categories, index=categories.index(product['category']))
        unit = unit_labels.get(product['unit'], product['unit'])
        previous_stock = product['stock_before_receipt']
        stock_before_receipt = st.number_input(
            'Stock before last receipt', value=float(previous_stock) if previous_stock is not None else None,
            help=f'Warehouse balance in {unit} immediately before the latest receipt.',
        )
        received = product['latest_received']
        last_received = st.number_input('Last received', min_value=0.0,
                                        value=float(received) if received is not None else None,
                                        help=f'Latest receipt quantity in {unit}. Changing this updates receipt history.')
        stock = st.number_input('Current stock', min_value=0.0, value=float(product['stock']),
                                help=f'Enter the final warehouse balance in {unit}.')
        if st.form_submit_button('Save changes', type='primary'):
            try:
                db.edit_product(product, name, category, stock, last_received,
                                stock_before_receipt=stock_before_receipt)
            except ValueError as exc:
                st.error(str(exc))
            except db.IntegrityError:
                st.error('Could not save product changes. Try again.')
            else:
                show_saved_stock('Product updated.')


@st.dialog('Merge duplicate products')
def confirm_product_merge(products):
    st.write(products[0]['name'])
    unit = unit_labels.get(products[0]['unit'], products[0]['unit'])
    for product in products:
        st.text(f"{product['sku']} · {product['stock']:g} {unit}")
    st.write(f"Combined stock: {sum(p['stock'] for p in products):g} {unit}")
    st.caption('The oldest product row keeps its SKU. All receipts and dispatches move to that row.')
    confirmed = st.checkbox('These balances represent separate quantities of the same product.')
    if st.button('Merge products', type='primary', disabled=not confirmed):
        try:
            db.merge_duplicate_products(products)
        except ValueError as exc:
            st.error(str(exc))
        except db.IntegrityError:
            st.error('Could not merge these products. No changes were saved.')
        else:
            show_saved_stock('Duplicate rows merged. Stock history was preserved.')


def inventory_dashboard():
    products = db.overview_products()
    if not products:
        st.info('Go to Add product to get started.')
        return
    names = {}
    for product in sorted(products, key=lambda p: db.product_name_key(p['name'])):
        names.setdefault(db.product_name_key(product['name']), product['name'])
    search = st.selectbox('Search warehouse stock', list(names.values()), index=None,
                          key='warehouse-stock-search', accept_new_options=True, filter_mode='contains',
                          placeholder='Product name, category, or SKU',
                          help='Select a suggested product or press Enter to search for your text.')
    duplicates = {}
    for product in products:
        key = (db.product_name_key(product['name']), product['category'], product['unit'])
        duplicates.setdefault(key, []).append(product)
    terms = (search or '').casefold().split()
    products = [
        product for product in products
        if all(term in ' '.join((product['name'], product['category'], product['sku'])).casefold()
               for term in terms)
    ]
    if not products:
        st.info('No products match your search.')
        return
    groups = {}
    for product in products:
        groups.setdefault(product['category'], []).append(product)
    for heading in sorted(groups, key=lambda category: (category not in ('Panels', 'Inverters'),
                                                       category != 'Panels', category.casefold())):
        group = groups[heading]
        if group:
            st.subheader(heading)
            has_duplicates = any(len(duplicates[(db.product_name_key(p['name']), p['category'], p['unit'])]) > 1
                                 for p in group)
            widths = [3, 2.4, 1.8, 1.8, 1, 1.2] + ([1.2] if has_duplicates else [])
            with st.container(border=True):
                headers = st.columns(widths)
                for column, label in zip(headers, ('Product', 'Stock before last receipt', 'Last received', 'Current stock')):
                    column.markdown(f'**{label}**')
                for product in group:
                    name, before, received, stock, edit, delete, *merge = st.columns(widths, vertical_alignment='center')
                    unit = unit_labels.get(product['unit'], product['unit'])
                    name.text(product['name'])
                    previous_stock = product['stock_before_receipt']
                    before.text(f'{previous_stock:g} {unit}' if previous_stock is not None else '—')
                    stock.text(f"{product['stock']:g} {unit}")
                    latest_quantity = product['latest_received']
                    received.text(f'{latest_quantity:g} {unit}' if latest_quantity is not None else '—')
                    if edit.button('Edit', key=f"edit-product-{product['id']}", help=f"Edit {product['name']}"):
                        edit_product_details(product)
                    if delete.button('Delete', key=f"delete-product-{product['id']}",
                                     help=f"Delete {product['name']}"):
                        confirm_product_deletion(product)
                    matches = duplicates[(db.product_name_key(product['name']), product['category'], product['unit'])]
                    if len(matches) > 1 and merge[0].button('Merge', key=f"merge-product-{product['id']}",
                                                            help=f"Merge duplicate rows for {product['name']}"):
                        confirm_product_merge(matches)


def show_movement_history(records, party_column, empty_message):
    if records:
        table([
            {column: row[column] for column in (party_column, 'Product', 'Quantity', 'Unit', 'Time (UTC)')}
            for row in records
        ])
    else:
        st.info(empty_message)


if page == 'Overview':
    inventory_dashboard()

elif page == 'Inventory':
    catalog = db.rows('SELECT name,category,unit FROM products ORDER BY name,sku')
    suggestions = {}
    for product in catalog:
        suggestions.setdefault(db.product_name_key(product['name']), product['name'])
    name = st.selectbox('Product name *', list(suggestions.values()), index=None,
                        accept_new_options=True, filter_mode='contains',
                        placeholder='Search or type a product name',
                        help='Select an existing product or press Enter to use a new name.')
    name_key = db.product_name_key(name or '')
    matching_details = {(p['category'], p['unit']) for p in catalog
                        if db.product_name_key(p['name']) == name_key}
    categories = list(dict.fromkeys([*db.CATEGORIES, *(p['category'] for p in catalog)]))
    units = list(dict.fromkeys(['Nos', 'Metres', 'Sets', 'Kg', 'Rolls', 'Bundles',
                               *(p['unit'] for p in catalog)]))
    default_category, default_unit = categories[0], units[0]
    if len(matching_details) == 1:
        default_category, default_unit = next(iter(matching_details))
    with st.form(f'product-{name_key}', clear_on_submit=True):
        category = st.selectbox('Category', categories, index=categories.index(default_category),
                                key=f'add-product-category-{name_key}')
        unit = st.selectbox('Count in', units, index=units.index(default_unit),
                            key=f'add-product-unit-{name_key}',
                            format_func=lambda unit: unit_labels.get(unit, unit))
        quantity = st.number_input('How many came in? *', min_value=0.01, value=None, placeholder='Enter quantity')
        source = st.text_input('Received from (optional)', placeholder='Supplier or person').strip()
        if st.form_submit_button('Add product', type='primary'):
            if not name_key:
                st.error('Enter the product name.')
            elif quantity is None:
                st.error('Enter how many came in.')
            else:
                prefix = {'Panels': 'PNL', 'Inverters': 'INV'}.get(category, 'ITEM')
                name_code = re.sub(r'[\W_]+', '-', name.strip().upper()).strip('-')[:32].rstrip('-') or 'PRODUCT'
                sku = f'{prefix}-{name_code}-{uuid4().hex[:12].upper()}'
                try:
                    created = db.add_product(sku, name, category, unit, quantity, source=source or None)
                except ValueError as exc:
                    st.error(str(exc))
                except db.IntegrityError:
                    st.error('Could not add the product. Try again.')
                else:
                    message = (f'Product added with {quantity:g} in stock.' if created
                               else f'Added {quantity:g} to existing stock.')
                    show_saved_stock(message)

elif page == 'Sources':
    show_movement_history(db.receipt_history(), 'Received from', 'Stock receipts will appear here.')

elif page == 'Destinations':
    show_movement_history(db.dispatch_history(), 'Sent to', 'Stock sent to a customer or job site will appear here.')

elif page in ('Receipt', 'Issue'):
    receiving = page == 'Receipt'
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
            question = 'How many came in?' if receiving else 'How many are going out?'
            quantity = st.number_input(question, min_value=0.01, value=None,
                                       placeholder=f'Enter quantity in {unit}')
            if receiving:
                source = st.text_input('Received from *', placeholder='Supplier or person').strip()
                destination = None
            else:
                source = None
                destination = st.text_input('Where is it going? *', placeholder='Customer name or job site').strip()
            if st.form_submit_button(pages[page], type='primary'):
                if quantity is None:
                    st.error('Enter the quantity.')
                elif not (source or destination):
                    st.error('Enter who sent the stock.' if receiving else 'Enter where the stock is going.')
                else:
                    try:
                        db.move(product_id, page, quantity, 0, None, None, pages[page], '',
                                destination=destination, source=source)
                    except ValueError as exc:
                        st.error(str(exc))
                    except db.IntegrityError:
                        st.error('Could not save the stock change. Reopen the page and try again.')
                    else:
                        message = f'Stock received from {source}.' if receiving else f'Stock sent to {destination}.'
                        show_saved_stock(message)

