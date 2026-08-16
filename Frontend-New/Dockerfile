# Build stage
FROM node:22-slim AS build
WORKDIR /app
COPY package*.json bun.lock* ./
RUN npm install --legacy-peer-deps
COPY . .
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_GOOGLE_CLIENT_ID="598862026816-4cnrdb6k5jpvvh2lhfo1mltk2mo9ut7g.apps.googleusercontent.com"

# ── Company identity ────────────────────────────────────────────────────────
# Read by src/lib/brand.ts and printed on invoices.
#
# These are build args rather than runtime environment because Vite inlines
# `import.meta.env.VITE_*` into the bundle at build time. Setting them on the
# *container* would have no effect whatsoever — the strings are already
# compiled in — so they have to be supplied here, via `build.args` in
# docker-compose.yml.
#
# Left empty on purpose. `brand.ts` detects a missing legal entity and makes
# the invoice generator stamp the PDF as a DRAFT, which is the correct default
# for a deployment that has not been told who it is. A plausible-looking
# placeholder address baked in here would be far worse: it would print on
# documents customers file for tax without anything flagging it.
ARG VITE_APP_NAME="InfiChat"
ARG VITE_APP_TAGLINE="AI assistant for teams"
ARG VITE_LEGAL_ENTITY_NAME=""
ARG VITE_LEGAL_ADDRESS=""
ARG VITE_LEGAL_REGISTRATION_NUMBER=""
ARG VITE_LEGAL_TAX_ID=""
ARG VITE_PUBLIC_WEBSITE="infichat.ai"
ARG VITE_BILLING_EMAIL="billing@infichat.ai"
ARG VITE_SUPPORT_EMAIL="support@infichat.ai"
ARG VITE_PRIVACY_EMAIL="privacy@infichat.ai"
ARG VITE_SECURITY_EMAIL="security@infichat.ai"
ARG VITE_PAYMENT_PROCESSOR="Stripe"

ENV VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_APP_TAGLINE=${VITE_APP_TAGLINE} \
    VITE_LEGAL_ENTITY_NAME=${VITE_LEGAL_ENTITY_NAME} \
    VITE_LEGAL_ADDRESS=${VITE_LEGAL_ADDRESS} \
    VITE_LEGAL_REGISTRATION_NUMBER=${VITE_LEGAL_REGISTRATION_NUMBER} \
    VITE_LEGAL_TAX_ID=${VITE_LEGAL_TAX_ID} \
    VITE_PUBLIC_WEBSITE=${VITE_PUBLIC_WEBSITE} \
    VITE_BILLING_EMAIL=${VITE_BILLING_EMAIL} \
    VITE_SUPPORT_EMAIL=${VITE_SUPPORT_EMAIL} \
    VITE_PRIVACY_EMAIL=${VITE_PRIVACY_EMAIL} \
    VITE_SECURITY_EMAIL=${VITE_SECURITY_EMAIL} \
    VITE_PAYMENT_PROCESSOR=${VITE_PAYMENT_PROCESSOR}

ENV NITRO_PRESET=node-server
RUN npm run build

# Production stage — serve the SSR app with Node and Nginx
FROM node:22-slim
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/* && rm -f /etc/nginx/sites-enabled/default
WORKDIR /app
COPY --from=build /app/.output ./.output
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Copy start script
COPY start.sh /start.sh
RUN chmod +x /start.sh
EXPOSE 80
CMD ["/start.sh"]
