from sqlalchemy import Column, String, Integer, ForeignKey, BigInteger, REAL
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class QRCode(Base):
    __tablename__ = "qrcode"
    
    id = Column(BigInteger, primary_key=True)
    uuid = Column(String, nullable=False)


class Role(Base):
    __tablename__ = "role"
    
    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    
    
class User(Base):
    __tablename__ = "user"
    
    id = Column(BigInteger, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    login = Column(String, nullable=False)
    password = Column(String, nullable=False)
    role_id = Column(BigInteger, ForeignKey("role.id"), nullable=False)
    

class Customer(Base):
    __tablename__ = "customer"
    
    id = Column(BigInteger, primary_key=True)
    phone = Column(String(11), nullable=False)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)


class Employee(Base):
    __tablename__ = "employee"
    
    id = Column(BigInteger, primary_key=True)
    salary = Column(REAL, nullable=False)
    order_count = Column(Integer, nullable=False)
    user_id = Column(BigInteger, ForeignKey("user.id"), nullable=False)

    
class Item(Base):
    __tablename__ = "item"
    
    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    price = Column(Integer, nullable=False)


class Order(Base):
    __tablename__ = "order"
    
    id = Column(BigInteger, primary_key=True)
    total_price = Column(Integer, nullable=False)
    customer_id = Column(BigInteger, ForeignKey("customer.id"))
    qrcode_id = Column(BigInteger, ForeignKey("qrcode.id"))
    employee_id = Column(Integer, ForeignKey("employee.id"), nullable=False)
    

class OrderItem(Base):
    __tablename__ = "order-item"
    
    id = Column(BigInteger, primary_key=True)
    order_id = Column(BigInteger, ForeignKey("order.id"), nullable=False)
    item_id = Column(BigInteger, ForeignKey("item.id"), nullable=False)