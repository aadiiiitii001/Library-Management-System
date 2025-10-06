from flask import Flask, render_template, request, redirect, url_for
from model import db, Book, Member, Issue
from datetime import datetime
import plotly.express as px
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

def create_tables():
    with app.app_context():
        db.create_all()
create_tables()  # call it once before running the app

@app.route('/')
def index():
    books = Book.query.all()
    members = Member.query.all()
    issues = Issue.query.filter_by(return_date=None).all()
    return render_template('index.html', books=books, members=members, issues=issues)

@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    db.session.add(Book(title=title, author=author))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_member', methods=['POST'])
def add_member():
    name = request.form['name']
    email = request.form['email']
    db.session.add(Member(name=name, email=email))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/issue_book', methods=['POST'])
def issue_book():
    book_id = request.form['book_id']
    member_id = request.form['member_id']
    book = Book.query.get(book_id)
    if book and book.available:
        issue = Issue(book_id=book_id, member_id=member_id)
        book.available = False
        db.session.add(issue)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/return_book/<int:issue_id>')
def return_book(issue_id):
    issue = Issue.query.get(issue_id)
    if issue:
        issue.return_date = datetime.utcnow()
        issue.book.available = True
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    issues = Issue.query.all()
    data = [{
        'issue_date': i.issue_date,
        'returned': bool(i.return_date)
    } for i in issues]
    df = pd.DataFrame(data)

    if not df.empty:
        df['month'] = df['issue_date'].dt.strftime('%b')
        chart = px.bar(df.groupby('month').size().reset_index(name='Issues'),
                       x='month', y='Issues', title='Books Issued per Month')
        chart_html = chart.to_html(full_html=False)
    else:
        chart_html = "<p>No data yet.</p>"

    total_books = Book.query.count()
    total_members = Member.query.count()
    total_issued = Issue.query.filter_by(return_date=None).count()

    return render_template('dashboard.html',
                           chart_html=chart_html,
                           total_books=total_books,
                           total_members=total_members,
                           total_issued=total_issued)

if __name__ == '__main__':
    app.run(debug=True)
