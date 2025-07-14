from flask import Flask, flash, redirect, render_template, request, session, url_for, make_response, jsonify, get_flashed_messages
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from helpf import login_required, usd, budget
from flask_migrate import Migrate
from sqlalchemy import desc
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os


db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Configurations
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    app.secret_key = "you"
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'lifebudget.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    Session(app)
    db.init_app(app)
    migrate.init_app(app, db)

    app.jinja_env.filters["usd"] = usd

    return app

app = create_app()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    hash = db.Column(db.Text, nullable=False)
    income = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class custom_Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_name = db.Column(db.Text)
    category = db.Column(db.Text, nullable=False)
    budgeted = db.Column(db.Float, default=0.0)
    spent = db.Column(db.Float, default=0.0)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.Date, default=datetime.utcnow)
    updated_at = db.Column(db.Date, onupdate=datetime.utcnow)
    end_at = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)



class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Null for predefined goals
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    term = db.Column(db.String(50), nullable=False)
    custom_term = db.Column(db.String(50), nullable=True)  # Custom term if applicable
    status = db.Column(db.String(50), default="Not Started")  #  "Not Started", "In Progress", "Completed"
    beging_date = db.Column(db.Date, default=datetime.utcnow)  #I add it to now when I ask the use to make a new one
    end_date = db.Column(db.Date) #beging_date + term or custom_term

def add_predefined_goals():
    predefined_goals = [
        {"name": "Emergency Fund", "target_amount": 1000, "term": "3 month"},
        {"name": "Vacation Savings", "target_amount": 2000, "term": "6 month"},
        {"name": "New Car", "target_amount": 10000, "term": "12 month"}
    ]
    for goal in predefined_goals:
        if not Goal.query.filter_by(name=goal["name"]).first():
            newgoal = Goal(name=goal["name"], target_amount=goal["target_amount"], term=goal["term"])
            db.session.add(newgoal)
        db.session.commit()

@app.route('/')
@login_required
def home():
    user_id = session["user_id"]
    user = User.query.filter_by(id=user_id).first()
    user_plan = custom_Budget.query.filter_by(user_id=user_id, is_active=True).all()
    user_goal = Goal.query.filter_by(user_id=user_id, status = "In Progress").first()
    if not user_plan:
        return redirect(url_for("generat_budget"))
    for plan in user_plan:
            if plan.end_at <= datetime.now().date():
                plan.is_active = False
                if user_goal:
                    user_goal.status = "Completed"
    db.session.commit()
    user_plan = custom_Budget.query.filter_by(user_id=user_id, is_active=True).all()
    if not user_plan:
        return redirect(url_for("generat_budget"))

    for plan in user_plan:
        time_to_spint = plan.created_at +  relativedelta(months=1)
        if time_to_spint <= datetime.now().date():
            plan.spent = 0
    db.session.commit()
    budgets = [
            {
            "category": plan.category,
            "budget": (plan.budgeted),
            "spent": (plan.spent),
            "percentage": (plan.budgeted / user.income) * 100,
            "remaining": (plan.budgeted - plan.spent)
            }
            for plan in user_plan
    ]
    return render_template("index.html", budgets=budgets, income=user.income)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.hash, password):
            flash("Invalid username or password. Please try again.", "danger")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        response = make_response(redirect(url_for("home")))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        return response
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if len(password) < 4:
            flash("Password must be at least 4 characters", "danger")
            return redirect(url_for("register"))
        if password != confirmation:
            flash("Passwords do not match", "danger")
            return redirect(url_for("register"))
        if len(username) > 50:
            flash("Username cannot be more than 50 characters", "danger")
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = new_user.id
        response = make_response(redirect(url_for("home")))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        return response

    return render_template("register.html")



