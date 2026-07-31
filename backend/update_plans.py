import sys
import os
sys.path.append("/app")

from app.database.db import SessionLocal
from app.models.subscription import SubscriptionPlan
from app.services.seed_plans import DEFAULT_PLANS

db = SessionLocal()

for plan_data in DEFAULT_PLANS:
    plan = db.query(SubscriptionPlan).filter_by(name=plan_data["name"]).first()
    if plan:
        plan.price_annual = plan_data["price_annual"]
        plan.limits = plan_data["limits"]
        db.commit()
        print(f"Updated {plan.name}")
    else:
        plan = SubscriptionPlan(**plan_data)
        db.add(plan)
        db.commit()
        print(f"Added {plan.name}")

db.close()
