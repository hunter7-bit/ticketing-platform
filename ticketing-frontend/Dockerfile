# Use a modern, lightweight Node.js image to satisfy Vite's new requirements
FROM node:22-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
# This speeds up your builds significantly if you haven't changed dependencies!
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend source code
COPY . .

# Expose the Vite default port
EXPOSE 5173

# Run the Vite development server
# The --host flag is CRUCIAL in Docker! It tells Vite to expose the app 
# to the outside world (your browser) instead of trapping it inside the container.
CMD ["npm", "run", "dev", "--", "--host"]