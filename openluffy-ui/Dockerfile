# Build
FROM node:22-alpine AS build
WORKDIR /app
COPY openluffy-ui/package*.json ./
RUN npm ci
COPY openluffy-ui/ .
RUN npm run build

# Serve
FROM nginx:alpine
COPY openluffy-ui/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
