import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict, Union, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Transaction:
    day: int
    amount: float
    name: str
    color: str

@dataclass
class OneTimeTransaction:
    date: datetime
    amount: float
    type: str
    name: str
    color: str

class FinanceTracker:
    def __init__(self, initial_balance: float):
        self.data_file = Path('finance_data.json')
        self.initial_balance: float = initial_balance
        self.current_balance: float = initial_balance
        self.monthly_incomes: List[Transaction] = []
        self.monthly_expenses: List[Transaction] = []
        self.one_time_transactions: List[OneTimeTransaction] = []
        
        self.load_data()
        if not self.monthly_incomes and not self.monthly_expenses:
            self._set_default_transactions()

    def _set_default_transactions(self) -> None:
        """Set default monthly transactions if none exist"""
        self.monthly_incomes = [
            Transaction(day=21, amount=13000, name="Pension", color="green")
        ]
        
        self.monthly_expenses = [
            Transaction(day=14, amount=35000, name="Rent", color="red"),
            Transaction(day=22, amount=900, name="Internet", color="darkred")
        ]
        self.save_data()

    def load_data(self) -> None:
        """Load data from JSON file with error handling"""
        try:
            if self.data_file.exists():
                data = json.loads(self.data_file.read_text())
                self.initial_balance = data.get('initial_balance', self.initial_balance)
                self.current_balance = data.get('current_balance', self.current_balance)
                
                # Convert dictionaries to dataclass instances
                self.monthly_incomes = [Transaction(**t) for t in data.get('monthly_incomes', [])]
                self.monthly_expenses = [Transaction(**t) for t in data.get('monthly_expenses', [])]
                
                # Handle datetime conversion for one-time transactions
                self.one_time_transactions = []
                for t in data.get('one_time_transactions', []):
                    t['date'] = datetime.fromisoformat(t['date'])
                    self.one_time_transactions.append(OneTimeTransaction(**t))
        except Exception as e:
            print(f"Error loading data: {e}")
            self._set_default_transactions()

    def save_data(self) -> None:
        """Save current state to JSON file with error handling"""
        try:
            data = {
                'initial_balance': self.initial_balance,
                'current_balance': self.current_balance,
                'monthly_incomes': [asdict(t) for t in self.monthly_incomes],
                'monthly_expenses': [asdict(t) for t in self.monthly_expenses],
                'one_time_transactions': [
                    {**asdict(t), 'date': t.date.isoformat()} 
                    for t in self.one_time_transactions
                ]
            }
            
            self.data_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"Error saving data: {e}")

    def add_income(self, amount: float, date: Optional[datetime] = None, 
                  name: Optional[str] = None, color: str = "green") -> None:
        """Add one-time income with validation"""
        if amount <= 0:
            raise ValueError("Income amount must be positive")
            
        self.one_time_transactions.append(OneTimeTransaction(
            date=date or datetime.now(),
            amount=amount,
            type="income",
            name=name or "One-time Income",
            color=color
        ))
        self.save_data()

    def add_expense(self, amount: float, date: Optional[datetime] = None,
                   name: Optional[str] = None, color: str = "red") -> None:
        """Add one-time expense with validation"""
        if amount <= 0:
            raise ValueError("Expense amount must be positive")
            
        self.one_time_transactions.append(OneTimeTransaction(
            date=date or datetime.now(),
            amount=-amount,
            type="expense",
            name=name or "One-time Expense",
            color=color
        ))
        self.save_data()

    def add_monthly_income(self, day: int, amount: float, name: str, 
                         color: str = "green") -> None:
        """Add monthly income with validation"""
        if not 1 <= day <= 31:
            raise ValueError("Day must be between 1 and 31")
        if amount <= 0:
            raise ValueError("Income amount must be positive")
            
        self.monthly_incomes.append(Transaction(
            day=day,
            amount=amount,
            name=name,
            color=color
        ))
        self.save_data()

    def add_monthly_expense(self, day: int, amount: float, name: str,
                          color: str = "red") -> None:
        """Add monthly expense with validation"""
        if not 1 <= day <= 31:
            raise ValueError("Day must be between 1 and 31")
        if amount <= 0:
            raise ValueError("Expense amount must be positive")
            
        self.monthly_expenses.append(Transaction(
            day=day,
            amount=amount,
            name=name,
            color=color
        ))
        self.save_data()

    def update_initial_balance(self, balance: float) -> None:
        """Update initial balance with validation"""
        if balance < 0:
            raise ValueError("Initial balance cannot be negative")
            
        self.initial_balance = balance
        self.current_balance = balance
        self.save_data()

    def generate_daily_forecast(self, max_days: int = 180) -> pd.DataFrame:
        """Generate daily forecast with improved performance"""
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        forecast_data = []
        current_balance = self.initial_balance
        
        # Pre-sort one-time transactions for better performance
        sorted_transactions = sorted(
            self.one_time_transactions,
            key=lambda x: x.date.date()
        )
        
        for day_offset in range(max_days):
            current_date = start_date + timedelta(days=day_offset)
            day_transactions = []
            
            # Add monthly transactions
            if any(income.day == current_date.day for income in self.monthly_incomes):
                day_transactions.extend([
                    {
                        "type": "income",
                        "name": income.name,
                        "amount": income.amount,
                        "color": income.color
                    }
                    for income in self.monthly_incomes
                    if income.day == current_date.day
                ])
            
            if any(expense.day == current_date.day for expense in self.monthly_expenses):
                day_transactions.extend([
                    {
                        "type": "expense",
                        "name": expense.name,
                        "amount": -expense.amount,
                        "color": expense.color
                    }
                    for expense in self.monthly_expenses
                    if expense.day == current_date.day
                ])
            
            # Add one-time transactions
            day_transactions.extend([
                {
                    "type": t.type,
                    "name": t.name,
                    "amount": t.amount,
                    "color": t.color
                }
                for t in sorted_transactions
                if t.date.date() == current_date.date()
            ])
            
            # Update balance
            for transaction in day_transactions:
                current_balance += transaction['amount']
            
            forecast_data.append({
                "date": current_date,
                "transactions": day_transactions,
                "balance": current_balance
            })
            
            if current_balance <= 0:
                break
        
        return self._create_forecast_dataframe(forecast_data)
    
    def _create_forecast_dataframe(self, forecast_data: List[Dict]) -> pd.DataFrame:
        """Create forecast DataFrame with improved efficiency"""
        rows = []
        for entry in forecast_data:
            if entry['transactions']:
                rows.extend([
                    {
                        "Date": entry['date'].strftime("%Y-%m-%d"),
                        "Transaction": transaction['name'],
                        "Income": abs(transaction['amount']) if transaction['amount'] > 0 else 0,
                        "Expense": abs(transaction['amount']) if transaction['amount'] < 0 else 0,
                        "Balance": entry['balance']
                    }
                    for transaction in entry['transactions']
                ])
            else:
                rows.append({
                    "Date": entry['date'].strftime("%Y-%m-%d"),
                    "Transaction": "-",
                    "Income": 0,
                    "Expense": 0,
                    "Balance": entry['balance']
                })
        
        return pd.DataFrame(rows)

