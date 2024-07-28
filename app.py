import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import os

# Define your MySQL connection string
DATABASE_URL = os.getenv("DATABASE_URL", "mysql://root@localhost/penny_wise")

# Create an engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)  # Added length constraint
    email = Column(String(150), nullable=False, unique=True)  # Added length constraint
    password = Column(String(255), nullable=False)  # Added length constraint

# Define the Category model
class Category(Base):
    __tablename__ = 'categories'
    category_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)  # Added length constraint

# Define the Expense model
class Expense(Base):
    __tablename__ = 'expenses'
    expense_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    amount = Column(Float, nullable=False)  # Changed from Integer to Float
    category_id = Column(Integer, ForeignKey('categories.category_id'), nullable=False)
    description = Column(String(255))  # Increased length from 60 to 255
    date = Column(Date, nullable=False)

# Create all tables in the database
Base.metadata.create_all(engine)

def add_expense(user_id, amount, category_id, description, date):
    """Add a new expense to the database."""
    try:
        new_expense = Expense(user_id=user_id, amount=amount, category_id=category_id, description=description, date=date)
        session.add(new_expense)
        session.commit()
    except Exception as e:
        st.error(f"Error adding expense: {e}")

def get_categories():
    """Retrieve all categories from the database."""
    try:
        return session.query(Category).all()
    except Exception as e:
        st.error(f"Error fetching categories: {e}")
        return []

def get_expenses(user_id):
    """Retrieve expenses for a specific user."""
    try:
        return session.query(Expense).filter_by(user_id=user_id).all()
    except Exception as e:
        st.error(f"Error fetching expenses: {e}")
        return []

def get_category_totals(user_id):
    """Calculate total expenses per category for a specific user."""
    expenses = get_expenses(user_id)
    if not expenses:
        return pd.DataFrame(columns=["Category", "Amount"])
    
    df = pd.DataFrame([(exp.amount, exp.category_id) for exp in expenses], columns=["Amount", "Category"])
    category_totals = df.groupby("Category").sum().reset_index()
    category_totals['Category'] = category_totals['Category'].map({cat.category_id: cat.name for cat in get_categories()})
    return category_totals

def get_monthly_summary(user_id):
    """Provide a monthly summary of expenses for a specific user."""
    expenses = get_expenses(user_id)
    if not expenses:
        return pd.DataFrame(columns=["Month", "Amount"])
    
    df = pd.DataFrame([(exp.amount, exp.date) for exp in expenses], columns=["Amount", "Date"])
    df['Month'] = df['Date'].apply(lambda x: x.strftime('%Y-%m'))
    monthly_summary = df.groupby("Month").sum().reset_index()
    return monthly_summary

# Streamlit app layout
st.title("Expense Tracker")

# Check for existing user or create a new one (for demonstration)
user = session.query(User).filter_by(user_id=1).first()
if not user:
    user = User(username="demo_user", email="demo@example.com", password="password")
    session.add(user)
    session.commit()

# Expense Logging Form
with st.form("expense_form"):
    amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    
    # Fetch categories and populate select box
    categories = get_categories()  
    category_options = [(cat.category_id, cat.name) for cat in categories]
    
    # Select box for categories
    category_id = st.selectbox("Category", category_options, format_func=lambda x: x[1])
    
    # Input for description and date
    description = st.text_input("Description")
    date = st.date_input("Date")
    
    # Submit button for form
    submitted = st.form_submit_button("Add Expense")

    if submitted:
        # Static user_id for demonstration purposes
        user_id = user.user_id
        add_expense(user_id, amount, category_id[0], description, date)
        st.success("Expense added successfully!")

# Display Expense Table
st.subheader("Your Expenses")
expenses = get_expenses(user_id=user.user_id)
expense_df = pd.DataFrame(
    [(exp.expense_id, exp.amount, exp.category_id, exp.description, exp.date) for exp in expenses],
    columns=["ID", "Amount", "Category", "Description", "Date"]
)
expense_df['Category'] = expense_df['Category'].map({cat.category_id: cat.name for cat in get_categories()})
st.dataframe(expense_df)

# Category Analysis
st.subheader("Expenses by Category")
category_totals = get_category_totals(user_id=user.user_id)
st.dataframe(category_totals)

# Monthly Summary
st.subheader("Monthly Summary")
monthly_summary = get_monthly_summary(user_id=user.user_id)
st.dataframe(monthly_summary)

# Plot Category Analysis
st.subheader("Category Analysis Chart")
fig, ax = plt.subplots()
ax.pie(category_totals['Amount'], labels=category_totals['Category'], autopct='%1.1f%%', startangle=140)
ax.axis('equal')
st.pyplot(fig)
