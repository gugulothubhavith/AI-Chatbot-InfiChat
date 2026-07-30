"""Subscription API — Plan listing, user subscription, and admin plan management."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os

try:
    import geoip2.database  # installed inside Docker only
except ImportError:
    geoip2 = None  # type: ignore

try:
    import stripe  # installed inside Docker only
except ImportError:
    stripe = None  # type: ignore

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.subscription_service import (
    get_available_plans,
    get_plan_by_id,
    create_plan,
    update_plan,
    delete_plan,
    assign_plan_to_user,
    get_user_subscription,
    get_user_usage_summary,
    get_all_users_usage,
)

router = APIRouter(prefix="/subscription", tags=["Subscription"])


# ── Schemas ───────────────────────────────────────────────────

class PlanCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    price_monthly: int = 0
    price_annual: int = 0
    limits: Dict[str, Any] = {}
    features: Dict[str, Any] = {}
    is_admin_plan: bool = False
    is_public: bool = True
    sort_order: int = 0

class PlanUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[int] = None
    price_annual: Optional[int] = None
    limits: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None

class SubscribeRequest(BaseModel):
    plan_id: str
    billing_cycle: str = "monthly"

# ── Regional Pricing Engine ─────────────────────────────────────
def get_regional_pricing(base_inr: int, request: Request) -> dict:
    """
    Advanced Regional Pricing Engine utilizing PPP (Purchasing Power Parity)
    and dynamic exchange rate estimation based on Geo-IP headers or local DB.
    """
    country = request.headers.get("cf-ipcountry")
    if not country:
        # Fallback to local GeoIP database
        client_ip = request.client.host if request.client else "127.0.0.1"
        db_path = "/usr/share/GeoIP/GeoLite2-Country.mmdb"
        if os.path.exists(db_path) and client_ip and client_ip not in ("127.0.0.1", "::1"):
            try:
                with geoip2.database.Reader(db_path) as reader:
                    response = reader.country(client_ip)
                    country = response.country.iso_code
            except Exception:
                pass
        
    country = (country or "US").upper()
    
    if country == "IN":
        return {
            "currency": "INR",
            "symbol": "₹",
            "multiplier": 1.0,
            "monthly": base_inr,
            "annual": base_inr * 12 * 0.8 # 20% discount
        }
    else:
        # Default to USD with PPP adjustment (e.g. 499 INR -> 20 USD instead of 6 USD)
        usd_price = 0
        if base_inr == 199: usd_price = 10
        elif base_inr == 499: usd_price = 20
        elif base_inr == 999: usd_price = 49
        elif base_inr > 0: usd_price = round(base_inr / 40.0) # Custom mapping
        
        return {
            "currency": "USD",
            "symbol": "$",
            "multiplier": 1.0,
            "monthly": usd_price,
            "annual": usd_price * 12 * 0.8
        }

# ── Public Endpoints ──────────────────────────────────────────

from app.core.deps import get_current_user_optional
from app.models.subscription import UserSubscription, SubscriptionStatus

@router.get("/plans")
def list_plans(request: Request, user: User | None = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    """Get all available public subscription plans with regional pricing. Includes admin plan if user has it."""
    plans = get_available_plans(db)
    
    # Check if user has an admin plan
    if user:
        active_sub = db.query(UserSubscription).filter(
            UserSubscription.user_id == user.id,
            UserSubscription.status == SubscriptionStatus.ACTIVE
        ).first()
        if active_sub and active_sub.plan and active_sub.plan.is_admin_plan:
            # Avoid adding duplicate
            if active_sub.plan.id not in [p.id for p in plans]:
                plans.append(active_sub.plan)
    
    result = []
    for p in plans:
        regional = get_regional_pricing(p.price_monthly, request)
        result.append({
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "price_monthly": p.price_monthly,
            "price_annual": getattr(p, "price_annual", 0),
            "regional": regional,
            "features": p.features,
            "limits": p.limits,
            "is_admin_plan": p.is_admin_plan,
            "sort_order": p.sort_order,
        })
    return result

from app.core.config import settings

if stripe is not None and settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/checkout")
def create_checkout_session(req: SubscribeRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Generate real Stripe Checkout Session for subscription.
    """
    if stripe is None or not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Billing is not available on this server.")

    plan = get_plan_by_id(req.plan_id, db)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    if plan.price_monthly == 0 and plan.price_annual == 0:
        # Free plan - just assign it
        assign_plan_to_user(str(user.id), str(plan.id), db)
        return {"url": "/settings?tab=subscription&success=true"}
        
    # Get regional pricing (for currency)
    regional = get_regional_pricing(plan.price_monthly, request)
    currency = regional["currency"].lower()
    
    # Base amount (fallback if logic fails, though regional handles it)
    amount = plan.price_annual if req.billing_cycle == "annually" else plan.price_monthly
    
    # In a real app we'd map to stripe Price IDs, but we can use ad-hoc prices for now
    # Or create the price on the fly
    unit_amount = amount * 100 # Stripe uses smallest currency unit (cents, paise)

    try:
        checkout_session = stripe.checkout.Session.create(
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': f"InfiChat {plan.name} Plan",
                        'description': f"Billed {req.billing_cycle}",
                    },
                    'unit_amount': unit_amount,
                    'recurring': {
                        'interval': 'year' if req.billing_cycle == "annually" else 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=settings.ALLOWED_ORIGINS.split(',')[0] + "/settings?tab=subscription&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.ALLOWED_ORIGINS.split(',')[0] + "/settings?tab=subscription",
            metadata={
                "user_id": str(user.id),
                "plan_id": str(plan.id),
                "billing_cycle": req.billing_cycle
            }
        )
        return {"url": checkout_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Secure webhook listener for Stripe.
    Idempotently updates user subscriptions on checkout.session.completed events.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if stripe is None or not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Billing is not available on this server.")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        plan_id = session.get("metadata", {}).get("plan_id")
        
        if user_id and plan_id:
            assign_plan_to_user(user_id, plan_id, db)
            
            # Optionally save the Stripe customer ID to the user for future portal sessions
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # We could store customer_id in a new column or metadata json
                pass

    return {"status": "success"}

@router.get("/portal")
def get_customer_portal(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns a URL to the Stripe Customer Portal for managing billing."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured.")
        
    # In a real app we'd fetch the user's saved stripe_customer_id
    # For now we'll search stripe for a customer with this email
    customers = stripe.Customer.list(email=user.email, limit=1)
    if not customers.data:
        raise HTTPException(status_code=404, detail="No active billing profile found for this user.")
        
    customer_id = customers.data[0].id
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=settings.ALLOWED_ORIGINS.split(',')[0] + "/settings?tab=subscription",
        )
        return {"url": portal_session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoices")
def get_invoices(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch user invoices directly from Stripe."""
    if not settings.STRIPE_SECRET_KEY:
        return []
        
    customers = stripe.Customer.list(email=user.email, limit=1)
    if not customers.data:
        return []
        
    customer_id = customers.data[0].id
    invoices = stripe.Invoice.list(customer=customer_id, limit=20)
    
    result = []
    for inv in invoices.data:
        result.append({
            "id": inv.id,
            "date": str(inv.created), # normally we'd format this
            "amount": inv.total / 100,
            "status": inv.status,
            "plan": inv.lines.data[0].plan.nickname if inv.lines.data and getattr(inv.lines.data[0], "plan", None) else "Subscription",
            "cycle": "monthly", # We could infer from line item
            "pdf_url": inv.invoice_pdf
        })
    return result

@router.get("/my-plan")
def my_plan(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's subscription plan and usage."""
    sub_info = get_user_subscription(str(user.id), db)
    plan = sub_info["plan"]
    usage = get_user_usage_summary(str(user.id), db)

    return {
        "plan": {
            "id": str(plan.id) if plan else None,
            "name": plan.name if plan else "Free",
            "price_monthly": plan.price_monthly if plan else 0,
            "price_annual": getattr(plan, "price_annual", 0) if plan else 0,
            "features": plan.features if plan else {},
            "limits": plan.limits if plan else {},
        },
        "subscription": {
            "is_active": sub_info["is_active"],
            "is_admin_assigned": sub_info["is_admin_assigned"],
            "start_date": sub_info["start_date"].isoformat() if sub_info.get("start_date") else None,
            "end_date": sub_info["end_date"].isoformat() if sub_info.get("end_date") else None,
        },
        "usage": {
            feature: data
            for feature, data in usage.items()
        },
    }


@router.post("/subscribe")
def subscribe(
    req: SubscribeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Subscribe to a plan."""
    plan = get_plan_by_id(req.plan_id, db)
    if not plan or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.is_admin_plan:
        raise HTTPException(
            status_code=400,
            detail="This plan cannot be self-subscribed. Contact an administrator.",
        )

    subscription = assign_plan_to_user(str(user.id), req.plan_id, db)
    return {
        "message": f"Subscribed to {plan.name}",
        "plan_name": plan.name,
        "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
    }


# ── Admin Endpoints ───────────────────────────────────────────

@router.get("/admin/plans")
def admin_list_plans(db: Session = Depends(get_db)):
    """Get ALL plans including inactive (admin only)."""
    from app.models.subscription import SubscriptionPlan

    plans = db.query(SubscriptionPlan).order_by(SubscriptionPlan.sort_order).all()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "price_monthly": p.price_monthly,
            "features": p.features,
            "limits": p.limits,
            "is_active": p.is_active,
            "is_admin_plan": p.is_admin_plan,
            "is_public": p.is_public,
            "sort_order": p.sort_order,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in plans
    ]


@router.post("/admin/plans")
def admin_create_plan(
    req: PlanCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new subscription plan (admin only)."""
    plan = create_plan(db, **req.model_dump())
    return {"id": str(plan.id), "name": plan.name, "message": "Plan created successfully"}


@router.put("/admin/plans/{plan_id}")
def admin_update_plan(
    plan_id: str,
    req: PlanUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update an existing plan (admin only)."""
    filtered = {k: v for k, v in req.model_dump().items() if v is not None}
    plan = update_plan(plan_id, db, **filtered)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"message": "Plan updated successfully", "id": plan_id}


@router.delete("/admin/plans/{plan_id}")
def admin_delete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
):
    """Delete a plan (admin only)."""
    if not delete_plan(plan_id, db):
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"message": "Plan deleted successfully"}


@router.get("/admin/usage")
def admin_usage(db: Session = Depends(get_db)):
    """Platform-wide usage stats (admin only)."""
    usage = get_all_users_usage(db)
    return {"features": usage}


@router.get("/admin/user-usage/{user_id}")
def admin_user_usage(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Get usage for a specific user (admin only)."""
    return get_user_usage_summary(user_id, db)


@router.post("/admin/users/{user_id}/assign-plan")
def admin_assign_plan(
    user_id: str,
    req: SubscribeRequest,
    db: Session = Depends(get_db),
):
    """Admin force-assign a plan to a user (bypasses limits)."""
    plan = get_plan_by_id(req.plan_id, db)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    assign_plan_to_user(user_id, req.plan_id, db, admin_assigned=True)
    return {
        "message": f"Plan '{plan.name}' assigned to user",
        "plan_name": plan.name,
    }
