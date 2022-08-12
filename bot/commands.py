from json import load

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from sqlalchemy import create_engine

from models import (
    QRCode, 
    Item,
    Order, 
    OrderItem,
    Employee
)

from utils import (
    ItemGetter,
    QRCodeGenerator,
    ReplyGenerator, 
    ItemPaginator,
    SyncOrder,
    language_converter
)


with open('tokens.json', 'r') as f:
    db_token = load(f)["db-token"]
    
engine = create_engine(db_token)

START, MENU, ITEMS, ORDER = range(4)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        session_id = update.message.text.split()[1]
        
        getter = ItemGetter(engine=engine, item_model=QRCode)
        qrcode = getter.get_item(attribute="uuid", value=session_id)
            
        if not qrcode:
            await update.message.reply_text(
                text="Invalid session id."
            )
            return ConversationHandler.END
    
    except IndexError:
        await update.message.reply_text(
            text="That don't works this way."
        )
        return ConversationHandler.END
    
    user_data = ctx.user_data
    user_data["qrcode_id"] = qrcode.id
    user_data["total_price"] = 0
    user_data["current_order"] = []
    user_data["reply_generator"] = None
    user_data["item_paginator"] = None
    
    qrcode_generator = QRCodeGenerator(
        engine=engine,
        qrcode_model=QRCode,
        qrcode_id=qrcode.id,
        bot_username="bot_username"
    )
    
    qrcode_generator.make_qrcode()
    qrcode_generator.sync_with_db()
    
    text, reply_markup = ReplyGenerator.start_reply()
    
    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
    
    return START


async def menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = ctx.user_data
    callback_text = update.message.text
    
    if not user_data["reply_generator"]:
        language = language_converter(text=callback_text)
        if language:
            user_data["reply_generator"] = ReplyGenerator(language=language)
            user_data["item_paginator"] = ItemPaginator(engine=engine, item_model=Item, language=language)
        else:
            await update.message.reply_text(
                text="That don't works this way."
            )
            return ConversationHandler.END
    
    reply_generator = user_data["reply_generator"]
    text, reply_markup = reply_generator.menu_reply(condition=len(user_data["current_order"]))
    
    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )

    return MENU


async def items(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:    
    user_data = ctx.user_data
    callback_text = update.message.text
    paginator = user_data["item_paginator"]
    
    paginator.do_action(action=callback_text)

    text, reply_markup = paginator.page_text(), paginator.page()
    
    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )

    return ITEMS


async def item_view(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = ctx.user_data
    reply_generator = user_data["reply_generator"]
    
    getter = ItemGetter(engine=engine, item_model=Item)
    
    item = getter.get_item(attribute="name", value=update.message.text)
    
    if not item:
        await update.message.reply_text(
            text=reply_generator.incorrect_item_reply()
        )
        return

    text, reply_markup = reply_generator.item_view_reply(item=item)

    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )


async def item_view_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = ctx.user_data
    reply_generator = user_data["reply_generator"]
    query = update.callback_query
    
    await query.answer()
    
    getter = ItemGetter(engine=engine, item_model=Item)
    
    item = getter.get_item(attribute="id", value=query.data)
    
    user_data["current_order"].append(item.id)
    user_data["total_price"] += item.price
    
    text = reply_generator.item_view_handler_reply(item_name=item.name)
    
    await query.edit_message_text(
        text=text
    )


async def order_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = ctx.user_data
    reply_generator = user_data["reply_generator"]
    
    for item_id in user_data["current_order"]:
        getter = ItemGetter(engine=engine, item_model=Item)
        item = getter.get_item(attribute="id", value=item_id)
        
        text, reply_markup = reply_generator.order_item_reply(
            item_id=item_id,
            name=item.name,
            price=item.price
        )
        
        await ctx.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup
        )
    
    text, reply_markup = reply_generator.order_reply(user_data["total_price"])
        
    user_data["order_message"] = await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
        
    return ORDER


async def order_list_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = ctx.user_data
    reply_generator = user_data["reply_generator"]
    query = update.callback_query

    await query.answer()

    item_id = query.data
    user_data["current_order"].remove(int(item_id))
    
    getter = ItemGetter(engine=engine, item_model=Item)
    item = getter.get_item(attribute="id", value=item_id)
    
    user_data["total_price"] -= item.price

    query_text, text, reply_markup = reply_generator.order_handler_reply(item_name=item.name, total_price=user_data["total_price"])

    await query.edit_message_text(
        text=query_text
    )

    await user_data["order_message"].delete()
    
    user_data["order_message"] = await ctx.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=reply_markup
    )


async def checkout(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = ctx.user_data
    
    reply_markup = ReplyGenerator.checkout_reply()
    
    if not user_data["current_order"]:
        await update.message.reply_text(
            text="See you next time!",
            reply_markup=reply_markup
        )
        
        user_data.clear()
        
        return ConversationHandler.END
    
    
    sync_order = SyncOrder(
        engine=engine,
        order_model=Order,
        order_item_model=OrderItem,
        employee_model=Employee,
        total_price=user_data["total_price"],
        qrcode_id=user_data["qrcode_id"],
        current_order=user_data["current_order"]
    )
    
    sync_order.commit()
        
    await update.message.reply_text(
        text=f"Thank you for your purchase!\nTotal price: {user_data['total_price']}",
        reply_markup=reply_markup
    )

    user_data.clear()

    return ConversationHandler.END