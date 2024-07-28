from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
import mysql.connector

# Database connection URL using mysql-connector
DATABASE_URL = "mysql+mysqlconnector://root:@localhost/penny_wise"

# Create an engine instance
engine = create_engine(DATABASE_URL, echo=True)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a Session
session = Session()

# Create a base class for declarative class definitions
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)

# Define the Category model
class Category(Base):
    __tablename__ = 'categories'
    category_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

# Define the Expense model
class Expense(Base):
    __tablename__ = 'expenses'
    expense_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.category_id'))
    description = Column(String(255))
    date = Column(Date, nullable=False)

# Create tables
Base.metadata.create_all(engine)

# Example of inserting data
def insert_sample_data():
    new_user = User(username='johndoe', email='johndoe@example.com', password='securepassword')
    new_category = Category(name='Groceries')
    new_expense = Expense(user_id=1, amount=150.0, category_id=1, description='Weekly groceries', date='2024-07-28')
    
    session.add(new_user)
    session.add(new_category)
    session.add(new_expense)
    session.commit()

# Example of querying data
def query_data():
    users = session.query(User).all()
    for user in users:
        print(user.username, user.email)

# Uncomment the following lines to insert sample data and query it
# insert_sample_data()
# query_data()
