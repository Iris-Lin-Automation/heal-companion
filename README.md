# heal · 专属陪伴 Agent（可演示）

> **一句话：** 带账号隔离、长期记忆、流式对话与环境白噪音的 1v1 LLM 陪伴应用。  
> 工程内核可迁移到多轮客服 / 语音坐席 / 业务智能体。

| | |
|---|---|
| **线上演示** | https://heal-companion.onrender.com |
| **源码** | https://github.com/Iris-Lin-Automation/heal-companion |
| **技术证明** | Auth（Supabase JWT）· 用户数据隔离 · Postgres 记忆 · SSE 流式对话 · TTS / 环境音 |

> Render 免费实例会休眠，首次打开可能要等几十秒。请先 **注册/登录** 再进入对话。

---

## 先看长什么样

<p align="center">
  <img src="web/public/images/heal-character-main.jpg" alt="heal 角色立绘" width="360" />
</p>

<p align="center">
  <img src="docs/demo-frames/expressions.gif" alt="heal 表情切换演示" width="320" />
  <br/>
  <em>立绘表情切换：平静 / 微笑 / 害羞 / 生气 / 委屈 / 受伤 / 说话</em>
</p>

**体验路径（约 2 分钟）：**

1. 打开 [演示站](https://heal-companion.onrender.com) → 注册 / 登录  
2. 填入 DeepSeek API Key（免费体验，Key 只在你浏览器）  
3. 进入对话，发一句；可开 **雨声 / 树荫白噪音**（右上菜单 → 音乐）  
4. 打开 **记忆本**，查看或改写一起记得的事  

> 有时间的话，再补一段 30–60 秒真实操作录屏会更好（登录 → 开雨声 → 对话 → 记忆本）。不是必须：现在 GIF + 演示链接已经够简历展示。

---

## 你能立刻感知的功能

- **登录隔离**：A 只能看到 A 的伴侣 / 会话 / 记忆  
- **长期记忆**：对话后抽取并召回；记忆本可编辑删除  
- **流式对话**：SSE 逐字输出 + OpenAI 兼容 `/v1`  
- **语音**：浏览器语音输入；AI 回复可 TTS 自动播放  
- **环境音**：树荫雨声、热带雨林雨声、雨声+颂钵等（AmbientPlayer）  
- **主动问候**：低密度 heartbeat，偶尔来一句  

---

## 技术栈（简历口径）

| 层 | 技术 |
|----|------|
| 前端 | React 19 · TypeScript · Vite · Glass UI |
| 后端 | Python · FastAPI · Uvicorn · SSE |
| 模型 | DeepSeek（OpenAI SDK 兼容） |
| 身份 | Supabase Auth · JWT（JWKS / ES256） |
| 数据 | Postgres（profiles / companions / conversations / messages / memories）+ RLS |
| 语音 / 声学 | 火山 / edge-tts · Web Speech · Ambient 雨声轨 |
| 工程 | Docker · Render · pytest 隔离测试 |

架构要点：

```
登录拿 JWT → API 只信 token.sub → get_store(user)
  → Supabase（或本地文件回退）读写仅限该用户
```

---

## 本地运行

```bash
# 1) 后端
pip install -r requirements.txt
copy .env.example .env   # 填 OPENAI_* 与 SUPABASE_*
# 在 Supabase SQL Editor 执行 supabase/migrations/001_identity_and_memory.sql
uvicorn api.server:app --reload --port 8787

# 2) 前端
cd web
npm install
npm run dev
```

打开 http://127.0.0.1:5173

必需环境变量见 `.env.example`（`SUPABASE_URL`、`SUPABASE_SERVICE_ROLE_KEY`、`VITE_SUPABASE_*`、`VITE_SITE_URL` 等）。

---

## 测试

```bash
pytest tests -q
```

覆盖：未登录拒绝、跨用户读写拒绝、令牌身份优先于 body 伪造 `user_id`、service-role 查询仍带用户过滤。

---

## 部署（Render）

`render.yaml` + `Dockerfile` 多阶段构建。上线前请在 Render 配齐：

- `OPENAI_*` / `VOLC_*`（可选）
- `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_JWT_SECRET`（可空，走 JWKS）
- 构建参数：`VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` / `VITE_SITE_URL`

---

## 记忆类型

identity / preference / person / event / commitment / emotion_pattern / win / boundary

---

## 求职 / 合作怎么讲

**产品壳是陪伴，工程内核是 Agent 底座：** 鉴权 → 会话 → 长期记忆 → 流式生成 → 语音/声学。  
同一套可迁到多轮客服、语音坐席、内部知识助手。

---

## License / 说明

个人作品，欢迎试用与反馈。源码公开便于审查能力；请勿把别人的 API Key 或 service_role 密钥提交进仓库。
