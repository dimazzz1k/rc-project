import logging
from json import load

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)

from commands import (
    START,
    MENU,
    ITEMS, 
    ORDER,
    start,
    menu,
    items,
    order_list,
    order_list_handler,
    item_view,
    item_view_handler,
    checkout
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

with open('tokens.json', 'r') as f:
    bot_token = load(f)["bot-token"]


def main() -> None:
    app = Application.builder().token(bot_token).build()
    
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [
                MessageHandler(filters.Regex("^(English|Русский)$"), menu)
            ],
            MENU: [
                MessageHandler(filters.Regex("^(Items to buy|Предметы для покупки)$"), items),
                MessageHandler(filters.Regex("^(Current order|Текущий заказ)$"), order_list)
            ],
            ITEMS: [
                MessageHandler(filters.Regex("^(Back to menu|Обратно в меню)$"), menu),
                MessageHandler(filters.Regex("^<$"), items),
                MessageHandler(filters.Regex("^>$"), items),
                MessageHandler(filters.TEXT & ~(filters.COMMAND | filters.Regex("^(Exit|Checkout|Выход|Оплатить)$")), item_view),
                CallbackQueryHandler(item_view_handler)
            ],
            ORDER: [
                MessageHandler(filters.Regex("^(Items to buy|Предметы для покупки)$"), items),
                CallbackQueryHandler(order_list_handler)
            ]
        },
        fallbacks=[MessageHandler(filters.Regex("^(Exit|Checkout|Выход|Оплатить)$"), checkout)]
    )
    
    app.add_handler(conversation_handler)
    
    app.run_polling()

    
if __name__ == "__main__":
    main()