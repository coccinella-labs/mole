FROM node:22-alpine AS build

# Set working directory
WORKDIR /app

# Set build args as env vars
ARG VITE_BACKEND_URL
ARG VITE_API_KEY
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL
ENV VITE_API_KEY=$VITE_API_KEY

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy project files
COPY . .

# Build the app
RUN npx vite build

FROM nginx:alpine

# Copy built app to nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
