FROM node:22-alpine AS build

# Set working directory
WORKDIR /app

# Set build args as env vars
ARG REACT_APP_BACKEND_URL
ARG REACT_APP_API_KEY
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV REACT_APP_API_KEY=$REACT_APP_API_KEY

# Install dependencies
COPY package.json package-lock.json ./
RUN npm ci

# Copy project files
COPY . .

# Build the app
RUN npx react-scripts build

FROM nginx:alpine

# Copy built app to nginx
COPY --from=build /app/build /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
