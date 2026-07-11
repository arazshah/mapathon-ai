FROM docker.abrha.net/library/node:24-bookworm-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./

RUN node --version \
    && npm --version \
    && npm config set fetch-retries 5 \
    && npm config set fetch-retry-factor 2 \
    && npm config set fetch-retry-mintimeout 10000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && npm ci --no-audit --no-fund

COPY . .

ARG VITE_API_URL=https://api.mapathon.ir
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build


FROM docker.abrha.net/library/nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
