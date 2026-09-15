"""单卡 QLoRA 微调（4090 够用），不上 DeepSpeed。"""
import os

import torch
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    HfArgumentParser,
    Trainer,
    TrainingArguments,
    set_seed,
)

from .arguments import DataTrainingArguments, ModelArguments, PeftArguments
from .data_preprocess import prepare_datasets
from .utils import empty_cache


def setup_model_and_tokenizer(model_args: ModelArguments, peft_args: PeftArguments):
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        model_args.model_name_or_path,
        trust_remote_code=True,
        padding_side="right",
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_args.model_name_or_path,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)

    target_modules = (
        peft_args.target_modules.split(",")
        if peft_args.target_modules
        else ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=peft_args.lora_rank,
        lora_alpha=peft_args.lora_alpha,
        lora_dropout=peft_args.lora_dropout,
        target_modules=target_modules,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    model.gradient_checkpointing_enable()

    return model, tokenizer


def main():
    parser = HfArgumentParser(
        (ModelArguments, DataTrainingArguments, PeftArguments, TrainingArguments)
    )
    model_args, data_args, peft_args, training_args = parser.parse_args_into_dataclasses()

    set_seed(training_args.seed)

    model, tokenizer = setup_model_and_tokenizer(model_args, peft_args)
    train_dataset, eval_dataset, data_collator = prepare_datasets(
        data_args, tokenizer, training_args
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset if training_args.do_train else None,
        eval_dataset=eval_dataset if training_args.do_eval else None,
        data_collator=data_collator,
    )

    if training_args.do_train:
        trainer.train()
        empty_cache()

    if training_args.do_eval:
        metrics = trainer.evaluate()
        print(f"Eval metrics: {metrics}")

    if training_args.output_dir:
        trainer.save_model(training_args.output_dir)
        tokenizer.save_pretrained(training_args.output_dir)


if __name__ == "__main__":
    main()
