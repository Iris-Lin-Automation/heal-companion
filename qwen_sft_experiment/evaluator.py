#!/usr/bin/env python3
"""
基于heal项目的Qwen中文小说能力SFT评估脚本
"""

import os
import json
import time
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import load_dataset
import evaluate
import torch

@dataclass
class EvaluationConfig:
    """评估配置"""
    model_path: str = "./qwen_sft_output"
    base_model_name: str = "Qwen/Qwen3-1.7B"
    eval_data_path: str = "heal_dialogue_evaluation_data.json"
    output_dir: str = "./evaluation_results"
    
    # 生成参数
    max_length: int = 200
    temperature: float = 0.7
    top_p: float = 0.9
    num_return_sequences: int = 1
    
    # 评估指标
    use_bleu: bool = True
    use_rouge: bool = True
    use_meteor: bool = True
    
    # 人工评估
    num_manual_eval_samples: int = 20
    
class ModelEvaluator:
    """模型评估器"""
    
    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.base_model = None
        self.sft_model = None
        
        # 初始化评估指标
        self.bleu_metric = evaluate.load("bleu") if config.use_bleu else None
        self.rouge_metric = evaluate.load("rouge") if config.use_rouge else None
        self.meteor_metric = evaluate.load("meteor") if config.use_meteor else None
        
        # 创建输出目录
        os.makedirs(config.output_dir, exist_ok=True)
        
    def load_models(self):
        """加载模型"""
        print("正在加载模型...")
        
        # 加载分词器
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model_name,
            trust_remote_code=True
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # 加载基础模型
        print("加载基础模型...")
        self.base_model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model_name,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # 加载SFT模型
        print("加载SFT模型...")
        self.sft_model = AutoModelForCausalLM.from_pretrained(
            self.config.model_path,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        print("模型加载完成")
        
    def load_eval_data(self) -> List[Dict[str, Any]]:
        """加载评估数据"""
        print("正在加载评估数据...")
        
        with open(self.config.eval_data_path, 'r', encoding='utf-8') as f:
            eval_data = json.load(f)
            
        print(f"评估数据加载完成，共{len(eval_data)}条")
        return eval_data
        
    def generate_response(self, model, instruction: str, input_text: str) -> str:
        """生成回复"""
        # 构建prompt
        prompt = f"""instruction: {instruction}
input: {input_text}
output:"""
        
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        ).to(self.device)
        
        # 生成回复
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_length=self.config.max_length,
                num_return_sequences=self.config.num_return_sequences,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id,
            )
            
        # 解码回复
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 提取output部分
        if "output:" in response:
            response = response.split("output:")[1].strip()
            
        return response
        
    def evaluate_quantitative(self, eval_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """定量评估"""
        print("开始定量评估...")
        
        results = {
            "base_model": {},
            "sft_model": {},
            "comparison": {}
        }
        
        # 准备评估数据
        predictions_base = []
        predictions_sft = []
        references = []
        
        for item in eval_data:
            instruction = item["instruction"]
            input_text = item["input"]
            reference = item["output"]
            
            # 生成回复
            base_response = self.generate_response(self.base_model, instruction, input_text)
            sft_response = self.generate_response(self.sft_model, instruction, input_text)
            
            predictions_base.append(base_response)
            predictions_sft.append(sft_response)
            references.append(reference)
            
        # 计算BLEU分数
        if self.config.use_bleu:
            bleu_base = self.bleu_metric.compute(predictions=predictions_base, references=references)
            bleu_sft = self.bleu_metric.compute(predictions=predictions_sft, references=references)
            
            results["base_model"]["bleu"] = bleu_base
            results["sft_model"]["bleu"] = bleu_sft
            results["comparison"]["bleu_improvement"] = bleu_sft["bleu"] - bleu_base["bleu"]
            
        # 计算ROUGE分数
        if self.config.use_rouge:
            rouge_base = self.rouge_metric.compute(predictions=predictions_base, references=references)
            rouge_sft = self.rouge_metric.compute(predictions=predictions_sft, references=references)
            
            results["base_model"]["rouge"] = rouge_base
            results["sft_model"]["rouge"] = rouge_sft
            results["comparison"]["rouge_improvement"] = {
                "rouge1": rouge_sft["rouge1"] - rouge_base["rouge1"],
                "rouge2": rouge_sft["rouge2"] - rouge_base["rouge2"],
                "rougeL": rouge_sft["rougeL"] - rouge_base["rougeL"]
            }
            
        # 计算METEOR分数
        if self.config.use_meteor:
            meteor_base = self.meteor_metric.compute(predictions=predictions_base, references=references)
            meteor_sft = self.meteor_metric.compute(predictions=predictions_sft, references=references)
            
            results["base_model"]["meteor"] = meteor_base
            results["sft_model"]["meteor"] = meteor_sft
            results["comparison"]["meteor_improvement"] = meteor_sft["meteor"] - meteor_base["meteor"]
            
        print("定量评估完成")
        return results
        
    def evaluate_qualitative(self, eval_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """定性评估"""
        print("开始定性评估...")
        
        # 随机选择样本
        random.seed(42)
        eval_samples = random.sample(eval_data, min(self.config.num_manual_eval_samples, len(eval_data)))
        
        results = {
            "base_model_responses": [],
            "sft_model_responses": [],
            "reference_responses": [],
            "evaluation_criteria": {
                "角色一致性": "回复是否符合heal角色的设定（清冷→热烈）",
                "情感表达": "情感表达是否自然丰富",
                "上下文连贯": "回复是否与上下文自然衔接",
                "语言质量": "语言是否自然流畅，避免模板化"
            },
            "scores": {
                "base_model": {},
                "sft_model": {}
            }
        }
        
        # 评估每个样本
        for item in eval_samples:
            instruction = item["instruction"]
            input_text = item["input"]
            reference = item["output"]
            
            # 生成回复
            base_response = self.generate_response(self.base_model, instruction, input_text)
            sft_response = self.generate_response(self.sft_model, instruction, input_text)
            
            # 保存回复
            results["base_model_responses"].append({
                "input": input_text,
                "response": base_response,
                "reference": reference
            })
            
            results["sft_model_responses"].append({
                "input": input_text,
                "response": sft_response,
                "reference": reference
            })
            
            # 人工评估（这里简化处理，实际应用中需要人工评估）
            base_score = self.automated_evaluate_response(base_response, reference, instruction)
            sft_score = self.automated_evaluate_response(sft_response, reference, instruction)
            
            # 更新分数
            for criterion in results["evaluation_criteria"].keys():
                if criterion not in results["scores"]["base_model"]:
                    results["scores"]["base_model"][criterion] = []
                    results["scores"]["sft_model"][criterion] = []
                    
                results["scores"]["base_model"][criterion].append(base_score.get(criterion, 0))
                results["scores"]["sft_model"][criterion].append(sft_score.get(criterion, 0))
                
        # 计算平均分数
        for criterion in results["evaluation_criteria"].keys():
            results["scores"]["base_model"][criterion] = np.mean(results["scores"]["base_model"][criterion])
            results["scores"]["sft_model"][criterion] = np.mean(results["scores"]["sft_model"][criterion])
            
        print("定性评估完成")
        return results
        
    def automated_evaluate_response(self, response: str, reference: str, instruction: str) -> Dict[str, float]:
        """自动评估回复质量"""
        score = {
            "角色一致性": 0.0,
            "情感表达": 0.0,
            "上下文连贯": 0.0,
            "语言质量": 0.0
        }
        
        # 简化的评估逻辑
        # 1. 角色一致性
        if any(keyword in response for keyword in ["认真", "温柔", "热烈", "心疼"]):
            score["角色一致性"] = 0.8
        else:
            score["角色一致性"] = 0.4
            
        # 2. 情感表达
        if len(response) > 20 and any(emotion in response for emotion in ["[", "]"):
            score["情感表达"] = 0.7
        else:
            score["情感表达"] = 0.3
            
        # 3. 上下文连贯
        if len(response.split()) > 5 and not response.startswith("我"):
            score["上下文连贯"] = 0.8
        else:
            score["上下文连贯"] = 0.4
            
        # 4. 语言质量
        if len(response) > 15 and not response in ["我在这儿陪着你", "加油，你可以的"]:
            score["语言质量"] = 0.9
        else:
            score["语言质量"] = 0.3
            
        return score
        
    def save_results(self, quantitative_results: Dict[str, Any], qualitative_results: Dict[str, Any]):
        """保存评估结果"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "quantitative_results": quantitative_results,
            "qualitative_results": qualitative_results,
            "summary": self.generate_summary(quantitative_results, qualitative_results)
        }
        
        # 保存完整结果
        with open(f"{self.config.output_dir}/evaluation_results.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        # 保存详细对比
        self.save_detailed_comparison(qualitative_results)
        
        print(f"评估结果已保存到：{self.config.output_dir}/evaluation_results.json")
        
    def save_detailed_comparison(self, qualitative_results: Dict[str, Any]):
        """保存详细对比"""
        comparison_file = f"{self.config.output_dir}/detailed_comparison.md"
        
        with open(comparison_file, 'w', encoding='utf-8') as f:
            f.write("# 模型对比评估结果\n\n")
            f.write("## 评估标准\n\n")
            
            for criterion, description in qualitative_results["evaluation_criteria"].items():
                f.write(f"### {criterion}\n")
                f.write(f"{description}\n\n")
                
            f.write("## 详细对比\n\n")
            f.write("| 输入 | 基础模型回复 | SFT模型回复 | 参考回复 |\n")
            f.write("|------|-------------|-------------|----------|\n")
            
            for i in range(len(qualitative_results["base_model_responses"])):
                base_resp = qualitative_results["base_model_responses"][i]["response"]
                sft_resp = qualitative_results["sft_model_responses"][i]["response"]
                reference = qualitative_results["base_model_responses"][i]["reference"]
                input_text = qualitative_results["base_model_responses"][i]["input"]
                
                # 截断过长的回复
                base_resp = base_resp.replace("\n", " ")[:100] + "..." if len(base_resp) > 100 else base_resp
                sft_resp = sft_resp.replace("\n", " ")[:100] + "..." if len(sft_resp) > 100 else sft_resp
                reference = reference.replace("\n", " ")[:100] + "..." if len(reference) > 100 else reference
                
                f.write(f"| {input_text[:50]}... | {base_resp} | {sft_resp} | {reference} |\n")
                
        print(f"详细对比已保存到：{comparison_file}")
        
    def generate_summary(self, quantitative_results: Dict[str, Any], qualitative_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成评估摘要"""
        summary = {
            "improvement_overall": False,
            "improvement_details": {},
            "key_findings": []
        }
        
        # 定量改进
        if "comparison" in quantitative_results:
            comp = quantitative_results["comparison"]
            for metric, improvement in comp.items():
                if isinstance(improvement, dict):
                    for sub_metric, value in improvement.items():
                        if value > 0:
                            summary["improvement_overall"] = True
                            summary["improvement_details"][f"{metric}_{sub_metric}"] = value
                elif improvement > 0:
                    summary["improvement_overall"] = True
                    summary["improvement_details"][metric] = improvement
                    
        # 定性改进
        base_scores = qualitative_results["scores"]["base_model"]
        sft_scores = qualitative_results["scores"]["sft_model"]
        
        for criterion in base_scores.keys():
            if sft_scores[criterion] > base_scores[criterion]:
                improvement = sft_scores[criterion] - base_scores[criterion]
                summary["improvement_details"][f"{criterion}_qualitative"] = improvement
                
                if improvement > 0.1:
                    summary["key_findings"].append(f"SFT模型在{criterion}方面有显著提升")
                    
        return summary
        
    def run_evaluation(self):
        """运行完整评估"""
        print("开始评估...")
        
        # 加载模型
        self.load_models()
        
        # 加载评估数据
        eval_data = self.load_eval_data()
        
        # 定量评估
        quantitative_results = self.evaluate_quantitative(eval_data)
        
        # 定性评估
        qualitative_results = self.evaluate_qualitative(eval_data)
        
        # 保存结果
        self.save_results(quantitative_results, qualitative_results)
        
        # 打印摘要
        summary = self.generate_summary(quantitative_results, qualitative_results)
        print("\n评估摘要：")
        print(f"整体改进：{summary['improvement_overall']}")
        print(f"改进详情：{summary['improvement_details']}")
        print(f"关键发现：{summary['key_findings']}")
        
        print("评估完成！")

def main():
    """主函数"""
    config = EvaluationConfig(
        model_path="./qwen_sft_output",
        base_model_name="Qwen/Qwen3-1.7B",
        eval_data_path="heal_dialogue_evaluation_data.json",
        output_dir="./evaluation_results",
        num_manual_eval_samples=20
    )
    
    evaluator = ModelEvaluator(config)
    evaluator.run_evaluation()

if __name__ == "__main__":
    main()