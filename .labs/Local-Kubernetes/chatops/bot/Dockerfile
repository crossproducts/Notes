FROM node:22-alpine

RUN apk add --no-cache curl

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

USER node

CMD ["node", "dist/index.js"]
