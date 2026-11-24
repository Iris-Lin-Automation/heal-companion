#!/usr/bin/env python3
"""
基于heal项目的Qwen中文小说能力SFT实验主脚本
"""

import os
import sys
import json
import argparse
from datetime import datetime
from data_generator import HealDialogueGenerator
from sft_trainer import QwenSFTTrainer, SFTConfig
from evaluator import ModelEvaluator, EvaluationConfig

class QwenSFTExperiment:
    """Qwen SFT实验管理器"""
    
    def __init__(self, experiment_name: str = "heal_sft_experiment"):
        self.experiment_name = experiment_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.experiment_dir = f"./experiments/{experiment_name}_{self.timestamp}"
        
        # 创建实验目录
        os.makedirs(self.experiment_dir, exist_ok=True)
        
        # 初始化组件
        self.data_generator = None
        self.trainer = None
        self.evaluator = None
        
        print(f"实验初始化完成：{self.experiment_dir}")
        
    def setup_experiment(self):
        """设置实验"""
        print("正在设置实验...")
        
        # 1. 生成训练数据
        print("1. 生成训练数据...")
        self.data_generator = HealDialogueGenerator()
        
        # 生成训练数据
        training_data = self.data_generator.generate_training_data(1500)
        training_data_path = f"{self.experiment_dir}/heal_dialogue_training_data.json"
        self.data_generator.save_training_data(training_data, training_data_path)
        
        # 生成评估数据
        evaluation_data = self.data_generator.generate_training_data(200)
        evaluation_data_path = f"{self.experiment_dir}/heal_dialogue_evaluation_data.json"
        self.data_generator.save_training_data(evaluation_data, evaluation_data_path)
        
        # 2. 设置训练配置
        print("2. 设置训练配置...")
        train_config = SFTConfig(
            model_name="Qwen/Qwen3-1.7B",
            train_data_path=training_data_path,
            eval_data_path=evaluation_data_path,
            output_dir=f"{self.experiment_dir}/sft_output",
            lora_r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            num_train_epochs=3,
            max_seq_length=512,
            warmup_steps=100,
            logging_steps=10,
            save_steps=100,
            eval_steps=100,
            seed=42
        )
        
        # 3. 设置评估配置
        print("3. 设置评估配置...")
        eval_config = EvaluationConfig(
            model_path=f"{self.experiment_dir}/sft_output",
            base_model_name="Qwen/Qwen3-1.7B",
            eval_data_path=evaluation_data_path,
            output_dir=f"{self.experiment_dir}/evaluation_results",
            num_manual_eval_samples=20
        )
        
        # 保存实验配置
        experiment_config = {
            "experiment_name": self.experiment_name,
            "timestamp": self.timestamp,
            "train_config": train_config.__dict__,
            "eval_config": eval_config.__dict__,
            "data_paths": {
                "training_data": training_data_path,
                "evaluation_data": evaluation_data_path
            }
        }
        
        with open(f"{self.experiment_dir}/experiment_config.json", 'w', encoding='utf-8') as f:
            json.dump(experiment_config, f, ensure_ascii=False, indent=2)
        
        print("实验设置完成")
        
    def run_baseline_evaluation(self):
        """运行基线评估"""
        print("运行基线评估...")
        
        eval_config = EvaluationConfig(
            model_path="Qwen/Qwen3-1.7B",  # 使用基础模型
            base_model_name="Qwen/Qwen3-1.7B",
            eval_data_path=f"{self.experiment_dir}/heal_dialogue_evaluation_data.json",
            output_dir=f"{self.experiment_dir}/baseline_evaluation",
            num_manual_eval_samples=20
        )
        
        self.evaluator = ModelEvaluator(eval_config)
        self.evaluator.run_evaluation()
        
        print("基线评估完成")
        
    def run_training(self):
        """运行训练"""
        print("开始训练...")
        
        train_config = SFTConfig(
            model_name="Qwen/Qwen3-1.7B",
            train_data_path=f"{self.experiment_dir}/heal_dialogue_training_data.json",
            eval_data_path=f"{self.experiment_dir}/heal_dialogue_evaluation_data.json",
            output_dir=f"{self.experiment_dir}/sft_output",
            lora_r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            num_train_epochs=3,
            max_seq_length=512,
            warmup_steps=100,
            logging_steps=10,
            save_steps=100,
            eval_steps=100,
            seed=42
        )
        
        self.trainer = QwenSFTTrainer(train_config)
        self.trainer.train()
        
        print("训练完成")
        
    def run_evaluation(self):
        """运行评估"""
        print("开始评估...")
        
        eval_config = EvaluationConfig(
            model_path=f"{self.experiment_dir}/sft_output",
            base_model_name="Qwen/Qwen3-1.7B",
            eval_data_path=f"{self.experiment_dir}/heal_dialogue_evaluation_data.json",
            output_dir=f"{self.experiment_dir}/evaluation_results",
            num_manual_eval_samples=20
        )
        
        self.evaluator = ModelEvaluator(eval_config)
        self.evaluator.run_evaluation()
        
        print("评估完成")
        
    def generate_report(self):
        """生成实验报告"""
        print("生成实验报告...")
        
        # 读取实验配置
        with open(f"{self.experiment_dir}/experiment_config.json", 'r', encoding='utf-8') as f:
            experiment_config = json.load(f)
            
        # 读取训练结果
        with open(f"{self.experiment_dir}/sft_output/training_results.json", 'r', encoding='utf-8') as f:
            training_results = json.load(f)
            
        # 读取评估结果
        with open(f"{self.experiment_dir}/evaluation_results/evaluation_results.json", 'r', encoding='utf-8') as f:
            evaluation_results = json.load(f)
            
        # 生成报告
        report = f"""# Qwen中文小说能力SFT实验报告

## 实验概述
- **实验名称**: {self.experiment_name}
- **实验时间**: {self.timestamp}
- **实验目标**: 基于heal项目角色设定，改善AI对话的**人物声音一致性**、**上下文衔接自然度**和**情感表达能力**

## 实验设计
- **初始模型**: Qwen/Qwen3-1.7B
- **训练方法**: LoRA微调
- **数据规模**: 1500条训练数据，200条评估数据
- **训练参数**: 
  - LoRA r=8, alpha=16
  - batch_size=4, epochs=3, lr=2e-4
  - max_seq_length=512

## 问题选择与假设

### 选择的问题
1. **人物声音趋同** → 改善角色一致性
2. **上下文衔接不自然** → 改善上下文理解能力
3. **描写空泛** → 增强情感表达能力

### 实验假设
- 通过SFT训练，模型能够更好地理解heal角色的设定
- 模型能够生成更符合角色特点的对话回复
- 模型能够更好地处理上下文和情感表达

## 数据准备

### 数据来源
- 基于heal项目现有的角色设定（persona_card.yaml, examples.yaml）
- 自动生成高质量对话数据
- 包含负面案例（模板化回复）用于对比训练

### 数据质量
- 高质量示例: 70%（符合角色设定）
- 模板化示例: 30%（用于对比训练）
- 涵盖5种场景: 日常聊天、情绪支持、工作压力、生活分享、冲突处理

## 训练过程

### 训练配置
- **模型**: Qwen/Qwen3-1.7B
- **LoRA参数**: r=8, alpha=16, dropout=0.05
- **训练参数**: batch_size=4, epochs=3, lr=2e-4
- **优化器**: AdamW

### 训练结果
- **训练损失**: {training_results['train_loss']:.4f}
- **训练轮数**: {training_results['epoch']}
- **训练时间**: {training_results['timestamp']}

## 评估结果

### 定量评估
"""
        
        # 添加定量评估结果
        if 'quantitative_results' in evaluation_results:
            quant_results = evaluation_results['quantitative_results']
            if 'comparison' in quant_results:
                comp = quant_results['comparison']
                report += "\n#### 指标改进\n"
                for metric, improvement in comp.items():
                    if isinstance(improvement, dict):
                        for sub_metric, value in improvement.items():
                            report += f"- {metric}_{sub_metric}: {value:.4f}\n"
                    else:
                        report += f"- {metric}: {improvement:.4f}\n"
                        
        # 添加定性评估结果
        if 'qualitative_results' in evaluation_results:
            qual_results = evaluation_results['qualitative_results']
            if 'scores' in qual_results:
                scores = qual_results['scores']
                report += "\n### 定性评估\n"
                report += "\n#### 评分对比\n"
                report += "| 评估标准 | 基础模型 | SFT模型 | 改进幅度 |\n"
                report += "|---------|----------|---------|----------|\n"
                
                for criterion in scores['base_model'].keys():
                    base_score = scores['base_model'][criterion]
                    sft_score = scores['sft_model'][criterion]
                    improvement = sft_score - base_score
                    report += f"| {criterion} | {base_score:.3f} | {sft_score:.3f} | {improvement:.3f} |\n"
                    
        # 添加结论
        if 'summary' in evaluation_results:
            summary = evaluation_results['summary']
            report += f"\n## 结论\n\n"
            report += f"**整体改进**: {'是' if summary['improvement_overall'] else '否'}\n\n"
            
            if summary['key_findings']:
                report += f"**关键发现**:\n"
                for finding in summary['key_findings']:
                    report += f"- {finding}\n"
                    
        # 保存报告
        report_path = f"{self.experiment_dir}/experiment_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
            
        print(f"实验报告已生成: {report_path}")
        
    def run_full_experiment(self):
        """运行完整实验"""
        print("开始完整实验...")
        
        # 1. 设置实验
        self.setup_experiment()
        
        # 2. 运行基线评估
        self.run_baseline_evaluation()
        
        # 3. 运行训练
        self.run_training()
        
        # 4. 运行评估
        self.run_evaluation()
        
        # 5. 生成报告
        self.generate_report()
        
        print("完整实验完成！")
        
    def run_quick_experiment(self):
        """运行快速实验（仅训练和评估）"""
        print("开始快速实验...")
        
        # 1. 生成数据
        self.data_generator = HealDialogueGenerator()
        training_data = self.data_generator.generate_training_data(500)  # 减少数据量
        evaluation_data = self.data_generator.generate_training_data(100)
        
        training_data_path = f"{self.experiment_dir}/heal_dialogue_training_data.json"
        evaluation_data_path = f"{self.experiment_dir}/heal_dialogue_evaluation_data.json"
        
        self.data_generator.save_training_data(training_data, training_data_path)
        self.data_generator.save_training_data(evaluation_data, evaluation_data_path)
        
        # 2. 运行训练
        train_config = SFTConfig(
            model_name="Qwen/Qwen3-1.7B",
            train_data_path=training_data_path,
            eval_data_path=evaluation_data_path,
            output_dir=f"{self.experiment_dir}/sft_output",
            lora_r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            per_device_train_batch_size=4,
            per_device_eval_batch_size=4,
            gradient_accumulation_steps=4,
            learning_rate=2e-4,
            num_train_epochs=2,  # 减少训练轮数
            max_seq_length=512,
            warmup_steps=50,
            logging_steps=10,
            save_steps=50,
            eval_steps=50,
            seed=42
        )
        
        self.trainer = QwenSFTTrainer(train_config)
        self.trainer.train()
        
        # 3. 运行评估
        eval_config = EvaluationConfig(
            model_path=f"{self.experiment_dir}/sft_output",
            base_model_name="Qwen/Qwen3-1.7B",
            eval_data_path=evaluation_data_path,
            output_dir=f"{self.experiment_dir}/evaluation_results",
            num_manual_eval_samples=10
        )
        
        self.evaluator = ModelEvaluator(eval_config)
        self.evaluator.run_evaluation()
        
        # 4. 生成报告
        self.generate_report()
        
        print("快速实验完成！")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Qwen中文小说能力SFT实验')
    parser.add_argument('--mode', choices=['full', 'quick'], default='full',
                       help='实验模式: full(完整实验) 或 quick(快速实验)')
    parser.add_argument('--experiment-name', default='heal_sft_experiment',
                       help='实验名称')
    
    args = parser.parse_args()
    
    # 创建实验管理器
    experiment = QwenSFTExperiment(args.experiment_name)
    
    # 运行实验
    if args.mode == 'full':
        experiment.run_full_experiment()
    else:
        experiment.run_quick_experiment()

if __name__ == "__main__":
    main()