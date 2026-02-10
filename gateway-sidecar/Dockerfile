FROM node:20-alpine AS build

WORKDIR /app

ARG CLOUDSMITH_TOKEN
ENV CLOUDSMITH_TOKEN=$CLOUDSMITH_TOKEN

COPY .npmrc package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:20-alpine

WORKDIR /app
ENV NODE_ENV=production

COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json package-lock.json ./

EXPOSE 4010
CMD ["node", "dist/server.js"]
