import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api } from "@/lib/api";

export type Cycle = "monthly" | "annually";

export type PaymentMethod = {
  brand: string;
  last4: string;
  expMonth: number;
  expYear: number;
  holder: string;
};

export type Invoice = {
  id: string;
  date: string;
  amount: number;
  status: "paid" | "open" | "refunded";
  plan: string;
  cycle: Cycle;
};

export type ApiPlan = {
  id: string;
  name: string;
  description: string;
  price_monthly: number;
  price_annual: number;
  regional: {
    currency: string;
    symbol: string;
    multiplier: number;
    monthly: number;
    annual: number;
  };
  features: Record<string, any>;
  limits: Record<string, any>;
};

type BillingState = {
  currentPlanId: string | null;
  availablePlans: ApiPlan[];
  cycle: Cycle;
  paymentMethod: PaymentMethod;
  invoices: Invoice[];
  setCycle: (c: Cycle) => void;
  setPaymentMethod: (m: PaymentMethod) => void;
  hydrate: () => Promise<void>;
  checkout: (plan_id: string, cycle: Cycle) => Promise<void>;
};

export const useBillingStore = create<BillingState>()(
  persist(
    (set, get) => ({
      currentPlanId: null,
      availablePlans: [],
      cycle: "monthly",
      paymentMethod: {
        brand: "",
        last4: "",
        expMonth: 0,
        expYear: 0,
        holder: "",
      },
      invoices: [],
      setCycle: (cycle) => set({ cycle }),
      setPaymentMethod: (paymentMethod) => set({ paymentMethod }),
      hydrate: async () => {
        try {
          const plans = (await api.getPlans()) as ApiPlan[];
          const myPlan = (await api.getMyPlan()) as any;
          set({ 
            availablePlans: plans, 
            currentPlanId: myPlan?.plan?.id || null 
          });
          
          try {
             const invoices = await api.getInvoices() as Invoice[];
             set({ invoices });
          } catch(e) {
             console.log("No invoices found or Stripe not configured");
          }
        } catch (e) {
          console.error("Failed to hydrate billing", e);
        }
      },
      checkout: async (plan_id, cycle) => {
        const res = (await api.checkout(plan_id, cycle)) as any;
        if (res?.url) {
          window.location.href = res.url;
        }
      }
    }),
    { name: "infichat-billing" },
  ),
);
