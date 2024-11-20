import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

class FinancialTracker:
    def __init__(self, mongo_uri):
        """Initialize MongoDB connection"""
        try:
            # Connect to MongoDB
            self.client = MongoClient(mongo_uri)
            
            # Select or create database
            self.db = self.client['financial_tracker']
            
            # Create collections
            self.expenses_collection = self.db['expenses']
            self.income_collection = self.db['income']
            self.investments_collection = self.db['investments']
            
            st.sidebar.success("MongoDB Connection Successful!")
        except Exception as e:
            st.sidebar.error(f"MongoDB Connection Error: {e}")
            raise

    def add_expense(self, date, category, amount, description):
        """Add an expense to MongoDB"""
        expense_doc = {
            'date': date,
            'category': category,
            'amount': float(amount),
            'description': description,
            'timestamp': datetime.now()
        }
        return self.expenses_collection.insert_one(expense_doc)

    def add_income(self, date, source, amount, description):
        """Add income to MongoDB"""
        income_doc = {
            'date': date,
            'source': source,
            'amount': float(amount),
            'description': description,
            'timestamp': datetime.now()
        }
        return self.income_collection.insert_one(income_doc)

    def add_investment(self, date, type, amount, ticker, purchase_price):
        """Add an investment to MongoDB"""
        investment_doc = {
            'date': date,
            'type': type,
            'amount': float(amount),
            'ticker': ticker,
            'purchase_price': float(purchase_price),
            'timestamp': datetime.now()
        }
        return self.investments_collection.insert_one(investment_doc)

    def get_expenses(self):
        """Retrieve expenses from MongoDB"""
        expenses = list(self.expenses_collection.find())
        return pd.DataFrame(expenses)

    def get_income(self):
        """Retrieve income from MongoDB"""
        income = list(self.income_collection.find())
        return pd.DataFrame(income)

    def get_investments(self):
        """Retrieve investments from MongoDB"""
        investments = list(self.investments_collection.find())
        return pd.DataFrame(investments)

    def generate_financial_summary(self):
        """Generate a comprehensive financial summary"""
        # Aggregate expenses
        expenses_aggregate = list(self.expenses_collection.aggregate([
            {
                '$group': {
                    '_id': None,
                    'total_expenses': {'$sum': '$amount'}
                }
            }
        ]))
        total_expenses = expenses_aggregate[0]['total_expenses'] if expenses_aggregate else 0

        # Aggregate income
        income_aggregate = list(self.income_collection.aggregate([
            {
                '$group': {
                    '_id': None,
                    'total_income': {'$sum': '$amount'}
                }
            }
        ]))
        total_income = income_aggregate[0]['total_income'] if income_aggregate else 0

        # Aggregate investments
        investments_aggregate = list(self.investments_collection.aggregate([
            {
                '$group': {
                    '_id': None,
                    'total_investments': {'$sum': '$amount'}
                }
            }
        ]))
        total_investments = investments_aggregate[0]['total_investments'] if investments_aggregate else 0

        # Calculate net worth
        net_worth = total_income - total_expenses + total_investments

        return {
            'total_expenses': total_expenses,
            'total_income': total_income,
            'total_investments': total_investments,
            'net_worth': net_worth
        }

def main():
    st.set_page_config(page_title="Financial Tracker", page_icon=":money_with_wings:", layout="wide")
    
    # MongoDB Connection URI
    mongo_uri = st.secrets.get("MONGO_URI", "mongodb+srv://richardrt13:QtZ9CnSP6dv93hlh@stockidea.isx8swk.mongodb.net/?retryWrites=true&w=majority&appName=StockIdea")
    
    try:
        tracker = FinancialTracker(mongo_uri)

        # Sidebar Navigation
        st.sidebar.title("Financial Tracker")
        menu = ["Home", "Add Expense", "Add Income", "Add Investment", "Reports"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Home":
            st.title("Financial Dashboard")
            
            # Financial Summary
            summary = tracker.generate_financial_summary()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Income", f"${summary['total_income']:,.2f}")
            with col2:
                st.metric("Total Expenses", f"${summary['total_expenses']:,.2f}")
            with col3:
                st.metric("Total Investments", f"${summary['total_investments']:,.2f}")
            with col4:
                st.metric("Net Worth", f"${summary['net_worth']:,.2f}")

            # Expense Breakdown
            st.subheader("Expense Breakdown")
            expenses_df = tracker.get_expenses()
            if not expenses_df.empty:
                expense_fig = px.pie(expenses_df, names='category', values='amount', 
                                      title='Expenses by Category')
                st.plotly_chart(expense_fig)

        elif choice == "Add Expense":
            st.title("Record Expenses")
            
            with st.form(key='expense_form'):
                expense_date = st.date_input("Date")
                expense_category = st.selectbox("Category", [
                    "Groceries", "Utilities", "Rent/Mortgage", 
                    "Transportation", "Entertainment", "Other"
                ])
                expense_amount = st.number_input("Amount", min_value=0.0, format="%.2f")
                expense_description = st.text_input("Description")
                
                submit_expense = st.form_submit_button("Add Expense")
                
                if submit_expense:
                    tracker.add_expense(
                        expense_date, 
                        expense_category, 
                        expense_amount, 
                        expense_description
                    )
                    st.success("Expense Added Successfully!")

        elif choice == "Add Income":
            st.title("Record Income")
            
            with st.form(key='income_form'):
                income_date = st.date_input("Date")
                income_source = st.selectbox("Source", [
                    "Salary", "Freelance", "Investment Income", 
                    "Rental Income", "Other"
                ])
                income_amount = st.number_input("Amount", min_value=0.0, format="%.2f")
                income_description = st.text_input("Description")
                
                submit_income = st.form_submit_button("Add Income")
                
                if submit_income:
                    tracker.add_income(
                        income_date, 
                        income_source, 
                        income_amount, 
                        income_description
                    )
                    st.success("Income Added Successfully!")

        elif choice == "Add Investment":
            st.title("Record Investments")
            
            with st.form(key='investment_form'):
                investment_date = st.date_input("Date")
                investment_type = st.selectbox("Investment Type", [
                    "Stocks", "Bonds", "Real Estate", 
                    "Mutual Funds", "Cryptocurrency", "Other"
                ])
                investment_amount = st.number_input("Amount Invested", min_value=0.0, format="%.2f")
                investment_ticker = st.text_input("Ticker Symbol (if applicable)")
                purchase_price = st.number_input("Purchase Price per Share", min_value=0.0, format="%.2f")
                
                submit_investment = st.form_submit_button("Add Investment")
                
                if submit_investment:
                    tracker.add_investment(
                        investment_date, 
                        investment_type, 
                        investment_amount, 
                        investment_ticker, 
                        purchase_price
                    )
                    st.success("Investment Added Successfully!")

        elif choice == "Reports":
            st.title("Financial Reports")
            
            # Expenses Report
            st.subheader("Expenses Report")
            expenses_df = tracker.get_expenses()
            st.dataframe(expenses_df)
            
            # Income Report
            st.subheader("Income Report")
            income_df = tracker.get_income()
            st.dataframe(income_df)
            
            # Investments Report
            st.subheader("Investments Report")
            investments_df = tracker.get_investments()
            st.dataframe(investments_df)

    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
