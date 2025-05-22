from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import asyncio

import db
import payment
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class DealForm(StatesGroup):
    waiting_for_seller = State()
    waiting_for_amount = State()

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply("Welcome to Escrow Bot! Use /newdeal to start.")

@dp.message_handler(commands=["newdeal"])
async def new_deal(message: types.Message):
    await message.reply("Send the @username of the seller:")
    await DealForm.waiting_for_seller.set()

@dp.message_handler(state=DealForm.waiting_for_seller)
async def get_seller(message: types.Message, state: FSMContext):
    await state.update_data(seller=message.text)
    await message.reply("Now enter the amount in USDT:")
    await DealForm.waiting_for_amount.set()

@dp.message_handler(state=DealForm.waiting_for_amount)
async def get_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    seller_username = data['seller']
    try:
        amount = float(message.text)
        seller = await bot.get_chat(seller_username)
        await db.create_deal(message.from_user.id, seller.id, amount)
        await message.reply(f"Deal created for {amount} USDT. Ask buyer to pay to: \n<code>{config.TRON_WALLET}</code>", parse_mode='HTML')
    except Exception as e:
        await message.reply("Failed to create deal: " + str(e))
    await state.finish()

@dp.message_handler(commands=["submit"])
async def submit_product_handler(message: types.Message):
    args = message.text.split(" ", 2)
    if len(args) < 3:
        await message.reply("Usage: /submit <deal_id> <product_info>")
        return
    await db.submit_product(int(args[1]), args[2])
    await message.reply("Product submitted!")

@dp.message_handler(commands=["confirm"])
async def confirm(message: types.Message):
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Usage: /confirm <deal_id>")
        return
    deal_id = int(args[1])
    deal = await db.get_deal_by_id(deal_id)
    if not deal:
        await message.reply("Deal not found")
        return

    if message.from_user.id == deal[1]:
        await db.confirm_buyer(deal_id)
    elif message.from_user.id == deal[2]:
        await db.confirm_seller(deal_id)
    else:
        await message.reply("You're not part of this deal.")
        return

    deal = await db.get_deal_by_id(deal_id)
    if deal[6] == 1 and deal[7] == 1:
        await message.reply("✅ Deal completed. Releasing payment to seller.")
    else:
        await message.reply("Waiting for other party to confirm.")

async def check_payments_loop():
    while True:
        deals = await db.get_open_deals()
        deal_id, txid = await payment.check_payment(deals)
        if deal_id:
            await db.mark_paid(deal_id, txid)
            await bot.send_message(chat_id=deal_id, text=f"✅ Payment received. Deal ID: {deal_id}")
        await asyncio.sleep(30)

async def on_startup(dispatcher):
    await db.init_db()
    asyncio.create_task(check_payments_loop())

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)
