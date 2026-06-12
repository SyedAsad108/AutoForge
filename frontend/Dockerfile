FROM node:20-alpine

WORKDIR /app

# Copy package files first to leverage Docker cache
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server, binding to 0.0.0.0 so it is accessible outside the container
CMD ["npm", "run", "dev", "--", "--host"]