# Styles
STYLES = {
    'content': {
        'margin-left': 'auto',
        'margin-right': 'auto',
        'max-width': '1200px',
        'padding': '2rem',
        'background-color': '#f8fafc',
        'min-height': '100vh',
        'font-family': 'Inter, sans-serif'
    },
    'card': {
        'background-color': 'white',
        'padding': '2rem',
        'border-radius': '8px',
        'box-shadow': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
        'margin-bottom': '2rem'
    },
    'input': {
        'margin-right': '1rem',
        'padding': '0.5rem',
        'border-radius': '4px',
        'border': '1px solid #e2e8f0',
        'margin-bottom': '1rem'
    },
    'button': {
        'background-color': '#1a365d',
        'color': 'white',
        'padding': '0.5rem 1rem',
        'border-radius': '4px',
        'border': 'none',
        'cursor': 'pointer',
        'font-weight': '500',
        'transition': 'background-color 0.2s'
    }
}

def create_app():
    """Create and configure Dash application"""
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'
        ]
    )
    server = app.server
    # Initialize FinanceTracker
    tracker = FinanceTracker(0)
    
    app.layout = html.Div(style=STYLES['content'], children=[
        html.H1("Панель финансового прогноза", style={
            'color': '#1a365d',
            'text-align': 'center',
            'margin-bottom': '2rem',
            'font-weight': '700'
        }),
        
        # Initial Balance Input
        html.Div(style=STYLES['card'], children=[
            html.H3("Текущий баланс", style={
                'color': '#2d3748',
                'margin-bottom': '1rem'
            }),
            dcc.Input(
                id='initial-balance',
                type='number',
                placeholder='Enter initial balance',
                value=0,
                style=STYLES['input']
            ),
            html.Button(
                'Обновить баланс',
                id='update-balance-button',
                n_clicks=0,
                style=STYLES['button']
            ),
        ]),
        
        # Monthly Transactions Section
        html.Div(style=STYLES['card'], children=[
            html.Div(style={
                'display': 'flex',
                'gap': '2rem',
                'flex-wrap': 'wrap'
            }, children=[
                # Monthly Income
                html.Div(style={
                    'flex': '1',
                    'min-width': '300px'
                }, children=[
                    html.H3("Добавить ежемесячное поступление", style={
                        'color': '#2d3748',
                        'margin-bottom': '1rem'
                    }),
                    dcc.Input(
                        id='income-day',
                        type='number',
                        placeholder='Day of month',
                        min=1,
                        max=31,
                        style=STYLES['input']
                    ),
                    dcc.Input(
                        id='income-amount',
                        type='number',
                        placeholder='Amount',
                        style=STYLES['input']
                    ),
                    dcc.Input(
                        id='income-name',
                        type='text',
                        placeholder='Description',
                        style=STYLES['input']
                    ),
                    html.Button(
                        'Добавить доход',
                        id='add-monthly-income-button',
                        n_clicks=0,
                        style={
                            **STYLES['button'],
                            'background-color': '#2f855a'
                        }
                    ),
                ]),
                
                # Monthly Expense
                html.Div(style={
                    'flex': '1',
                    'min-width': '300px'
                }, children=[
                    html.H3("Add Monthly Expense", style={
                        'color': '#2d3748',
                        'margin-bottom': '1rem'
                    }),
                    dcc.Input(
                        id='expense-day',
                        type='number',
                        placeholder='Day of month',
                        min=1,
                        max=31,
                        style=STYLES['input']
                    ),
                    dcc.Input(
                        id='expense-amount',
                        type='number',
                        placeholder='Amount',
                        style=STYLES['input']
                    ),
                    dcc.Input(
                        id='expense-name',
                        type='text',
                        placeholder='Description',
                        style=STYLES['input']
                    ),
                    html.Button(
                        'Добавить расход',
                        id='add-monthly-expense-button',
                        n_clicks=0,
                        style={
                            **STYLES['button'],
                            'background-color': '#c53030'
                        }
                    ),
                ]),
            ]),
        ]),
        
        # One-time Transaction
        html.Div(style=STYLES['card'], children=[
            html.H3("Добавить единичная поступление", style={
                'color': '#2d3748',
                'margin-bottom': '1rem'
            }),
            html.Div(style={
                'display': 'flex',
                'gap': '1rem',
                'flex-wrap': 'wrap',
                'align-items': 'center'
            }, children=[
                dcc.DatePickerSingle(
                    id='transaction-date',
                    date=datetime.now().date(),
                    style={'margin-bottom': '1rem'}
                ),
                dcc.Input(
                    id='transaction-amount',
                    type='number',
                    placeholder='Amount',
                    style=STYLES['input']
                ),
                dcc.Input(
                    id='transaction-name',
                    type='text',
                    placeholder='Description',
                    style=STYLES['input']
                ),
                dcc.RadioItems(
                    id='transaction-type',
                    options=[
                        {'label': 'Income', 'value': 'income'},
                        {'label': 'Expense', 'value': 'expense'}
                    ],
                    value='income',
                    style={'margin-bottom': '1rem'},
                    inputStyle={'margin-right': '0.5rem'},
                    labelStyle={'margin-right': '1rem'}
                ),
                html.Button(
                    'Добавить операцию',
                    id='add-transaction-button',
                    n_clicks=0,
                    style=STYLES['button']
                ),
            ]),
        ]),
        
        # Forecast Table
        html.Div(style=STYLES['card'], children=[
            html.H3("Таблица прогнозов", style={
                'color': '#2d3748',
                'margin-bottom': '1rem'
            }),
            dash_table.DataTable(
                id='forecast-table',
                columns=[
                    {"name": i, "id": i}
                    for i in ["Date", "Transaction", "Income", "Expense", "Balance"]
                ],
                style_table={
                    'height': '300px',
                    'overflowY': 'auto',
                    'border': '1px solid #e2e8f0',
                    'border-radius': '4px'
                },
                style_cell={
                    'textAlign': 'left',
                    'padding': '12px',
                    'font-family': 'Inter, sans-serif'
                },
                style_header={
                    'backgroundColor': '#f7fafc',
                    'fontWeight': 'bold',
                    'border-bottom': '2px solid #e2e8f0'
                },
                style_data_conditional=[
                    {
                        'if': {'column_id': 'Income'},
                        'color': '#2f855a'
                    },
                    {
                        'if': {'column_id': 'Expense'},
                        'color': '#c53030'
                    }
                ]
            ),
        ]),
        
        # Forecast Graph
        html.Div(style=STYLES['card'], children=[
            html.H3("Прогноз", style={
                'color': '#2d3748',
                'margin-bottom': '1rem'
            }),
            dcc.Graph(id='forecast-graph')
        ]),
    ])

    @app.callback(
        [Output('forecast-table', 'data'),
         Output('forecast-graph', 'figure')],
        [Input('update-balance-button', 'n_clicks'),
         Input('add-monthly-income-button', 'n_clicks'),
         Input('add-monthly-expense-button', 'n_clicks'),
         Input('add-transaction-button', 'n_clicks')],
        [State('initial-balance', 'value'),
         State('income-day', 'value'),
         State('income-amount', 'value'),
         State('income-name', 'value'),
         State('expense-day', 'value'),
         State('expense-amount', 'value'),
         State('expense-name', 'value'),
         State('transaction-date', 'date'),
         State('transaction-amount', 'value'),
         State('transaction-name', 'value'),
         State('transaction-type', 'value')]
    )
    def update_forecast(balance_clicks, income_clicks, expense_clicks, transaction_clicks,
                       initial_balance, income_day, income_amount, income_name,
                       expense_day, expense_amount, expense_name,
                       transaction_date, transaction_amount, transaction_name, transaction_type):
        """Update forecast table and graph based on user input"""
        ctx = dash.callback_context
        if not ctx.triggered:
            button_id = 'No clicks yet'
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            if button_id == 'update-balance-button' and initial_balance is not None:
                tracker.update_initial_balance(initial_balance)
            
            elif button_id == 'add-monthly-income-button' and all([income_day, income_amount, income_name]):
                tracker.add_monthly_income(income_day, income_amount, income_name)
            
            elif button_id == 'add-monthly-expense-button' and all([expense_day, expense_amount, expense_name]):
                tracker.add_monthly_expense(expense_day, expense_amount, expense_name)
            
            elif button_id == 'add-transaction-button' and all([transaction_date, transaction_amount, transaction_name]):
                date = datetime.strptime(transaction_date, '%Y-%m-%d')
                if transaction_type == 'income':
                    tracker.add_income(transaction_amount, date, transaction_name)
                else:
                    tracker.add_expense(transaction_amount, date, transaction_name)
        
        except ValueError as e:
            print(f"Validation error: {e}")
            # You might want to add some UI feedback here
        except Exception as e:
            print(f"Unexpected error: {e}")
            # You might want to add some UI feedback here
        
        # Generate forecast
        forecast_df = tracker.generate_daily_forecast()
        
        # Create figure
        fig = go.Figure()
        
        # Add area plot for balance
        fig.add_trace(go.Scatter(
            x=forecast_df['Date'],
            y=forecast_df['Balance'],
            fill='tozeroy',
            mode='lines+markers',
            name='Balance',
            line=dict(color='#4299e1')
        ))
        
        # Add bar plots for income and expenses
        fig.add_trace(go.Bar(
            x=forecast_df['Date'],
            y=forecast_df['Expense'],
            name='Expense',
            marker=dict(color='#fc8181')
        ))
        
        fig.add_trace(go.Bar(
            x=forecast_df['Date'],
            y=forecast_df['Income'],
            name='Income',
            marker=dict(color='#68d391')
        ))
        
        # Update layout
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Amount',
            barmode='group',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font_family='Inter, sans-serif',
            margin=dict(t=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Update axes
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='#f0f0f0'
        )
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='#f0f0f0'
        )
        
        return forecast_df.to_dict('records'), fig

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 8080))
    app.run_server(host='0.0.0.0', port=port)
