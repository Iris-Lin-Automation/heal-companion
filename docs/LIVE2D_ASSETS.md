# Live2D / 角色素材放置说明

## 现在先放什么

第一阶段不用完整 Live2D，先放一张高质量立绘即可：

```text
web/public/images/avatar.png
```

当前页面默认读取这个文件。你想换男主图，直接替换同名文件，刷新网页即可。

建议图片：

- PNG 优先，JPG 也可以。
- 半身到大腿，正面或 3/4 视角。
- 竖图，主体居中。
- 背景最好透明或干净，不要复杂大字。
- 少年感男性，脸和眼睛清晰。

## 真正 Live2D 后面放哪里

等你有 Live2D 模型后，放到：

```text
web/public/live2d/heal/
```

推荐结构：

```text
web/public/live2d/heal/heal.model3.json
web/public/live2d/heal/heal.moc3
web/public/live2d/heal/textures/
web/public/live2d/heal/motions/
web/public/live2d/heal/expressions/
```

代码里已经预留模型入口：

```tsx
modelSrc="/live2d/heal/heal.model3.json"
```

位置：

```text
web/src/pages/ChatRoom.tsx
web/src/components/LiveCharacterView.tsx
```

## 情绪映射

现在前端已经有这些状态：

- `bright`：明亮、日常回来
- `hot`：热烈、专属偏爱
- `warm`：温柔、低声安抚
- `playful`：撒娇、熟悉后
- `hurt`：心疼、委屈、小情绪
- `serious`：认真、边界
- `neutral`：普通待机

目前这些状态先驱动 CSS 微动和光感。接入真正 Live2D 后，再映射到表情和动作：

```text
bright  -> smile / idle_bright
hot     -> smile_big / lean_in
warm    -> soft_eye / idle_soft
playful -> tilt / playful
hurt    -> worried / look_down
serious -> serious / boundary
```

## 你现在需要准备的素材

先准备一张 `avatar.png` 就够了。完整 Live2D 模型可以晚一点再做。

如果是找画师/模型师，至少要准备：

- 分层 PSD：头发、眼睛、眼皮、瞳孔、嘴、脸、脖子、衣服、手臂分开。
- 表情：明亮、温柔、热烈、撒娇、委屈、认真。
- 动作：呼吸、眨眼、说话嘴型、靠近、偏头、低头、短暂停顿。
