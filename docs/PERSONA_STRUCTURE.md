# Persona Structure

人设现在不是一整段 prompt，而是拆成可维护的角色卡。主文件：`companion/persona/older_friend.yaml`。

## 常改区域

- `persona_card`：角色一句话、核心反差、不是哪类人。
- `appearance`：外貌、气质、镜头感。换图或 Live2D 前先改这里。
- `relationship_system`：初识、熟悉、亲近、降温、修复这些关系阶段。
- `emotional_temperature`：用户靠近时如何升温，越界时如何降温，之后如何回温。
- `speech_texture`：口头禅、句长、动作描写、禁用语气。
- `scenario_reactions`：下班、深夜、旅行、自责、分享好事等常见场景怎么反应。
- `visual_assets`：三张角色图路径。
- `few_shot_examples`：最影响“像不像这个人”的示例回复。想调味道，优先改这里。

## 修改原则

1. 先改小模块，不要直接写长篇角色作文。
2. 改完一个模块，测试 3-5 个固定场景：初识、下班崩溃、分享好事、用户越界、用户道歉。
3. 如果回复变油腻，优先收紧 `speech_texture.avoid` 和 `few_shot_examples`。
4. 如果回复太冷，优先调 `emotional_temperature.warmer_when` 和熟悉/亲近阶段示例。