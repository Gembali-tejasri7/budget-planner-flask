from flask import Flask, render_template, request, redirect, url_for, session
from collections import OrderedDict
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Important for session management

# Dummy user data for demonstration
users = {'testuser': 'testpassword'}
user_data = {}  # To store budget data for each user

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username not in users:
            users[username] = password
            user_data[username] = {}
            return redirect(url_for('login'))
        else:
            return render_template('signup.html', error='Username already exists')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))  # Correct redirection to dashboard
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/select_months')
def select_months():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('select_months.html')

@app.route('/set_months', methods=['POST'])
def set_months():
    if 'username' not in session:
        return redirect(url_for('login'))
    num_months = int(request.form['num_months'])
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][:num_months]
    session['months'] = months
    user = session['username']
    if user not in user_data:
        user_data[user] = {'budget_data': {}}  # Initialize if it doesn't exist
    user_data[user]['budget_data'] = {month: {'income': 0, 'expenses': {}, 'savings': {}} for month in months}
    return redirect(url_for('enter_income', month_index=0))

@app.route('/enter_income/<int:month_index>', methods=['GET', 'POST'])
def enter_income(month_index):
    if 'username' not in session:
        return redirect(url_for('login'))
    months = session.get('months')
    if month_index < len(months):
        current_month = months[month_index]
        if request.method == 'POST':
            income = float(request.form['income'])
            user = session['username']
            user_data[user]['budget_data'][current_month]['income'] = income
            return redirect(url_for('select_categories', month_index=month_index))
        return render_template('enter_income.html', month=current_month, month_index=month_index)
    else:
        return redirect(url_for('enter_savings', month_index=0)) # Proceed to savings after all months' income

@app.route('/select_categories/<int:month_index>', methods=['GET', 'POST'])
def select_categories(month_index):
    if 'username' not in session:
        return redirect(url_for('login'))
    months = session.get('months')
    if month_index < len(months):
        current_month = months[month_index]
        categories = ["Rent", "Utilities", "Grocery", "Emergency", "Travel", "Medical", "Entertainment", "Other"]
        if request.method == 'POST':
            selected_categories = request.form.getlist('categories')
            user = session['username']
            user_data[user]['budget_data'][current_month]['categories'] = selected_categories
            return redirect(url_for('enter_expenses', month_index=month_index))
        return render_template('select_categories.html', month=current_month, categories=categories, month_index=month_index)
    else:
        return redirect(url_for('enter_savings', month_index=0)) # Proceed to savings after all months' categories

@app.route('/enter_expenses/<int:month_index>', methods=['GET', 'POST'])
def enter_expenses(month_index):
    if 'username' not in session:
        return redirect(url_for('login'))
    months = session.get('months')
    if month_index < len(months):
        current_month = months[month_index]
        user = session['username']
        selected_categories = user_data[user]['budget_data'][current_month]['categories']
        travel_options = ["Flight", "Train", "Cab", "Bus", "Auto", "Bike", "Other"]
        expenses = {}
        if request.method == 'POST':
            for cat in selected_categories:
                if cat == 'Travel':
                    travel_expense = {}
                    for option in travel_options:
                        expense_value = request.form.get(f'expense_{option.lower()}')
                        if expense_value:
                            travel_expense[option] = float(expense_value)
                    expenses[cat] = travel_expense
                else:
                    expense_value = float(request.form.get(f'expense_{cat.lower()}', 0))
                    expenses[cat] = expense_value
            user_data[user]['budget_data'][current_month]['expenses'] = expenses
            return redirect(url_for('enter_savings', month_index=month_index))
        return render_template('enter_expenses.html', month=current_month, categories=selected_categories, travel_options=travel_options, month_index=month_index)
    else:
        return redirect(url_for('enter_savings', month_index=0))

