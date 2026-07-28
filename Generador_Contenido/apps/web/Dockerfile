FROM node:22-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
# nginx.conf (API reverse-proxy) is mounted by docker-compose, not baked in here,
# so the build context stays scoped to apps/web.
EXPOSE 80
