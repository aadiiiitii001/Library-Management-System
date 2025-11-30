from flask import Flask, render_template, request, redirect, url_for
from model import db, Book, Member, Issue
from datetime import datetime, timedelta
import plotly.express as px
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = "YourSecretKey"

db.init_app(app)

def create_tables():
    with app.app_context():
        db.create_all()

create_tables()

# ------------------------------
# HOME PAGE
# ------------------------------
@app.route('/')
def index():
    books = Book.query.all()
    members = Member.query.all()
    issues = Issue.query.filter_by(return_date=None).all()

    return render_template(
        'index.html',
        books=books,
        members=members,
        issues=issues
    )

# ------------------------------
# ADD BOOK
# ------------------------------
@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']

    # For advanced model: quantity=1, available=1
    new_book = Book(
        title=title,
        author=author,
        quantity=1,
        available=1
    )

    db.session.add(new_book)
    db.session.commit()

    return redirect(url_for('index'))

# ------------------------------
# ADD MEMBER
# ------------------------------
@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form['name']
    email = request.form['email']

    db.session.add(Member(name=name, email=email))
    db.session.commit()

    return redirect(url_for('index'))

# ------------------------------
# ISSUE BOOK (With Due-Date + Stock Update)
# ------------------------------
@app.route('/issue_book', methods=['POST'])
def issue_book():
    book_id = request.form['book_id']
    member_id = request.form['member_id']

    book = Book.query.get(book_id)

    # Only allow if stock available
    if book and book.available > 0:
        issue = Issue(
            book_id=book_id,
            member_id=member_id,
            due_date=datetime.utcnow() + timedelta(days=7)  # Return in 7 days
        )

        book.available -= 1  # Reduce available stock

        db.session.add(issue)
        db.session.commit()

    return redirect(url_for('index'))

# ------------------------------
# RETURN BOOK (With Fine Calculation)
# ------------------------------
@app.route('/return_book/<int:issue_id>')
def return_book(issue_id):
    issue = Issue.query.get(issue_id)

    if issue:
        issue.return_date = datetime.utcnow()

        # Fine: Rs. 5 per delayed day
        if issue.return_date > issue.due_date:
            late_days = (issue.return_date - issue.due_date).days
            issue.fine = late_days * 5
        else:
            issue.fine = 0

        # Increase available stock again
        issue.book.available += 1

        db.session.commit()

    return redirect(url_for('index'))

# ------------------------------
# DASHBOARD PAGE
# ------------------------------
@app.route('/dashboard')
def dashboard():

    issues = Issue.query.all()

    data = [{
        'issue_date': i.issue_date,
        'returned': bool(i.return_date)
    } for i in issues]

    df = pd.DataFrame(data)

    # Chart: Issues per month
    if not df.empty:
        df['month'] = df['issue_date'].dt.strftime('%b')
        chart = px.bar(
            df.groupby('month').size().reset_index(name='Issues'),
            x='month',
            y='Issues',
            title='Books Issued Per Month',
        )
        chart_html = chart.to_html(full_html=False)
    else:
        chart_html = "<p>No data yet.</p>"

    return render_template(
        'dashboard.html',
        chart_html=chart_html,
        total_books=Book.query.count(),
        total_members=Member.query.count(),
        total_issued=Issue.query.filter_by(return_date=None).count()
    )

# ------------------------------
# RUN APP
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True)
