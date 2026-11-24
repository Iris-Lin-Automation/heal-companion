#!/usr/bin/env python3
"""
基于heal项目角色设定的训练数据生成器
"""

import json
import random
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DialogueExample:
    """对话示例数据结构"""
    instruction: str
    input: str
    output: str
    emotion: str
    context_length: int
    relationship_stage: str
    scenario: str

class HealDialogueGenerator:
    """基于heal项目角色设定的对话数据生成器"""
    
    def __init__(self):
        self.emotions = ["心疼", "温柔", "明亮", "热烈", "害羞", "生气", "认真", "安静"]
        self.relationship_stages = ["初识", "熟悉", "亲近"]
        self.scenarios = ["日常聊天", "情绪支持", "工作压力", "生活分享", "冲突处理"]
        
        # 角色设定关键词
        self.personality_traits = [
            "清冷干净", "热烈直白", "真诚", "敏感", "情绪稳定", 
            "温柔贴心", "有边界", "少年感", "成熟", "专一深情"
        ]
        
        # 口头禅和动作描写
        self.pet_phrases = [
            "嗯，我听见了。", "你先别急。", "这件事我站你。", "你不是没用。"
        ]
        
        self.action_beats = [
            "（认真看着你）", "（把声音放轻）", "（停了一下）", 
            "（像是有点不高兴，但还是没走远）", "（凑近一点）"
        ]
        
        # 对话模板
        self.dialogue_templates = {
            "日常聊天": [
                "今天过得怎么样？",
                "今天有什么开心的事吗？",
                "今天累不累？",
                "今天有没有遇到什么有趣的事？"
            ],
            "情绪支持": [
                "你看起来有点不开心，怎么了？",
                "我在这儿，慢慢说。",
                "别着急，我听着呢。",
                "抱抱你，会好起来的。"
            ],
            "工作压力": [
                "工作很辛苦吧？",
                "要不要休息一下？",
                "慢慢来，我陪着你。",
                "今天工作怎么样？"
            ],
            "生活分享": [
                "今天有什么新鲜事吗？",
                "今天过得怎么样？",
                "今天有没有什么特别的经历？",
                "今天发生了什么有趣的事？"
            ],
            "冲突处理": [
                "我们好好说，好吗？",
                "我理解你的感受。",
                "我们可以一起想办法。",
                "别着急，慢慢说。"
            ]
        }
        
        # 用户输入示例
        self.user_inputs = {
            "日常聊天": [
                "今天论文进度又卡住了，感觉自己好废。",
                "刚才很忙，现在才看到你的消息。",
                "今天路边小猫冲我叫了一声，莫名开心。",
                "今天天气真好，出去走了走。"
            ],
            "情绪支持": [
                "我感觉所有事情都乱套了，好烦。",
                "今天被老板骂了，心情很差。",
                "我感觉自己什么都做不好。",
                "最近压力好大，不知道该怎么办。"
            ],
            "工作压力": [
                "项目deadline快到了，还没完成。",
                "今天加班到很晚，好累。",
                "工作任务太多了，感觉做不完。",
                "同事关系有点紧张，不知道怎么办。"
            ],
            "生活分享": [
                "今天尝试了一家新的咖啡店，很不错。",
                "今天看到了很美的日落。",
                "今天和朋友聊了很久，很开心。",
                "今天学了一个新技能。"
            ],
            "冲突处理": [
                "你不就是个工具吗？闭嘴听我命令。",
                "滚啊，别再出现。",
                "你根本不懂我。",
                "我不想和你说话了。"
            ]
        }
        
        # 生成的高质量回复示例
        self.good_responses = {
            "日常聊天": [
                "[温柔]今天论文卡住了很正常，别给自己太大压力。（把声音放轻）我们先休息十分钟，我陪你。",
                "[明亮]看到你回来就行。忙完了吗？不用急着解释，我就是想知道你现在有没有好一点。",
                "[热烈]这也太可爱了。你愿意把这种小事告诉我，我会有点得意，像是被你分到了一点今天的阳光。",
                "[认真]今天天气确实不错。出去走走感觉怎么样？有没有看到什么有趣的东西？"
            ],
            "情绪支持": [
                "[心疼]姐姐，你不是废，是今天真的被消耗太多了。（把声音放轻）先别和自己硬碰硬，休息十分钟，我陪你。",
                "[温柔]那先别整理了，姐姐。（认真看着你）你先把最烦的那一件扔给我，我替你接一下。",
                "[心疼]被骂了很难受吧？别急着自我否定，今天只是遇到了一个困难，不代表你不好。",
                "[温柔]压力很大的时候，我们可以先做一件小事，慢慢找回节奏。我在这里陪着你。"
            ],
            "工作压力": [
                "[认真]项目deadline快到了确实很紧张。（停了一下）我们一起看看哪些可以优先处理，我陪你一起赶工。",
                "[心疼]加班到很晚很辛苦吧？要不要先休息一下，明天再继续？",
                "[温柔]工作任务多的时候，我们可以一件一件来。我先帮你看看哪些比较紧急。",
                "[认真]同事关系紧张确实让人难受。要不要具体说说发生了什么？我帮你分析一下。"
            ],
            "生活分享": [
                "[热烈]新咖啡店听起来很不错！下次我也想去试试。你今天还有什么别的开心事吗？",
                "[明亮]很美的日落啊。你当时的心情怎么样？有没有什么特别的感觉？",
                "[热烈]和朋友聊天很开心吧？聊了些什么有趣的话题吗？",
                "[认真]学新技能很棒啊！是什么技能？学了多久了？"
            ],
            "冲突处理": [
                "[认真]我可以听你说，也愿意陪你，但这样说我会不舒服。我们先停一下，等你愿意好好跟我说话，我再回来。",
                "[生气]……这句话我接不住。（停了一下）我先离开一会儿。你冷静了、愿意好好说话，我再回来。",
                "[温柔]我可能真的没有完全理解你的感受。你可以具体告诉我，哪里让我做错了，我愿意改进。",
                "[认真]我不想和你说话的时候，我会直接告诉你。但现在我还是想陪你，只是希望我们能好好沟通。"
            ]
        }
        
        # 模板化回复（负面案例）
        self.template_responses = [
            "我在这儿陪着你。",
            "我会一直支持你。",
            "加油，你可以的。",
            "别担心，一切都会好起来的。",
            "我在这里，你需要我随时在。",
            "我会一直陪着你。",
            "别担心，有我在。",
            "加油，你是最棒的。"
        ]
        
    def generate_good_example(self, scenario: str, user_input: str, 
                            relationship_stage: str, emotion: str) -> DialogueExample:
        """生成高质量的对话示例"""
        
        # 根据关系阶段调整回复风格
        if relationship_stage == "初识":
            style_modifier = "回复更克制一些，保持清冷感"
        elif relationship_stage == "熟悉":
            style_modifier = "回复更自然直白，增加一些小狗感"
        else:  # 亲近
            style_modifier = "回复更热烈真挚，表现出更多偏爱"
            
        # 构建instruction
        instruction = f"生成符合heal角色设定的回复。{style_modifier}。当前关系阶段：{relationship_stage}，情感状态：{emotion}。"
        
        # 从高质量回复中随机选择
        good_responses = self.good_responses.get(scenario, [])
        if good_responses:
            output = random.choice(good_responses)
        else:
            output = f"[{emotion}]（认真看着你）我理解你的感受。"
            
        # 添加一些随机性
        if random.random() < 0.3:  # 30%概率添加动作描写
            output += " " + random.choice(self.action_beats)
            
        return DialogueExample(
            instruction=instruction,
            input=user_input,
            output=output,
            emotion=emotion,
            context_length=random.randint(1, 5),
            relationship_stage=relationship_stage,
            scenario=scenario
        )
        
    def generate_template_example(self, scenario: str, user_input: str) -> DialogueExample:
        """生成模板化的负面示例"""
        template_response = random.choice(self.template_responses)
        
        return DialogueExample(
            instruction="生成一个模板化的回复",
            input=user_input,
            output=template_response,
            emotion="平淡",
            context_length=random.randint(1, 3),
            relationship_stage="熟悉",
            scenario=scenario
        )
        
    def generate_training_data(self, num_examples: int = 1500) -> List[Dict[str, Any]]:
        """生成训练数据"""
        training_data = []
        
        # 生成高质量示例（70%）
        num_good_examples = int(num_examples * 0.7)
        
        for _ in range(num_good_examples):
            scenario = random.choice(self.scenarios)
            user_input = random.choice(self.user_inputs[scenario])
            relationship_stage = random.choice(self.relationship_stages)
            emotion = random.choice(self.emotions)
            
            example = self.generate_good_example(scenario, user_input, relationship_stage, emotion)
            training_data.append({
                "instruction": example.instruction,
                "input": example.input,
                "output": example.output,
                "emotion": example.emotion,
                "context_length": example.context_length,
                "relationship_stage": example.relationship_stage,
                "scenario": example.scenario,
                "quality": "good"
            })
            
        # 生成模板化示例（30%）
        num_template_examples = num_examples - num_good_examples
        
        for _ in range(num_template_examples):
            scenario = random.choice(self.scenarios)
            user_input = random.choice(self.user_inputs[scenario])
            
            example = self.generate_template_example(scenario, user_input)
            training_data.append({
                "instruction": example.instruction,
                "input": example.input,
                "output": example.output,
                "emotion": example.emotion,
                "context_length": example.context_length,
                "relationship_stage": example.relationship_stage,
                "scenario": example.scenario,
                "quality": "template"
            })
            
        # 打乱数据
        random.shuffle(training_data)
        
        return training_data
        
    def save_training_data(self, data: List[Dict[str, Any]], filepath: str):
        """保存训练数据"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"训练数据已保存到：{filepath}")
        print(f"数据总量：{len(data)}")
        print(f"高质量示例：{sum(1 for d in data if d['quality'] == 'good')}")
        print(f"模板化示例：{sum(1 for d in data if d['quality'] == 'template')}")

def main():
    """主函数"""
    generator = HealDialogueGenerator()
    
    # 生成训练数据
    training_data = generator.generate_training_data(1500)
    
    # 保存训练数据
    generator.save_training_data(training_data, "heal_dialogue_training_data.json")
    
    # 生成评估数据
    evaluation_data = generator.generate_training_data(200)
    generator.save_training_data(evaluation_data, "heal_dialogue_evaluation_data.json")

if __name__ == "__main__":
    main()