# Build
FROM node:22-alpine AS build
WORKDIR /app
COPY lebrickbot-ui/package*.json ./
RUN npm ci
COPY lebrickbot-ui/ .
RUN npm run build

# Serve
FROM nginx:alpine
COPY lebrickbot-ui/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
