# ---- Build stage ----
FROM node:22-slim AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

COPY . .

# Build-time API address. Optional on purpose: leaving it empty produces an
# image that resolves the API at *start* time from config.js instead, which is
# what makes one artifact promotable across environments. Set it only when you
# genuinely want an environment-specific image.
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL

# The repo's .env pins VITE_API_URL to a loopback address for local `npm run
# dev`. It is COPYied in above and Vite would prefer it over the build arg,
# baking 127.0.0.1 into every image — the exact reason the previous build was
# only usable from a browser on the Docker host. Remove it before building.
RUN rm -f .env .env.local .env.production

# Type errors should fail the image, not ship to an operator.
RUN npm run build

# ---- Production stage ----
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY --from=build /app/dist /usr/share/nginx/html

COPY docker-entrypoint.sh /docker-entrypoint.d/40-infichat-config.sh
RUN chmod +x /docker-entrypoint.d/40-infichat-config.sh \
    && sed -i 's/\r$//' /docker-entrypoint.d/40-infichat-config.sh

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
