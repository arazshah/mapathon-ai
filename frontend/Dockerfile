FROM public.ecr.aws/docker/library/node:22-bookworm-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm ci --no-audit --no-fund

COPY . .

ARG VITE_API_URL=https://api.mapathon.ir
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build


FROM public.ecr.aws/docker/library/nginx:alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
