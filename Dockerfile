# ---- frontend ----
FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi
COPY web/ .
# 匿名 key 可公开；默认写进构建，避免 Render 未配 build-arg / .dockerignore 挡掉 .env.production 时线上登不上。
ARG VITE_SUPABASE_URL=https://ibzfvnzjnapjelxmfidh.supabase.co
ARG VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImliemZ2bnpqbmFwamVseG1maWRoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTU3NDc4MDUsImV4cCI6MjExMTMyMzgwNX0.GISY5ITf3UujQWTlgqW7QUJuYvcdD47919iYRbJuwU0
ARG VITE_SITE_URL=https://heal-companion.onrender.com
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY
ENV VITE_SITE_URL=$VITE_SITE_URL
RUN npm run build

# ---- API + static UI ----
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=web /web/dist ./web/dist

# 项目 URL 可公开；用于校验登录 JWT（JWKS）。可被 Render 环境变量覆盖。
ENV SUPABASE_URL=https://ibzfvnzjnapjelxmfidh.supabase.co
ENV PORT=8787
EXPOSE 8787
CMD ["sh", "-c", "uvicorn api.server:app --host 0.0.0.0 --port ${PORT:-8787}"]
