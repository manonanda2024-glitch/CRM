# Manonanda Solar Energy CRM

Streamlit warehouse tracker for receiving and sending solar inventory. Starts with an empty database; no demo records are mixed with real stock.

## Run locally

```powershell
python -m pip install -r requirements.txt
$env:APP_PASSWORD = 'choose-a-private-password'
python -m streamlit run app.py
```

Open http://localhost:8501. Local data lives in `data/solar.db`. Without APP_PASSWORD, local development does not require login.

**Warehouse stock** shows quantities received and still in the warehouse. It updates when you save a stock change or reopen the page.

## Deploy Streamlit with Render PostgreSQL

1. Create or select a Render PostgreSQL database in Singapore, the region configured for the web service in `render.yaml`.
2. Push the application files to GitHub, then connect that repository to a new Render Blueprint. In the app's Environment settings, set `DATABASE_URL` to the database's **Internal Database URL**. Render generates `APP_PASSWORD` for the app.
3. To copy existing records, run the import locally before adding any records through the hosted app. Paste the database's **External Database URL** into the hidden prompt. If external access is restricted, allow your IP for the import and remove that entry after it completes.

   ```powershell
   python -m pip install -r requirements.txt
   $env:PGSSLMODE = 'require'
   python migrate_to_postgres.py --source data/solar.db
   Remove-Item Env:PGSSLMODE
   ```

4. Check the printed counts against the local records. Open the Render web service URL, sign in with `APP_PASSWORD`, and check **Warehouse stock** and **Sent to**.

Migration copies products, balances, contacts, projects and shipment history in one transaction and preserves record IDs. It requires an empty destination. The local SQLite file stays available as a copy of the pre-migration records.

Render Free PostgreSQL expires after 30 days and has no managed backups. Export your database or upgrade before it expires if you need to continue using the records. Render's free web service can take about a minute to wake after idling. [Render free tier limits](https://render.com/docs/free) · [Render PostgreSQL connections](https://render.com/docs/postgresql-creating-connecting)

## Workflow

1. Open **Add product**. Enter its name, category, how you count it, and how many came in. Saving also records the first delivery.
2. For later deliveries, open **Receive stock**, select the existing product, and enter the quantity.
3. When stock leaves, open **Send stock** and enter the quantity and the customer or job site. The destination appears under **Sent to**.
4. On **Warehouse stock**, use **Correct a product name** to fix a typo, or **Delete** next to a mistaken product. Deleting requires confirmation and removes its first delivery, if present. Products with later stock activity can only be renamed.

In pgAdmin, open **Schemas → public → Views → warehouse_products** for a stock list with just the product, category, quantity in stock, and unit.

Quantities use the product's chosen unit. The app blocks sending more stock than the warehouse has. Ledger timestamps are in UTC. Use `pg_dump` for hosted database backups and SQLite's backup API for local backups.

## Checks

```powershell
python -m unittest discover -s tests
```

