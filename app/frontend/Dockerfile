# Classifieds Pro — frontend image (static build served by nginx, /api proxied to backend)
# Build from the REPOSITORY ROOT:  docker build -f app/frontend/Dockerfile .
FROM node:20-alpine AS build

WORKDIR /app
COPY app/frontend/package.json app/frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY app/frontend ./
# "/api" makes the browser call the same origin; nginx proxies it to the backend.
ARG REACT_APP_API_URL=/api
ENV REACT_APP_API_URL=$REACT_APP_API_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY app/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
