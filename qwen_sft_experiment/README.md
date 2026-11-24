# Qwen中文小说能力SFT实验

基于heal项目角色设定的Qwen/Qwen3-1.7B中文小说能力SFT实验。

## 实验概述

### 实验目标
基于heal项目的"older_friend"角色设定，通过SFT训练改善以下问题：
1. **人物声音趋同**：确保AI角色的对话风格保持独特性和一致性
2. **上下文衔接不自然**：改善对话的连贯性和上下文理解能力
3. **描写空泛**：增强对话的情感表达和细节描写能力

### 实验特色
- 结合heal项目的角色设定，专注于AI陪伴场景
- 使用LoRA进行高效微调，适合1.7B模型
- 包含完整的数据生成、训练、评估流程
- 提供详细的实验报告和对比分析

## 快速开始

### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv qwen_sft_env
source qwen_sft_env/bin/activate  # Linux/Mac
qwen_sft_env\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行实验
```bash
# 完整实验（推荐）
python run_experiment.py --mode full --experiment-name heal_sft_experiment

# 快速实验（减少数据量和训练轮数）
python run_experiment.py --mode quick --experiment-name heal_sft_experiment
```

### 3. 查看结果
实验完成后，结果会保存在`experiments/`目录下，包含：
- 训练数据和模型
- 评估结果
- 实验报告
- 详细对比分析

## 项目结构

```
qwen_sft_experiment/
├── data_generator.py          # 训练数据生成器
├── sft_trainer.py             # SFT训练脚本
├── evaluator.py               # 模型评估脚本
├── run_experiment.py          # 主运行脚本
├── requirements.txt           # 依赖项
├── README.md                 # 说明文档
└── experiments/               # 实验结果目录
    ├── heal_sft_experiment_YYYYMMDD_HHMMSS/
    │   ├── heal_dialogue_training_data.json    # 训练数据
    │   ├── heal_dialogue_evaluation_data.json  # 评估数据
    │   ├── sft_output/                         # 训练模型
    │   ├── evaluation_results/                  # 评估结果
    │   ├── baseline_evaluation/                 # 基线评估
    │   ├── experiment_config.json              # 实验配置
    │   └── experiment_report.md                 # 实验报告
```

## 详细说明

### 1. 数据生成
基于heal项目的角色设定，自动生成高质量对话数据：
- **高质量示例**：70%符合角色设定
- **模板化示例**：30%用于对比训练
- **覆盖场景**：日常聊天、情绪支持、工作压力、生活分享、冲突处理

**角色设定特点**：
- 外在清冷干净，熟悉后热烈直白真挚
- 有少年感，但不幼稚
- 专一深情，但不强迫绑定
- 真诚敏感，被伤害会受伤，但情绪稳定

### 2. 训练配置
- **模型**：Qwen/Qwen3-1.7B
- **训练方法**：LoRA微调
- **LoRA参数**：r=8, alpha=16, dropout=0.05
- **训练参数**：batch_size=4, epochs=3, lr=2e-4
- **数据规模**：1500条训练数据，200条评估数据

### 3. 评估方法
- **定量评估**：BLEU、ROUGE、METEOR指标
- **定性评估**：角色一致性、情感表达、上下文连贯、语言质量
- **基线对比**：训练前后的模型对比

### 4. 实验报告
实验报告包含：
- 实验概述和设计
- 问题选择和假设
- 数据准备和质量分析
- 训练过程和结果
- 评估结果和对比分析
- 结论和改进建议

## 使用示例

### 1. 自定义数据生成
```python
from data_generator import HealDialogueGenerator

generator = HealDialogueGenerator()
training_data = generator.generate_training_data(1000)
generator.save_training_data(training_data, "custom_training_data.json")
```

### 2. 单独训练
```python
from sft_trainer import QwenSFTTrainer, SFTConfig

config = SFTConfig(
    model_name="Qwen/Qwen3-1.7B",
    train_data_path="custom_training_data.json",
    eval_data_path="custom_evaluation_data.json",
    output_dir="./custom_output"
)

trainer = QwenSFTTrainer(config)
trainer.train()
```

### 3. 单独评估
```python
from evaluator import ModelEvaluator, EvaluationConfig

config = EvaluationConfig(
    model_path="./custom_output",
    base_model_name="Qwen/Qwen3-1.7B",
    eval_data_path="custom_evaluation_data.json",
    output_dir="./custom_evaluation"
)

evaluator = ModelEvaluator(config)
evaluator.run_evaluation()
```

## 资源需求

### 硬件要求
- **GPU**：推荐1-2块RTX 3090或A100
- **内存**：至少16GB RAM
- **存储**：至少10GB可用空间

### 时间要求
- **完整实验**：约6-8小时
- **快速实验**：约2-3小时

### 环境要求
- Python 3.8+
- PyTorch 2.0+
- Transformers 4.30+

## 故障排除

### 1. 内存不足
- 减少batch_size
- 使用gradient_accumulation_steps
- 启用fp16

### 2. 训练时间过长
- 减少数据量
- 减少epochs
- 使用更小的LoRA参数

### 3. 评估结果不理想
- 检查数据质量
- 调整训练参数
- 增加训练数据量

## 扩展功能

### 1. 添加新的角色设定
修改`data_generator.py`中的角色设定和对话模板。

### 2. 自定义评估指标
在`evaluator.py`中添加新的评估指标。

### 3. 多模型对比
扩展评估脚本，支持多个模型的对比评估。

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目遵循MIT许可证。

## 致谢

- 感谢heal项目提供的角色设定和对话范例
- 感谢Qwen团队提供的开源模型
- 感谢Hugging Face提供的transformers库