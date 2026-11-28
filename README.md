# heal · 专属陪伴

带账号隔离、长期记忆、流式对话与环境白噪音的 1v1 LLM 陪伴应用。

| | |
|---|---|
| **线上演示** | https://heal-companion.onrender.com |
| **源码** | https://github.com/Iris-Lin-Automation/heal-companion |

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

**怎么玩：**

1. 打开 [演示站](https://heal-companion.onrender.com) → 注册 / 登录  
2. 填入 DeepSeek API Key（Key 只存在你的浏览器）  
3. 进入对话；可开 **雨声 / 树荫白噪音**（右上菜单 → 音乐）  
4. 打开 **记忆本**，查看或改写一起记得的事  

---

## 功能

- **登录隔离**：每人只能看到自己的伴侣、会话和记忆  
- **长期记忆**：对话后抽取并召回；记忆本可编辑、删除  
- **流式对话**：SSE 逐字输出；兼容 OpenAI 格式 `/v1`  
- **语音**：浏览器语音输入；回复可 TTS 自动播放  
- **环境音**：树荫雨声、热带雨林雨声、雨声+颂钵等  
- **主动问候**：低密度 heartbeat，偶尔来一句  

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | React 19 · TypeScript · Vite |
| 后端 | Python · FastAPI · Uvicorn · SSE |
| 模型 | DeepSeek（OpenAI SDK 兼容） |
| 身份 | Supabase Auth · JWT（JWKS / ES256） |
| 数据 | Postgres（profiles / companions / conversations / messages / memories）+ RLS |
| 语音 / 声学 | 火山 / edge-tts · Web Speech · Ambient 雨声 |
| 工程 | Docker · Render · pytest |

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

环境变量说明见 `.env.example`。

---

## 测试

```bash
pytest tests -q
```

---

## 部署（Render）

`render.yaml` + `Dockerfile`。需要配置：

- `OPENAI_*` / `VOLC_*`（可选）
- `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_JWT_SECRET`（可空，走 JWKS）
- 构建参数：`VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` / `VITE_SITE_URL`

---

## 记忆类型

identity / preference / person / event / commitment / emotion_pattern / win / boundary

---

欢迎试用与反馈。请勿把 API Key 或 service_role 密钥提交进仓库。