@app.route('/generat_budget', methods=['POST','GET'])
@login_required
def generat_budget():
    main_goals = Goal.query.filter_by(user_id=None).all()
    if request.method == "POST":
        user = User.query.filter_by(id=session["user_id"]).first()
        income = request.form.get("income")
        fixed = request.form.get("FixedExpenses")
        var = request.form.get("VariableExpenses")
        user_goal = request.form.get("goal")
        if user_goal == "custom":
            goal_name = request.form.get("name")
            goal_target = request.form.get("target_amount")
            goal_timeamount = int(request.form.get("term"))
            time_type = request.form.get("time")
            transform = {"month": 1, "day": 1 / 30, "year": 12, "week": 1 / 4.3}
            months_to_add = round(goal_timeamount * transform[time_type])
            end_date = datetime.now() + relativedelta(months=months_to_add)
            goal = Goal(name=goal_name,
                        target_amount=goal_target,
                        term = f"{months_to_add} month",
                        user_id=user.id,
                        end_date=end_date)
        else:
            user_mian_goal = Goal.query.filter_by(name=user_goal, user_id=None).first()
            time_amount = int(user_mian_goal.term.split()[0])
            end_date = datetime.now() +  relativedelta(months=time_amount)
            goal = Goal(name=user_mian_goal.name
                        ,target_amount=user_mian_goal.target_amount,
                        term=user_mian_goal.term,
                        user_id=user.id,
                        status = "In Progress",
                        end_date=end_date)
        end_user_goal = Goal.query.filter_by(user_id=user.id, status="In Progress").first()
        if end_user_goal:
            end_user_goal.status = "Completed"
        db.session.add(goal)
        user.income = float(income)
        db.session.commit()

        budget_plan = budget(income, fixed, goal.term, var, user.id, goal.target_amount)
        print(budget_plan)
        if budget_plan == "impossible":
            flash("It is impossible to create a plan for your target with the current income and term. Please adjust your target, increase your income, or extend your term.", "danger")
            return render_template("generat_plan.html", goals=main_goals)
        if type(budget_plan) == tuple:
            flash(f"Your selected plan will allocate {budget_plan[0] * 100}% of your remaining income. Please review your budget to ensure this aligns with your financial goals.", "warning")
            db.session.add_all(budget_plan[1])
        else:
            db.session.add_all(budget_plan)
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("generat_plan.html", goals=main_goals)


@app.route('/deletBudget',  methods=['GET'])
@login_required
def deletBudget():
    user_id = session["user_id"]
    user_budget = custom_Budget.query.filter_by(user_id=user_id, is_active=True).all()
    user_goal = Goal.query.filter_by(user_id=user_id, status="In Progress").first()
    for plan in user_budget:
        plan.is_active = False
    if user_goal:
        user_goal.status = "Completed"
    db.session.commit()
    return redirect(url_for("home"))


@app.route('/history',  methods=['GET'])
@login_required
def show_history():
    old_budgets = custom_Budget.query.filter_by(user_id=session["user_id"], is_active=False).all()
    income = User.query.filter_by(id=session["user_id"]).first().income

    if old_budgets:
        old_plan = {}
        for old_budget in old_budgets:
            old_plan.setdefault(old_budget.plan_name, []).append(old_budget)
        old_plan_json = []
        for plan_name, budgets in old_plan.items():
            old_plan_json.append({
                "plan_name": plan_name,
                "budgets": [
                    {
                        "category": budget.category,
                        "budget": float(budget.budgeted),
                        "spent": float(budget.spent),
                        "percentage": round((budget.budgeted / income) * 100, 2),
                        "remaining": float(budget.budgeted - budget.spent),
                    }
                    for budget in budgets
                ]
            })

        return render_template("history.html", plans=old_plan_json)


    return render_template("history.html", plans=[])


