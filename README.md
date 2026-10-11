# Smart Restaurant Review & Service Analytics System

A complete PBL-ready enterprise decision support web application integrating:
- ITPM: project planning, KPIs, risks, roles, reports
- ES: centralized restaurant/customer/review/employee/order management
- ASMA: descriptive statistics, sentiment analysis, trends, branch comparison and recommendations

## Technology
Python, Flask, SQLAlchemy, SQLite for local development, Neon PostgreSQL for hosted deployment, Bootstrap 5, Chart.js, ReportLab.

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

## Local demo accounts
These accounts are for local development only and must not be used for a public deployment.
- Admin: admin@smartrest.com / admin123
- Manager: manager@smartrest.com / manager123
- Customer: customer@smartrest.com / customer123

For hosted demo-data seeding, configure `DEMO_ADMIN_PASSWORD`, `DEMO_MANAGER_PASSWORD`, and `DEMO_CUSTOMER_PASSWORD` as strong, distinct environment variables.

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

## Free hosting: Render + Neon

The repository includes `render.yaml`, `.python-version`, and `.gitignore` for deployment. The hosted app reads its PostgreSQL connection string from `DATABASE_URL` and its Flask session secret from `SECRET_KEY`. Never commit either value.

1. Create a free PostgreSQL project on Neon and copy its connection string with SSL enabled.
2. Push this project to a GitHub repository (do not commit `instance/restaurant.db`, `.env`, or your virtual environment).
3. In Render, create a Web Service from that repository and use the included `render.yaml` settings.
4. Add `DATABASE_URL` and a long, random `SECRET_KEY` in Render's environment settings.
5. If you want the included sample restaurants/reviews, temporarily set `SEED_DEMO_DATA=true` and set strong, distinct values for all three `DEMO_*_PASSWORD` variables before the first deployment. Once the initial data exists, set `SEED_DEMO_DATA=false`. Existing database rows are not overwritten by seeding.
6. Verify login, reviews, analytics, and CSV/PDF reports using the public HTTPS URL.

**Free-tier caveat:** Render free web services sleep after inactivity and use an ephemeral filesystem. The Neon database is used so application records do not depend on that filesystem. Free plans and limits can change; check the provider's current terms.
