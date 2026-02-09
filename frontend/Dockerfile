# build
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package*.json frontend/
RUN cd frontend && npm ci
COPY frontend frontend
RUN cd frontend && npm run build

# serve
FROM nginx:alpine
COPY --from=build /app/frontend/dist /usr/share/nginx/html