@app.route('/add_spent', methods=['POST'])
@login_required
def add_spent():
    data = request.json
    category = data.get('category')
    amount = data.get('amount')
    user_id = session["user_id"]

    budget_entry = custom_Budget.query.filter_by(user_id=user_id, category=category, is_active=True).first()
    if budget_entry:
        budget_entry.spent += amount
        db.session.commit()
        return jsonify({"message": f"Added ${amount:.2f} to {category}."}), 200
    return jsonify({"message": "Budget category not found."}), 404




@app.route('/edit_budget', methods=['GET', 'POST'])
@login_required
def edit_budget():
    budgets = custom_Budget.query.filter_by(user_id=session["user_id"], is_active=True).all()
    goal = Goal.query.filter_by(user_id=session["user_id"], status="In Progress").first()
    target_in_month = goal.target_amount / int(goal.term.split(" ")[0])
    income = User.query.filter_by(id=session["user_id"]).first().income

    if request.method == 'POST':
            total_budget = 0

            # Process removed categories
            if 'removeCategory[]' in request.form:
                 remove_categories = request.form.getlist('removeCategory[]')
                 for category in remove_categories:
                     custom_budget = custom_Budget.query.filter_by(user_id=session["user_id"], category=category, is_active=True).first()
                     if custom_budget:
                            db.session.delete(custom_budget)

            # Process updated and new budgets
            for category, budget in request.form.items():
                if category.startswith("budgets["):
                    category_name = category.split('[')[1].rstrip(']')
                    try:
                        budget_value = float(budget)
                        if budget_value < 0:
                            flash(f"Budget for {category_name} cannot be negative.", "danger")
                            return redirect(url_for('edit_budget'))
                        for budget in budgets:
                            if budget.category == category_name:
                                if budget.category == "savings" and budget.budgeted > budget_value:
                                    flash(f"Savings budget of ${savings:.2f} is below your goal of ${target_in_month:.2f}.", "danger")
                                    return redirect(url_for('edit_budget'))
                                budget.budgeted = budget_value
                                total_budget += budget_value
                    except ValueError:
                        flash(f"Invalid budget value for {category_name}.", "danger")
                        return redirect(url_for('edit_budget'))

            new_categories = request.form.getlist('newCategory[]')
            new_budgets = request.form.getlist('newBudget[]')
            for category, budget in zip(new_categories, new_budgets):
                if category and budget:
                    try:
                        budget_value = float(budget)
                        if budget_value < 0:
                            flash(f"Budget for new category {category} cannot be negative.", "danger")
                            return redirect(url_for('edit_budget'))
                        if any(b.category == category for b in budgets):
                            flash(f"Category {category} already exists.", "danger")
                            return redirect(url_for('edit_budget'))

                        new_budget = custom_Budget(plan_name=budgets[0].plan_name,
                                                   user_id=session["user_id"],
                                                   category=category,
                                                   budgeted=budget_value,
                                                   end_at=budgets[0].end_at,
                                                   created_at=budgets[0].created_at)
                        db.session.add(new_budget)
                        total_budget += budget_value
                    except ValueError:
                        flash(f"Invalid budget value for new category {category}.", "danger")
                        return redirect(url_for('edit_budget'))

            if total_budget > income+2:
                flash(f"Total budget of ${total_budget:.2f} exceeds your income of ${income:.2f}.", "danger")
                return redirect(url_for('edit_budget'))

            db.session.commit()
            flash("Budget plan updated successfully!", "success")
            return redirect(url_for('home'))


    return render_template('edit_budget.html', budgets=budgets, user_income=income, savings_goal=target_in_month)


@app.route('/delete_category', methods=['POST'])
@login_required
def delete_category():

    data = request.get_json()
    category = data.get("category")

    if not category:
        return jsonify({"error": "Category name is required"}), 400

    budget_to_delete = custom_Budget.query.filter_by(user_id=session["user_id"], category=category, is_active=True).first()

    if budget_to_delete:
        db.session.delete(budget_to_delete)
        db.session.commit()
        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "Category not found"}), 404



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Tables created!")
        add_predefined_goals()

    app.run(debug=True)
