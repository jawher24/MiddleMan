import aiosqlite

async def init_db():
    async with aiosqlite.connect("data.db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_id INTEGER,
                seller_id INTEGER,
                amount REAL,
                product TEXT,
                paid INTEGER DEFAULT 0,
                confirmed_by_buyer INTEGER DEFAULT 0,
                confirmed_by_seller INTEGER DEFAULT 0,
                wallet_tx TEXT
            )
        ''')
        await db.commit()

async def create_deal(buyer_id, seller_id, amount):
    async with aiosqlite.connect("data.db") as db:
        await db.execute("INSERT INTO deals (buyer_id, seller_id, amount) VALUES (?, ?, ?)", (buyer_id, seller_id, amount))
        await db.commit()

async def get_open_deals():
    async with aiosqlite.connect("data.db") as db:
        cursor = await db.execute("SELECT * FROM deals WHERE paid = 0")
        return await cursor.fetchall()

async def mark_paid(deal_id, tx):
    async with aiosqlite.connect("data.db") as db:
        await db.execute("UPDATE deals SET paid = 1, wallet_tx = ? WHERE id = ?", (tx, deal_id))
        await db.commit()

async def submit_product(deal_id, product):
    async with aiosqlite.connect("data.db") as db:
        await db.execute("UPDATE deals SET product = ? WHERE id = ?", (product, deal_id))
        await db.commit()

async def confirm_buyer(deal_id):
    async with aiosqlite.connect("data.db") as db:
        await db.execute("UPDATE deals SET confirmed_by_buyer = 1 WHERE id = ?", (deal_id,))
        await db.commit()

async def confirm_seller(deal_id):
    async with aiosqlite.connect("data.db") as db:
        await db.execute("UPDATE deals SET confirmed_by_seller = 1 WHERE id = ?", (deal_id,))
        await db.commit()

async def get_deal_by_id(deal_id):
    async with aiosqlite.connect("data.db") as db:
        cursor = await db.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
        return await cursor.fetchone()