FROM node:24-alpine
ENV NODE_ENV=production
RUN install -d -o node -g node /data
WORKDIR /srv
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force
# .deployed (written by deploy-tool deploy) after the install, so a new commit does not re-run npm
COPY .deployed* ./
COPY src/ src/
COPY static/ static/
USER node
EXPOSE 8000
CMD ["node", "src/server.mjs"]
