# heal · 现实系 AI 陪伴

**不是心理疗愈工具，也不是乙游复刻**——用「记得你、自然说话、偶尔主动找你」的方式，成为用户现实生活里一个稳定的陪伴者。

## 架构（成熟开源 + 自研记忆）

| 层 | 选型 | 作用 |
|----|------|------|
| 自研核心 | Python 记忆层 + 人设 `soul.md` | 记得事件/人/承诺，先共情再给现实小步骤 |
| 自研网页 | Vite + React + [chatscope](https://github.com/chatscope/chat-ui-kit-react) | 现实系 1v1 陪伴界面（产品 UI） |
| 成熟 UI（可选） | [Open WebUI](https://github.com/open-webui/open-webui) (100k+★) | 把 API 指到本项目的 `/v1` 即可用 |
| 记忆演进（可选） | [Mem0](https://github.com/mem0ai/mem0) / [Memobase](https://github.com/memodb-io/memobase) | 以后把关键词召回升级成向量记忆 |

本仓库暴露 **OpenAI 兼容接口** `/v1/chat/completions`，因此 LobeChat / LibreChat / Open WebUI 都能接。

## 本地跑（推荐先看自研网页）

```bash
# 1) API
cd D:\Projects\heal-companion
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # 填 OPENAI_API_KEY
uvicorn api.server:app --reload --port 8787

# 2) 网页（另开终端）
cd web
npm install
npm run dev
```

打开 http://localhost:5173

- 聊天会走记忆召回 + 抽取  
- 右侧可看长期记忆  
- 「主动问候」= 低密度 heartbeat  

## 接 Open WebUI（成熟开源壳）

```bash
docker compose up -d
```

- 自研 API：http://localhost:8787  
- Open WebUI：http://localhost:3000  
- 连接里 API Base 填 `http://companion:8787/v1`（compose 已预置环境变量）

手动接已有 Open WebUI：Settings → Connections → OpenAI → URL `http://host.docker.internal:8787/v1`，选模型 `heal-companion`。

## 记忆类型

identity / preference / person / event / commitment / emotion_pattern / win / boundary  

文件在 `data/users/<id>/`（`memories.json` + 可读 `MEMORY.md`）。

## CLI（可选）

```bash
python main.py chat
```
