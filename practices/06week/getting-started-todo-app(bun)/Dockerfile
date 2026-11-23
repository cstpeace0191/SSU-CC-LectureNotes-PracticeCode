###################################################
# Stage: base
# 
# This base stage ensures all other stages are using the same Bun base image
# and provides common configuration for all stages, such as the working dir.
###################################################
FROM oven/bun:1 AS base
WORKDIR /usr/local/app

################## CLIENT STAGES ##################

###################################################
# Stage: client-base
#
# This stage is used as the base for the client-dev and client-build stages,
# since there are common steps needed for each.
###################################################
FROM base AS client-base
COPY client/package.json client/bun.lock* ./
RUN bun install
COPY client/index.html client/vite.config.ts client/tsconfig.json ./
COPY client/public ./public
COPY client/src ./src

###################################################
# Stage: client-dev
# 
# This stage is used for development of the client application. It sets 
# the default command to start the Vite development server.
###################################################
FROM client-base AS client-dev
CMD ["bun", "run", "dev"]

###################################################
# Stage: client-build
#
# This stage builds the client application, producing static HTML, CSS, and
# JS files that can be served by the backend.
###################################################
FROM client-base AS client-build
RUN bun run build

###################################################
################  BACKEND STAGES  #################
###################################################

###################################################
# Stage: backend-dev
#
# This stage is used as the base for the backend-dev and test stages, since
# there are common steps needed for each.
###################################################
FROM base AS backend-dev
COPY backend/package.json backend/bun.lock* backend/tsconfig.json ./
RUN bun install
COPY backend/spec ./spec
COPY backend/src ./src
CMD ["bun", "run", "dev"]

###################################################
# Stage: test
#
# This stage runs the tests on the backend using Bun test runner.
###################################################
FROM backend-dev AS test
RUN bun test

###################################################
# Stage: final
#
# This stage is intended to be the final "production" image. It sets up the
# backend and copies the built client application from the client-build stage.
###################################################
FROM base AS final
ENV NODE_ENV=production
WORKDIR /usr/local/app
COPY --from=test /usr/local/app/package.json /usr/local/app/bun.lock* /usr/local/app/tsconfig.json ./
RUN bun install --production
COPY backend/src ./src
COPY --from=client-build /usr/local/app/dist ./src/static
EXPOSE 3000
CMD ["bun", "src/index.ts"]
