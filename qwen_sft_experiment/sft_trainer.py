#!/usr/bin/env python3
"""
基于heal项目的Qwen中文小说能力SFT训练脚本
"""

import os
import json
import torch
import random
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
import numpy as np

@dataclass
class SFTConfig:
    """SFT配置"""
    model_name: str = "Qwen/Qwen3-1.7B"
    train_data_path: str = "heal_dialogue_training_data.json"
    eval_data_path: str = "heal_dialogue_evaluation_data.json"
    output_dir: str = "./qwen_sft_output"
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = None
    
    # 训练参数
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    num_train_epochs: int = 3
    max_seq_length: int = 512
    warmup_steps: int = 100
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100
    seed: int = 42
    
    def __post_init__(self):
        if self.lora_target_modules is None:
            self.lora_target_modules = [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ]

class QwenSFTTrainer:
    """Qwen SFT训练器"""
    
    def __init__(self, config: SFTConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.trainer = None
        
        # 设置随机种子
        self.set_seed()
        
    def set_seed(self):
        """设置随机种子"""
        random.seed(self.config.seed)
        np.random.seed(self.config.seed)
        torch.manual_seed(self.config.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.config.seed)
            
    def load_model_and_tokenizer(self):
        """加载模型和分词器"""
        print("正在加载模型和分词器...")
        
        # 加载分词器
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name,
            trust_remote_code=True
        )
        
        # 设置padding token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # 加载模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        print(f"模型加载完成：{self.config.model_name}")
        print(f"设备：{self.device}")
        
    def load_and_process_data(self) -> Dataset:
        """加载和处理数据"""
        print("正在加载和处理数据...")
        
        # 加载数据
        with open(self.config.train_data_path, 'r', encoding='utf-8') as f:
            train_data = json.load(f)
            
        with open(self.config.eval_data_path, 'r', encoding='utf-8') as f:
            eval_data = json.load(f)
            
        # 转换为Dataset格式
        train_dataset = Dataset.from_list(train_data)
        eval_dataset = Dataset.from_list(eval_data)
        
        # 数据预处理函数
        def preprocess_function(examples):
            """预处理数据"""
            instructions = examples["instruction"]
            inputs = examples["input"]
            outputs = examples["output"]
            
            # 构建完整的prompt
            prompts = []
            for instruction, input_text, output in zip(instructions, inputs, outputs):
                prompt = f"""instruction: {instruction}
input: {input_text}
output: {output}"""
                prompts.append(prompt)
                
            # Tokenize
            tokenized = self.tokenizer(
                prompts,
                truncation=True,
                max_length=self.config.max_seq_length,
                padding=False,
                return_tensors=None
            )
            
            # 设置labels
            tokenized["labels"] = tokenized["input_ids"].copy()
            
            return tokenized
            
        # 处理数据
        train_dataset = train_dataset.map(
            preprocess_function,
            batched=True,
            remove_columns=train_dataset.column_names
        )
        
        eval_dataset = eval_dataset.map(
            preprocess_function,
            batched=True,
            remove_columns=eval_dataset.column_names
        )
        
        print(f"数据处理完成")
        print(f"训练数据量：{len(train_dataset)}")
        print(f"评估数据量：{len(eval_dataset)}")
        
        return train_dataset, eval_dataset
        
    def setup_lora(self):
        """设置LoRA"""
        print("正在设置LoRA...")
        
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.lora_target_modules,
            bias="none",
        )
        
        # 应用LoRA
        self.model = get_peft_model(self.model, lora_config)
        
        # 打印可训练参数
        print(f"LoRA设置完成")
        print(f"可训练参数：{sum(p.numel() for p in self.model.parameters() if p.requires_grad)}")
        print(f"总参数：{sum(p.numel() for p in self.model.parameters())}")
        
    def setup_training_arguments(self):
        """设置训练参数"""
        print("正在设置训练参数...")
        
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            num_train_epochs=self.config.num_train_epochs,
            max_grad_norm=1.0,
            warmup_steps=self.config.warmup_steps,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            fp16=True,
            report_to=["tensorboard"],
            logging_dir=f"{self.config.output_dir}/logs",
            seed=self.config.seed,
        )
        
        # 数据整理器
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer,
            model=self.model,
            padding=True,
            max_length=self.config.max_seq_length,
            return_tensors="pt"
        )
        
        return training_args, data_collator
        
    def train(self):
        """开始训练"""
        print("开始SFT训练...")
        
        # 加载模型和分词器
        self.load_model_and_tokenizer()
        
        # 加载和处理数据
        train_dataset, eval_dataset = self.load_and_process_data()
        
        # 设置LoRA
        self.setup_lora()
        
        # 设置训练参数
        training_args, data_collator = self.setup_training_arguments()
        
        # 创建训练器
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        # 开始训练
        print("开始训练...")
        train_result = self.trainer.train()
        
        # 保存模型
        self.trainer.save_model(self.config.output_dir)
        self.tokenizer.save_pretrained(self.config.output_dir)
        
        # 保存训练结果
        self.save_training_results(train_result)
        
        print("训练完成！")
        
    def save_training_results(self, train_result):
        """保存训练结果"""
        results = {
            "train_loss": train_result.training_loss,
            "epoch": train_result.global_step,
            "config": self.config.__dict__,
            "timestamp": datetime.now().isoformat(),
        }
        
        with open(f"{self.config.output_dir}/training_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"训练结果已保存到：{self.config.output_dir}/training_results.json")
        
    def generate_response(self, instruction: str, input_text: str, max_length: int = 200) -> str:
        """生成回复"""
        if self.model is None:
            raise ValueError("模型未加载，请先调用train()方法")
            
        # 构建prompt
        prompt = f"""instruction: {instruction}
input: {input_text}
output:"""
        
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_seq_length,
        ).to(self.device)
        
        # 生成回复
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_length=max_length,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
            )
            
        # 解码回复
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 提取output部分
        if "output:" in response:
            response = response.split("output:")[1].strip()
            
        return response

def main():
    """主函数"""
    # 创建配置
    config = SFTConfig(
        model_name="Qwen/Qwen3-1.7B",
        train_data_path="heal_dialogue_training_data.json",
        eval_data_path="heal_dialogue_evaluation_data.json",
        output_dir="./qwen_sft_output",
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
    
    # 创建训练器
    trainer = QwenSFTTrainer(config)
    
    # 开始训练
    trainer.train()
    
    # 测试生成
    test_instruction = "生成符合heal角色设定的回复。当前关系阶段：熟悉，情感状态：温柔。"
    test_input = "今天论文进度又卡住了，感觉自己好废。"
    
    print("\n测试生成：")
    print(f"指令：{test_instruction}")
    print(f"输入：{test_input}")
    print(f"输出：{trainer.generate_response(test_instruction, test_input)}")

if __name__ == "__main__":
    main()