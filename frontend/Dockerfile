FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

ARG VITE_API_URL=http://localhost:8010/api/v1
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

EXPOSE 5173

# Render free-tier sets $PORT=10000; vite preview must listen on $PORT
CMD ["sh", "-c", "npm run preview -- --host 0.0.0.0 --port ${PORT:-5173}"]