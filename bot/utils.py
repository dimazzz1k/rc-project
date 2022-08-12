from sqlalchemy.orm import Session, Query
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
import qrcode
from uuid import uuid4
from math import ceil
from typing import Tuple


class ItemPaginator:
    def __init__(self, engine, item_model, language: str) -> None:
        self._engine = engine
        self._item_model = item_model
        self._items_on_page: int = 9
        self._items: list = self._get_items()
        self._current_page: int = 1
        self._pages: int = self._count_pages()
        self._language: str = language
    
    @property
    def current_page(self) -> int:
        return self._current_page
    
    @current_page.setter
    def current_page(self, value: int) -> None:
        if value > self._pages:
            raise IndexError("Page out of index.")
        elif value < 1:
            raise IndexError("Page out of index.")
        self._current_page = value
    
    @property
    def pages(self) -> int:
        return self._pages
    
    def _get_items(self) -> list:
        with Session(self._engine) as session:
            query = session.query(self._item_model)
            return query.all()    

    def _count_pages(self) -> int:
        items_count = len(self._items)
        pages = ceil(items_count / self._items_on_page)
        return pages
    
    def _get_min_page_range(self) -> int:
        min_range = (self._current_page - 1) * self._items_on_page
        return min_range
    
    def _get_max_page_range(self) -> int:
        max_index = len(self._items)
        max_range = self._current_page * self._items_on_page
        
        if max_range > max_index:
            max_range = max_index
        
        return max_range

    def _add_buttons(self) -> list:
        buttons = ["<", "", ">"]
        
        if self._language == "rus":
            buttons[1] = "Обратно в меню"
        elif self._language == "eng":
            buttons[1] = "Back to menu"
            
        return buttons
 
    def page(self) -> ReplyKeyboardMarkup:
        keyboard = [[]]
        
        min_range = self._get_min_page_range()
        max_range = self._get_max_page_range()
        
        x, y = 0, 0
        
        for item in self._items[min_range:max_range]:
            if x > 2:
                x = 0
                y += 1
                keyboard.append([])
            
            keyboard[y].append(item.name)
            x += 1
        
        keyboard.append(self._add_buttons())
        
        return ReplyKeyboardMarkup(keyboard=keyboard)
    
    def page_text(self) -> str:
        if self._language == "rus":
            text = f"Выберите предмет для просмотра.\nТекущая страница: {self._current_page}"
        elif self._language == "eng":
            text = f"Select item to view.\nCurrent page: {self._current_page}"

        return text
    
    def do_action(self, action: str) -> None:
        if action == ">" and self._current_page != self._pages:
            self.next()
        elif action == "<" and self._current_page != 1:
            self.prev()

    def next(self) -> None:
        if self._current_page == self._pages:
            raise IndexError("Page out of index.")
        self._current_page += 1

    def prev(self) -> None:
        if self._current_page == 1:
            raise IndexError("Page out of index.")
        self._current_page -= 1


class ReplyGenerator:
    def __init__(self, language: str):
        self.language = language
        
    @staticmethod
    def start_reply() -> Tuple[str, ReplyKeyboardMarkup]:
        text = "Hello! Select language to continue."
        keyboard = [["English", "Русский"]]
        
        return (text, ReplyKeyboardMarkup(keyboard=keyboard))
    
    def menu_reply(self, condition) -> Tuple[str, ReplyKeyboardMarkup]:
        if self.language == "rus":
            text = "Выберите следующее действие чтобы продолжить."
            
            if not condition:
                keyboard = [
                    ["Предметы для покупки"],
                    ["Выход"]
                ]
            else:
                keyboard = [
                    ["Предметы для покупки"],
                    ["Текущий заказ"],
                    ["Оплатить"]
                ]
            
        elif self.language == "eng":
            text = "Choose next action to proceed."
        
            if not condition:
                keyboard = [
                    ["Items to buy"],
                    ["Exit"]
                ]
            else:
                keyboard = [
                    ["Items to buy"],
                    ["Current order"],
                    ["Checkout"]
                ]
        
        return (text, ReplyKeyboardMarkup(keyboard=keyboard))
    
    def item_view_reply(self, item) -> Tuple[str, InlineKeyboardMarkup]:
        if self.language == "rus":
            text = f"{item.name}\nЦена: {item.price}\nОписание: {item.description}"
            keyboard = [
                [InlineKeyboardButton(text="Добавить в заказ", callback_data=item.id)]
            ]
        elif self.language == "eng":
            text = f"{item.name}\nPrice: {item.price}\nDescription: {item.description}"
            keyboard = [
                [InlineKeyboardButton(text="Add to order", callback_data=item.id)]
            ]
        
        return (text, InlineKeyboardMarkup(inline_keyboard=keyboard))
    
    def item_view_handler_reply(self, item_name) -> str:
        if self.language == "rus":
            text = f"Успешно добавлен(а) {item_name} в заказ."
        elif self.language == "eng":
            text = f"Succesfully added {item_name} to order."
            
        return text
    
    def order_item_reply(self, item_id: int, name: str, price: int) -> Tuple[str, InlineKeyboardMarkup]:
        if self.language == "rus":
            text = f"{name}\nЦена: {price}"
            keyboard = [
                [InlineKeyboardButton(text="Удалить предмет(ы) из заказа", callback_data=item_id)]
            ]
        elif self.language == "eng":
            text = f"{name}\nPrice: {price}"
            keyboard = [
                [InlineKeyboardButton(text="Delete item(s) from order", callback_data=item_id)]
            ]
        
        return (text, InlineKeyboardMarkup(inline_keyboard=keyboard))
    
    def order_reply(self, total_price: int) -> Tuple[str, ReplyKeyboardMarkup]:
        if self.language == "rus":
            text = f"Общая стоимость: {total_price}"
            keyboard = [
                ["Предметы для покупки"],
                ["Оплатить"]
            ]
        elif self.language == "eng":
            text = f"Total price: {total_price}"
            keyboard = [
                ["Items to buy"],
                ["Checkout"]
            ]

        return (text, ReplyKeyboardMarkup(keyboard=keyboard))
    
    def order_handler_reply(self, item_name: str, total_price: int) -> Tuple[str, str, ReplyKeyboardMarkup]:
        if self.language == "rus":
            query_text = f"Успешно удален(а) {item_name} из заказа."
            text = f"Общая стоимость: {total_price}"
            keyboard = [
                ["Предметы для покупки"],
                ["Оплатить"]
            ]
        elif self.language == "eng":
            query_text = f"Succesfully deleted {item_name} from order."
            text = f"Total price: {total_price}"
            keyboard = [
                ["Items to buy"],
                ["Checkout"]
            ]

        return (query_text, text, ReplyKeyboardMarkup(keyboard=keyboard))
    
    @staticmethod
    def checkout_reply() -> ReplyKeyboardMarkup:
        keyboard = [
            [":)"]
        ]
        return ReplyKeyboardMarkup(keyboard=keyboard)
    
    def incorrect_item_reply(self) -> str:
        if self.language == "rus":
            text = "Некорректный предмет."
        elif self.language == "eng":
            text = "Incorrect item."
            
        return text


