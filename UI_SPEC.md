# UI_SPEC — 现实系 1v1 陪伴沉浸式布局规范

> 本文件是 Heal-Companion 项目的 UI 架构约定。  
> 当前产品气质：现实系 1v1 男性 AI 陪伴，不做心理疗愈工具，也不做乙游复刻。
> 所有聊天页面组件必须严格遵守此规范，不得退化为普通网页卡片。

---

## 一、图层结构（Layering Strategy）

```
z-index 0  │ 全屏背景容器          position: fixed; inset: 0; overflow: hidden; background: #0E0B1E
z-index 0  │ 角色立绘 <img>        absolute inset-0, object-cover, object-position: center 15%
           │                       + animate-breathe（呼吸微动，见 globals.css）
z-index 1  │ 双层渐变遮罩           顶部 from-dark/55 → transparent（保护 topbar 文字）
           │                       底部 from-dark → transparent（托住聊天区域）
z-index 2  │ 顶部悬浮名牌           backdrop-blur-md, bg-white/10, border-white/20, rounded-full
z-index 2  │ 底部聊天交互区         backdrop-blur-xl, bg-slate-900/60, border-purple-500/30
```

---

## 二、核心 CSS Token（已在 app.css 的 `.world` 中定义）

| Token | 值 | 用途 |
|---|---|---|
| `--dark-bg` | `#0E0B1E` | 全局深夜底色 |
| `--glass-bg` | `rgba(18, 14, 38, 0.80)` | 磨砂卡片背景 |
| `--glass-border` | `rgba(196, 181, 232, 0.18)` | 磨砂卡片描边 |
| `--glass-blur` | `blur(22px)` | 磨砂强度 |
| `--ink` | `rgba(232, 226, 255, 0.92)` | 主文字色（浅紫白） |
| `--mute` | `rgba(180, 160, 230, 0.62)` | 次级文字色 |

---

## 三、呼吸微动动画（已定义于 `src/styles/globals.css`）

```css
@keyframes breathe {
  0%, 100% { transform: scale(1)    translateY(0);   }
  50%       { transform: scale(1.03) translateY(-6px); }
}

.animate-breathe {
  animation: breathe 7s ease-in-out infinite;
  transform-origin: center top; /* 锚定头部，放大时脸不下移 */
}
```

使用方式：在立绘 `<img>` 上添加 `className="... animate-breathe"`

---

## 四、立绘定位规则

```css
/* ✅ 正确 */
object-fit: cover;
object-position: center 15%;   /* 头肩黄金比，防止只露腰部 */

/* ❌ 禁止 */
border-radius: 50%;            /* 圆形 Avatar 会截断全身立绘 */
object-position: center center; /* 会导致只显示腰腹部 */
```

---

## 五、气泡样式规范

### AI 气泡（左对齐）
```css
background: rgba(100, 80, 180, 0.18);
backdrop-filter: blur(12px);
border: 1px solid rgba(180, 160, 240, 0.2);
color: rgba(232, 226, 255, 0.95);
border-radius: 20px;
border-bottom-left-radius: 5px;
```

### 用户气泡（右对齐）
```css
background: rgba(140, 110, 200, 0.55);
backdrop-filter: blur(8px);
color: rgba(240, 235, 255, 0.98);
border-radius: 20px;
border-bottom-right-radius: 5px;
```

---

## 六、输入栏规范

```css
background: rgba(14, 11, 30, 0.88);
backdrop-filter: blur(16px);
border-top: 1px solid rgba(255, 255, 255, 0.07);

/* 输入框 textarea */
background: rgba(255, 255, 255, 0.07);
border: 1px solid rgba(196, 181, 232, 0.2);
color: rgba(232, 226, 255, 0.95);
border-radius: 18px;

/* 发送按钮 */
background: linear-gradient(135deg, #9D80D4, #7A62B0);
border-radius: 999px;
```

---

## 七、绝对禁止清单（Immersion Rules）

| ❌ 禁止 | ✅ 替代方案 |
|---|---|
| 白色背景卡片 | `rgba(18,14,38,0.80)` 深色磨砂卡片 |
| 圆形 Avatar 头像 | 全屏立绘 `object-cover object-[center_15%]` |
| 每日任务 / 进度条 | 无 UI 元素化游戏感 |
| AI 免责声明水印 | 完全去除 |
| 说教式 AI 回复 | 先镜像共情，再轻量现实微建议 |
| `border-radius: 0` 直角卡片 | 最小 `border-radius: 18px`，主卡片 `32px` |
| 标准 `<input type="text">` 普通样式 | 磨砂玻璃圆角输入框 |

---

## 八、完整组件模板（React，使用项目自有 CSS 类）

> 以下模板与 `app.css` / `globals.css` 中已定义的类对应，**不依赖 Tailwind**。

```tsx
// ChatRoom.tsx 骨架
export default function ChatRoom() {
  return (
    <div className="char-room">

      {/* Layer 0+1: 立绘 + 渐变蒙版 */}
      <div className="char-bg" aria-hidden>
        <img
          src="/images/avatar.png"
          alt=""
          className="char-portrait animate-breathe"
          draggable={false}
        />
        <div className="char-gradient" />
      </div>

      {/* Layer 2: 顶部操作栏 */}
      <header className="char-topbar">
        <button className="char-back-btn">← 返回</button>
        <div className="char-topbar-actions">
          <button className="char-action-btn">记忆</button>
        </div>
      </header>

      {/* Layer 2: 主内容（角色名牌 + 消息 + 输入） */}
      <div className="char-overlay">
        <div className="char-hero-spacer">
          <div className="char-tag">
            <span className="char-status-dot" />
            <span className="char-tag-name">heal</span>
            <span className="char-tag-divider">·</span>
            <span className="char-tag-status">陪伴中</span>
          </div>
        </div>

        <div className="char-messages">
          {/* 渲染消息，AI 用 char-bubble--assistant，用户用 char-bubble--user */}
        </div>

        <div className="char-input-bar">
          <textarea className="char-input" placeholder="跟 heal 说点什么…" />
          <button className="char-send-btn">发送</button>
        </div>
      </div>

    </div>
  );
}
```

---

*本规范对应代码实现位于：*  
- `web/src/styles/app.css` — 所有 `.char-*` 类  
- `web/src/styles/globals.css` — `@keyframes breathe` + `.animate-breathe`  
- `web/src/pages/ChatRoom.tsx` — 完整运行组件  
