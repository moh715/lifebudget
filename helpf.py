import requests

from flask import redirect, render_template, session, flash
from functools import wraps
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta




def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function




def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
def budget(income, fixed, term, variable, user_id, target):
    from app import db, custom_Budget
    variable += .2 * variable
    end_plan = custom_Budget.query.filter_by(user_id=user_id, is_active=False).all()
    Expenses = float(fixed) + float(variable)
    remaining = float(income) - Expenses

    transform = {"month": 1, "day": 1 / 30, "year": 12, "week": 1 / 4.3}
    timeamount = term.split(" ")
    term_in_months = max(1, round(float(timeamount[0]) * transform[timeamount[1].lower()]))

    save = target / term_in_months
    if save > remaining:
        return "impossible"
    saving_percentage = save / remaining
    investment_percentage = 0.7 * (1 - saving_percentage)
    fan_percentage = 1 - (saving_percentage + investment_percentage)
    Expenses_percentage = Expenses/remaining
    categories = {
        "expenses": Expenses_percentage,
        "savings": saving_percentage,
        "fan": fan_percentage,
        "investment": investment_percentage,
    }
    budget_plan = []
    for category, percentage in categories.items():
        budgeted = round(remaining * percentage)
        budget_plan.append(
            custom_Budget(
                user_id=user_id,
                plan_name=f"{user_id} plan {(len(end_plan)/4) + 1}",
                category=category,
                budgeted=budgeted,
                spent=0.0,
                is_public=False,
                end_at = datetime.now() + relativedelta(months=term_in_months)
            )
        )
    if save >= .9 * remaining:
        return (remaining - save)/remaining , budget_plan

    return budget_plan