class ItemGetter:
    def __init__(self, engine, item_model) -> None:
        self._engine = engine
        self._item_model = item_model
        
        self._query = self._get_query()
    
    def _get_query(self) -> Query:
        with Session(self._engine) as session:
            query = session.query(self._item_model)
            return query
        
    def get_query_list(self) -> list:
        return self._query.all()
    
    def get_item(self, attribute: str, value):
        query = self._query
        result = query.filter(self._item_model.__dict__[attribute] == value).one_or_none()
        return result
    
    def get_new_id(self) -> int:
        query = self._query.order_by(self._item_model.id).all()
        
        if not query:
            return 1
        
        last_id = query[-1].id
        return last_id + 1


class SyncOrder:
    def __init__(self,
                 engine,
                 order_model,
                 order_item_model,
                 employee_model,
                 total_price: int,
                 qrcode_id: int,
                 current_order: list
    ) -> None:
        self._engine = engine
        self._order_model = order_model
        self._order_item_model = order_item_model
        self._employee_model = employee_model
        self._total_price = total_price
        self._qrcode_id = qrcode_id
        self._current_order = current_order
        
        self._order = self._make_order()
        self._order_items = self._make_order_items()

    def _make_order(self):
        getter = ItemGetter(engine=self._engine, item_model=self._order_model)
        order_id = getter.get_new_id()
        
        order = self._order_model(
            id=order_id,
            total_price=self._total_price,
            customer_id=None,
            qrcode_id=self._qrcode_id,
            employee_id=self._get_employee_id()
        )
        
        self._increment_employee_orders(employee_id=order.employee_id)
        
        return order
        
    def _get_employee_id(self) -> int:
        getter = ItemGetter(engine=self._engine, item_model=self._employee_model)
        query = getter._query
        query = query.order_by(self._employee_model.order_count).first()
        return query.id
    
    def _increment_employee_orders(self, employee_id) -> None:
        with Session(self._engine) as session:
            query = session.query(self._employee_model).filter(self._employee_model.id == employee_id)
            orders = query.one().order_count
            query.update({"order_count": orders+1}, synchronize_session="fetch")

            session.commit()
    
    def _make_order_items(self) -> list:
        order_items = []
        
        getter = ItemGetter(engine=self._engine, item_model=self._order_item_model)
        order_item_id = getter.get_new_id()
        
        for item_id in self._current_order:
            order_item = self._order_item_model(
                id=order_item_id,
                order_id=self._order.id,
                item_id=item_id
            )
            
            order_items.append(order_item)
            order_item_id += 1
            
        return order_items
    
    def commit(self) -> None:
        with Session(self._engine) as session:
            session.add(self._order)
            session.add_all(self._order_items)
            
            session.commit()


class QRCodeGenerator:
    def __init__(self, engine, qrcode_model, qrcode_id: int, bot_username: str) -> None:
        self._engine = engine
        self._qrcode_model = qrcode_model
        self._qrcode_id: int = qrcode_id
        self._uuid: str = self._get_uuid()
        self._bot_username: str = bot_username
    
    def _get_uuid(self) -> str:
        return uuid4()
    
    def make_qrcode(self) -> None:
        link = f"https://t.me/{self._bot_username}?start={self._uuid}"
        
        img = qrcode.make(link)
        img.save(f".../rc-project-main/web/static/qrcodes/{self._qrcode_id}.png") # здесьЫ путь до папки с qr кодами

    def sync_with_db(self) -> None:
        with Session(self._engine) as session:
            query = session.query(self._qrcode_model).filter(self._qrcode_model.id == self._qrcode_id)
            query.update({"uuid": self._uuid}, synchronize_session="fetch")
            
            session.commit()


def language_converter(text: str) -> str | None:
    if text == "Русский":
        language = "rus"
    elif text == "English":
        language = "eng"
    else:
        language = None
     
    return language