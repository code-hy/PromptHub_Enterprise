FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

ENV VITE_API_URL=http://localhost:8010/api/v1

RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]