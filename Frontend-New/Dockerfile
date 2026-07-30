# Build stage
FROM node:22-slim AS build
WORKDIR /app
COPY package*.json bun.lock* ./
RUN npm install --legacy-peer-deps
COPY . .
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_GOOGLE_CLIENT_ID="598862026816-4cnrdb6k5jpvvh2lhfo1mltk2mo9ut7g.apps.googleusercontent.com"
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
