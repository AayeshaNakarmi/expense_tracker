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
    username = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False)

# Define the Category model
class Category(Base):
    __tablename__ = 'categories'
    category_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

# Define the Expense model
class Expense(Base):
    __tablename__ = 'expenses'
    expense_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.category_id'), nullable=False)
    description = Column(String(255))
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

def update_expense(expense_id, amount, category_id, description, date):
    """Update an existing expense in the database."""
    try:
        expense_to_update = session.query(Expense).filter_by(expense_id=expense_id).first()
        if expense_to_update:
            expense_to_update.amount = amount
            expense_to_update.category_id = category_id
            expense_to_update.description = description
            expense_to_update.date = date
            session.commit()
            st.success(f"Expense {expense_id} updated successfully!")
        else:
            st.error(f"Expense {expense_id} not found.")
    except Exception as e:
        st.error(f"Error updating expense: {e}")

def delete_expense(expense_id):
    """Delete an expense from the database."""
    try:
        expense_to_delete = session.query(Expense).filter_by(expense_id=expense_id).first()
        if expense_to_delete:
            session.delete(expense_to_delete)
            session.commit()
            st.success(f"Expense {expense_id} deleted successfully!")
        else:
            st.error(f"Expense {expense_id} not found.")
    except Exception as e:
        st.error(f"Error deleting expense: {e}")

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
    df['Date'] = pd.to_datetime(df['Date'])  # Ensure the 'Date' column is in datetime format
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    monthly_summary = df.groupby("Month")['Amount'].sum().reset_index()
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
        st.experimental_rerun()

# Display Expense Table
st.subheader("Your Expenses")
expenses = get_expenses(user_id=user.user_id)
expense_df = pd.DataFrame(
    [(exp.expense_id, exp.amount, exp.category_id, exp.description, exp.date) for exp in expenses],
    columns=["ID", "Amount", "Category", "Description", "Date"]
)
expense_df['Category'] = expense_df['Category'].map({cat.category_id: cat.name for cat in get_categories()})

# Display expenses in a table with delete and edit buttons
st.write("### Expenses Table")
for index, row in expense_df.iterrows():
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        st.write(row['ID'])
    with col2:
        st.write(row['Amount'])
    with col3:
        st.write(row['Category'])
    with col4:
        st.write(row['Description'])
    with col5:
        st.write(row['Date'])

    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"Delete {row['ID']}"):
            delete_expense(row['ID'])
            st.experimental_rerun()
    with col2:
        if st.button(f"Edit {row['ID']}"):
            st.session_state[f"edit_{row['ID']}"] = not st.session_state.get(f"edit_{row['ID']}", False)
    
    if st.session_state.get(f"edit_{row['ID']}", False):
        with st.form(f"edit_form_{row['ID']}"):
            new_amount = st.number_input("Amount", value=row['Amount'], min_value=0.0, format="%.2f")
            new_category_index = next((i for i, v in enumerate(category_options) if v[0] == row['Category']), None)
            new_category_id = st.selectbox("Category", category_options, index=new_category_index if new_category_index is not None else 0, format_func=lambda x: x[1])
            new_description = st.text_input("Description", value=row['Description'])
            new_date = st.date_input("Date", value=row['Date'])
            edit_button = st.form_submit_button("Edit")
            if edit_button:
                update_expense(row['ID'], new_amount, new_category_id[0], new_description, new_date)
                st.session_state[f"edit_{row['ID']}"] = False
                st.experimental_rerun()

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
