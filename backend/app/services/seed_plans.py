"""Seed default subscription plans into the database."""

import logging
from app.database.db import SessionLocal
from app.models.subscription import SubscriptionPlan

logger = logging.getLogger(__name__)

DEFAULT_PLANS = [
    {
        "name": "Free",
        "description": "Basic access to get started with limited features",
        "price_monthly": 0,
        "price_annual": 0,
        "sort_order": 0,
        "is_admin_plan": False,
        "is_public": True,
        "features": {
            "deep_research": False,
            "deep_thinking": False,
            "image_generation": False,
            "code_agent": False,
            "rag": True,
            "voice": True,
            "web_search": False,
        },
        "limits": {
            "chat_messages_per_day": 20,
            "chat_tokens_per_day": 10000,
            "deep_research_per_month": 0,
            "deep_thinking_per_month": 0,
            "image_gen_per_month": 0,
            "code_executions_per_month": 0,
            "rag_documents": 3,
            "web_search_per_day": 0,
            "max_tokens_per_response": 1024,
            "max_context_length": 4096,
        },
    },
    {
        "name": "Starter",
        "description": "For casual users who need more capabilities",
        "price_monthly": 199,
        "price_annual": 1990,
        "sort_order": 1,
        "is_admin_plan": False,
        "is_public": True,
        "features": {
            "deep_research": True,
            "deep_thinking": True,
            "image_generation": True,
            "code_agent": True,
            "rag": True,
            "voice": True,
            "web_search": True,
        },
        "limits": {
            "chat_messages_per_day": 100,
            "chat_tokens_per_day": 50000,
            "deep_research_per_month": 25,
            "deep_thinking_per_month": 50,
            "image_gen_per_month": 25,
            "code_executions_per_month": 50,
            "rag_documents": 10,
            "web_search_per_day": 20,
            "max_tokens_per_response": 2048,
            "max_context_length": 8192,
        },
    },
    {
        "name": "Pro",
        "description": "For power users and professionals",
        "price_monthly": 499,
        "price_annual": 4990,
        "sort_order": 2,
        "is_admin_plan": False,
        "is_public": True,
        "features": {
            "deep_research": True,
            "deep_thinking": True,
            "image_generation": True,
            "code_agent": True,
            "rag": True,
            "voice": True,
            "web_search": True,
        },
        "limits": {
            "chat_messages_per_day": 500,
            "chat_tokens_per_day": 250000,
            "deep_research_per_month": 100,
            "deep_thinking_per_month": 200,
            "image_gen_per_month": 100,
            "code_executions_per_month": 200,
            "rag_documents": 50,
            "web_search_per_day": 100,
            "max_tokens_per_response": 4096,
            "max_context_length": 16000,
        },
    },
    {
        "name": "Max",
        "description": "Maximum power for demanding workloads",
        "price_monthly": 999,
        "price_annual": 9990,
        "sort_order": 3,
        "is_admin_plan": False,
        "is_public": True,
        "features": {
            "deep_research": True,
            "deep_thinking": True,
            "image_generation": True,
            "code_agent": True,
            "rag": True,
            "voice": True,
            "web_search": True,
        },
        "limits": {
            "chat_messages_per_day": 2000,
            "chat_tokens_per_day": 1000000,
            "deep_research_per_month": 500,
            "deep_thinking_per_month": 1000,
            "image_gen_per_month": 500,
            "code_executions_per_month": 1000,
            "rag_documents": 200,
            "web_search_per_day": 500,
            "max_tokens_per_response": 8192,
            "max_context_length": 32000,
        },
    },
    {
        "name": "Enterprise",
        "description": "Unlimited everything — admin assigned only",
        "price_monthly": 0,
        "price_annual": 0,
        "sort_order": 99,
        "is_admin_plan": True,
        "is_public": False,
        "features": {
            "deep_research": True,
            "deep_thinking": True,
            "image_generation": True,
            "code_agent": True,
            "rag": True,
            "voice": True,
            "web_search": True,
        },
        "limits": {
            "chat_messages_per_day": 999999,
            "chat_tokens_per_day": 999999999,
            "deep_research_per_month": 999999,
            "deep_thinking_per_month": 999999,
            "image_gen_per_month": 999999,
            "code_executions_per_month": 999999,
            "rag_documents": 999999,
            "web_search_per_day": 999999,
            "max_tokens_per_response": 99999,
            "max_context_length": 999999,
        },
    },
]


def seed_plans():
    """Insert default plans if they don't already exist."""
    db = SessionLocal()
    try:
        existing = db.query(SubscriptionPlan).count()
        if existing > 0:
            logger.info(f"Plans already seeded ({existing} plans found), skipping")
            return

        for plan_data in DEFAULT_PLANS:
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)

        db.commit()
        msg = f"Seeded {len(DEFAULT_PLANS)} default subscription plans"
        logger.info(msg)
        print(f"[seed] {msg}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed plans: {e}")
        print(f"[seed] FAILED: {e}")
    finally:
        db.close()
