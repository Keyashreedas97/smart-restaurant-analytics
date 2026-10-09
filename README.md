# Smart Restaurant Review & Service Analytics System

A complete PBL-ready enterprise decision support web application integrating:
- ITPM: project planning, KPIs, risks, roles, reports
- ES: centralized restaurant/customer/review/employee/order management
- ASMA: descriptive statistics, sentiment analysis, trends, branch comparison and recommendations

## Technology
Python, Flask, SQLite, SQLAlchemy, Bootstrap 5, Chart.js, Pandas, TextBlob, ReportLab.

## Run
1. Install Python 3.10+.
2. Open terminal in this folder.
3. `python -m venv venv`
4. Windows: `venv\Scripts\activate`
5. macOS/Linux: `source venv/bin/activate`
6. `pip install -r requirements.txt`
7. `python app.py`
8. Open http://127.0.0.1:5000

The application automatically creates the database and sample data on first run.

## Demo accounts
Admin: admin@smartrest.com / admin123
Manager: manager@smartrest.com / manager123
Customer: customer@smartrest.com / customer123

## Modules
Customer:
- Submit service review
- View own reviews

Manager:
- Analytics dashboard
- Branch/service KPI monitoring
- Review sentiment
- Decision recommendations
- CSV/PDF reports

Admin:
- Restaurant/branch management
- Employee management
- User/review overview

## PBL Mapping
ITPM -> dashboard KPIs, project plan, risk matrix, role management, reporting.
ES -> enterprise master data, users, branches, employees, reviews, orders.
ASMA -> rating statistics, sentiment, correlations, trends and recommendations.

## Notes
This is an academic/demo project. Change the SECRET_KEY and passwords before any real deployment.