@app.route('/enter_savings/<int:month_index>', methods=['GET', 'POST'])
def enter_savings(month_index):
    if 'username' not in session:
        return redirect(url_for('login'))
    months = session.get('months')
    if month_index < len(months):
        current_month = months[month_index]
        if request.method == 'POST':
            savings_amount = float(request.form['savings_amount'])
            item_to_purchase = request.form['item_to_purchase']
            item_price = float(request.form['item_price'])

            user = session['username']
            user_data[user]['budget_data'][current_month]['savings'] = {
                'amount': savings_amount,
                'item': item_to_purchase,
                'price': item_price
            }
            next_month_index = month_index + 1
            if next_month_index < len(months):
                return redirect(url_for('enter_income', month_index=next_month_index))
            else:
                return redirect(url_for('enter_tax'))

        return render_template('enter_savings.html', month=current_month, month_index=month_index)
    else:
        return redirect(url_for('enter_tax'))

@app.route('/enter_tax', methods=['GET', 'POST'])
def enter_tax():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        pays_tax = request.form.get('pays_tax')
        tax_amount = 0
        if pays_tax == 'yes':
            tax_amount = float(request.form['tax_amount'])
        user = session['username']
        user_data[user]['tax'] = tax_amount
        return redirect(url_for('combined_summary'))
    return render_template('enter_tax.html')

@app.route('/combined_summary')
def combined_summary():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = session['username']
    budget_data = user_data.get(user, {}).get('budget_data', {})
    combined_data = {'total_income': 0, 'total_expenses': {}, 'total_savings': 0, 'tax': user_data.get(user, {}).get('tax', 0)}
    for month_data in budget_data.values():
        combined_data['total_income'] += month_data['income']
        combined_data['total_savings'] += month_data['savings'].get('amount', 0)
        for category, expense in month_data['expenses'].items():
            if isinstance(expense, dict):
                for sub_expense in expense.values():
                    combined_data['total_expenses'][category] = combined_data['total_expenses'].get(category, 0) + sub_expense
            else:
                combined_data['total_expenses'][category] = combined_data['total_expenses'].get(category, 0) + expense
    return render_template('combined_summary.html', combined_data=combined_data)

@app.route('/monthly_summary')
def monthly_summary():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = session['username']
    budget_data = user_data.get(user, {}).get('budget_data', {})
    tax = user_data.get(user, {}).get('tax', 0)
    return render_template('monthly_summary.html', budget_data=budget_data, tax=tax)

@app.route('/pie_chart')
def pie_chart():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = session['username']
    budget_data = user_data.get(user, {}).get('budget_data', {})
    category_totals = {}
    for month_data in budget_data.values():
        for category, expense in month_data['expenses'].items():
            if isinstance(expense, dict):
                for sub_expense in expense.values():
                    category_totals[category] = category_totals.get(category, 0) + sub_expense
            else:
                category_totals[category] = category_totals.get(category, 0) + expense
    return render_template('pie_chart.html', category_totals=category_totals)

@app.route('/bar_chart')
def bar_chart():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = session['username']
    budget_data = user_data.get(user, {}).get('budget_data', {})

    month_order = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]

    ordered_monthly_expenses = OrderedDict()
    for month in month_order:
        if month in budget_data:
            expenses = budget_data[month].get('expenses', {})
            print(f"Expenses for {month}: {expenses}")  # Debug print
            total_monthly_expense = sum(sum(exp.values()) if isinstance(exp, dict) else exp for exp in expenses.values())
            print(f"Total expense for {month}: {total_monthly_expense}")  # Debug print
            ordered_monthly_expenses[month] = total_monthly_expense
        else:
            ordered_monthly_expenses[month] = 0
            print(f"No data for {month}, setting expense to 0")  # Debug print

    print(f"Final ordered_monthly_expenses: {ordered_monthly_expenses}")  # Debug print
    return render_template('bar_chart.html', monthly_expenses=ordered_monthly_expenses)

if __name__ == '__main__':
    app.run(debug=True)