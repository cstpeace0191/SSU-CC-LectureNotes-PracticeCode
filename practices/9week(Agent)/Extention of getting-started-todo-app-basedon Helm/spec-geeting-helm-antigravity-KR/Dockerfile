###################################################
# Stage: base
###################################################
FROM node:22-alpine AS base
WORKDIR /usr/local/app
RUN apk add --no-cache python3 make g++

################## CLIENT STAGES ##################
FROM base AS client-base
COPY client/package.json ./
RUN npm install
COPY client/index.html client/vite.config.js client/.eslintrc.cjs ./
COPY client/src ./src

FROM client-base AS client-build
RUN npm run build

################## BACKEND STAGES #################
FROM base AS backend-dev
COPY backend/package.json ./
RUN npm install
COPY backend/src ./src
COPY backend/spec ./spec

FROM backend-dev AS test
RUN npm test

################## FINAL PRODUCTION STAGE #########
FROM node:22-alpine AS final
WORKDIR /usr/local/app
ENV NODE_ENV=production
COPY backend/package.json ./
RUN npm install --omit=dev && npm cache clean --force
COPY backend/src ./src
COPY --from=client-build /usr/local/app/dist ./src/static
EXPOSE 3000
CMD ["node", "src/index.js"]

