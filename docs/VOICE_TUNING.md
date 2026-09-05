# heal 语音与语气半自动调参指南

## 原文件在哪

- 角色人设与示例：`companion/persona/older_friend.yaml`
- 语气标签规则：`companion/persona/loader.py`
- 情绪标签到 TTS emotion 的映射：`companion/tts/emotion.py`
- 火山 TTS 请求参数：`companion/tts/volcengine.py`
- TTS API 与 edge-tts 回退：`api/server.py`
- 前端自动播放逻辑：`web/src/App.tsx`
- 左侧调音板样本：`web/src/components/DevLabPanel.tsx`

## 半自动怎么改

1. 打开网页左侧的“调”。
2. 在 `A · 调音` 里先切换音色：
   - 陶澄：`zh_male_taocheng_uranus_bigtts`
   - M191：`zh_male_m191_uranus_bigtts`
   - 温暖阿虎：`zh_male_wennuanahu_uranus_bigtts`
3. 再依次试听：
   - 明亮-日常回来
   - 热烈-专属偏爱
   - 温柔-低声安抚
   - 撒娇-熟悉后
   - 委屈-小情绪
   - 认真-边界
4. 哪条不像，就改 `web/src/components/DevLabPanel.tsx` 里的对应 `text`。
5. 如果是“说话方式不像”，改 `companion/persona/older_friend.yaml` 的示例。
6. 如果是“语音情绪不对”，改 `companion/tts/emotion.py` 的 `EMOTION_MAP`。
7. 如果是“声音太慢/太快/太低沉”，改 `.env`：

```env
VOLC_VOICE_TYPE=BV033_streaming
VOLC_SPEED_RATIO=1.04
VOLC_PITCH_RATIO=1.03
```

改完 `.env` 后需要重启后端。

页面端切换音色会保存到浏览器 localStorage，并随每次 `/api/tts` 请求传 `voice_type`，不用改 `.env` 也不用重启。

## 当前多情感标签

模型会在句首输出语气标签，前端不展示，但后端会拿来控制 TTS：

- `[明亮]`：日常问候、用户回来、清爽热情
- `[热烈]`：好事、偏爱、熟悉后的直球
- `[心疼]`：被骂、自责、崩溃、失眠、疲惫
- `[温柔]`：深夜、安抚、低声陪伴
- `[撒娇]`：熟悉后轻微黏人和小心思
- `[委屈]`：用户忽略或调侃过界时的小情绪
- `[认真]`：表达边界、承诺、现实建议
- `[开心]`：轻松玩笑、小确幸
- `[平和]`：普通事务确认

## 现在为什么会慢

当前链路是：

用户发送 -> LLM 流式回复 -> 等整段回复结束 -> 生成整段 TTS -> 播放。

所以文字会先出来，语音会慢半拍。要明显提速，需要下一步做“分句 TTS”：

用户发送 -> LLM 每生成完一句 -> 立刻合成这一句 -> 边播边生成下一句。

这是下一轮最值得做的体验优化。
