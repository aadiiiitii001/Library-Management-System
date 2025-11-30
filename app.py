from flask import Flask, render_template, request, redirect, url_for, session
from model import db, Book, Member, Issue
from datetime import datetime, timedelta
import plotly.express as px
import pandas as pd
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

def create_tables():
    with app.app_context():
        db.create_all()
create_tables()

# ===========================
#  ADMIN LOGIN CONFIG
# ===========================
ADMIN_USER = "admin"
ADMIN_PASS = "1234"

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["admin"] = True
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")


# ===========================
# HOME PAGE
# ===========================
@app.route('/')
def index():
    books = Book.query.all()
    members = Member.query.all()
    issues = Issue.query.filter_by(return_date=None).all()
    return render_template('index.html',
                           books=books,
                           members=members,
                           issues=issues,
                           admin=session.get("admin"))


# ===========================
# SEARCH BAR ROUTE
# ===========================
@app.route("/search")
def search():
    q = request.args.get("q", "")
    results = Book.query.filter(Book.title.contains(q)).all()
    return render_template("search_results.html", q=q, results=results)


# ===========================
#  ADD BOOK / MEMBER
# ===========================
@app.route('/add_book', methods=['POST'])
@admin_required
def add_book():
    title = request.form['title']
    author = request.form['author']
    book = Book(title=title, author=author, available=1)
    db.session.add(book)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_member', methods=['POST'])
@admin_required
def add_member():
    name = request.form['name']
    email = request.form['email']
    db.session.add(Member(name=name, email=email))
    db.session.commit()
    return redirect(url_for('index'))


# ===========================
# ISSUE BOOK - AUTO STOCK MGMT + DUE DATE
# ===========================
@app.route('/issue_book', methods=['POST'])
@admin_required
def issue_book():
    book_id = request.form['book_id']
    member_id = request.form['member_id']

    book = Book.query.get(book_id)
    if book.available > 0:
        issue = Issue(
            book_id=book_id,
            member_id=member_id,
            due_date=datetime.utcnow() + timedelta(days=7)  # 7-day loan
        )
        book.available -= 1
        db.session.add(issue)
        db.session.commit()

    return redirect(url_for('index'))


# ===========================
# RETURN BOOK - FINE CALCULATION
# ===========================
@app.route('/return_book/<int:issue_id>')
@admin_required
def return_book(issue_id):
    issue = Issue.query.get(issue_id)

    if issue:
        issue.return_date = datetime.utcnow()

        # Fine calculation
        if issue.return_date > issue.due_date:
            delay = (issue.return_date - issue.due_date).days
            issue.fine = delay * 5  # ₹5 per day fine

        # Restore stock
        issue.book.available += 1

        db.session.commit()

    return redirect(url_for('index'))


# ===========================
# ADVANCED DASHBOARD
# ===========================
@app.route('/dashboard')
@admin_required
def dashboard():
    issues = Issue.query.all()

    # ---- Issues per Month ----
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
        chart_html = "<p>No issue data available.</p>"

    # ---- Popular Books ----
    popular = db.session.query(
        Book.title, db.func.count(Issue.id)
    ).join(Issue).group_by(Book.id).all()

    if popular:
        df_pop = pd.DataFrame(popular, columns=["Book", "Issues"])
        chart_pop = px.bar(df_pop, x="Book", y="Issues", title="Most Issued Books")
        popular_html = chart_pop.to_html(full_html=False)
    else:
        popular_html = "<p>No popular book data.</p>"

    # ---- Summary Stats ----
    total_books = Book.query.count()
    total_members = Member.query.count()
    total_issued = Issue.query.filter_by(return_date=None).count()
    overdue = Issue.query.filter(Issue.return_date == None, Issue.due_date < datetime.utcnow()).count()

    return render_template('dashboard.html',
                           chart_html=chart_html,
                           popular_html=popular_html,
                           total_books=total_books,
                           total_members=total_members,
                           total_issued=total_issued,
                           overdue=overdue)


if __name__ == '__main__':
    app.run(debug=True)
