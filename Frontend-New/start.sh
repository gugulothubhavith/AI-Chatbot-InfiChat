#!/bin/sh
# Start the TanStack Start (Nitro) SSR server in the background
export PORT=3000
node .output/server/index.mjs &

# Start Nginx in the foreground to proxy requests to Node and Backend
nginx -g "daemon off;"
