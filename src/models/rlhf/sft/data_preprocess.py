"""把 jsonl 对话数据按 Qwen 的 chat template 处理成训练样本。"""
import json
from typing import Any, Dict, List, Optional, Tuple

from torch.utils.data import Dataset
from transformers import DataCollatorForSeq2Seq, PreTrainedTokenizer


class FeynmanSFTDataset(Dataset):
    def __init__(self, data: List[Dict[str, Any]], tokenizer: PreTrainedTokenizer, data_args):
        self.data = data
        self.tokenizer = tokenizer
        self.max_source_length = data_args.max_source_length
        self.max_target_length = data_args.max_target_length
        self.prompt_column = data_args.prompt_column
        self.response_column = data_args.response_column

    def __len__(self):
        return len(self.data)

    def __getitem__(self, i: int):
        item = self.data[i]
        prompt_messages = self._parse_messages(item[self.prompt_column])
        response_message = self._parse_response(item[self.response_column])

        prompt_text = self.tokenizer.apply_chat_template(
            prompt_messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        full_messages = prompt_messages + [response_message]
        full_text = self.tokenizer.apply_chat_template(
            full_messages,
            tokenize=False,
            add_generation_prompt=False,
        )

        prompt_ids = self.tokenizer(
            prompt_text,
            max_length=self.max_source_length,
            truncation=True,
            add_special_tokens=False,
        )
        full_ids = self.tokenizer(
            full_text,
            max_length=self.max_source_length + self.max_target_length,
            truncation=True,
            add_special_tokens=False,
        )

        input_ids = full_ids["input_ids"]
        prompt_len = len(prompt_ids["input_ids"])
        labels = [-100] * prompt_len + input_ids[prompt_len:]
        if len(labels) != len(input_ids):
            labels = labels[:len(input_ids)]

        return {
            "input_ids": input_ids,
            "attention_mask": full_ids["attention_mask"],
            "labels": labels,
        }

    def _parse_messages(self, raw: Any) -> List[Dict[str, str]]:
        if isinstance(raw, str):
            raw = json.loads(raw)
        if isinstance(raw, list):
            return [{"role": m["role"], "content": m["content"]} for m in raw]
        raise ValueError("prompt_column must be a message list or JSON string")

    def _parse_response(self, raw: Any) -> Dict[str, str]:
        if isinstance(raw, str):
            raw = json.loads(raw)
        return {"role": raw.get("role", "assistant"), "content": raw["content"]}


def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def prepare_datasets(data_args, tokenizer, training_args) -> Tuple[
    Optional[FeynmanSFTDataset],
    Optional[FeynmanSFTDataset],
    DataCollatorForSeq2Seq,
]:
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        pad_to_multiple_of=8,
    )

    train_dataset = None
    eval_dataset = None

    if training_args.do_train and data_args.train_file:
        train_data = load_jsonl(data_args.train_file)
        train_dataset = FeynmanSFTDataset(train_data, tokenizer, data_args)

    if training_args.do_eval and data_args.validation_file:
        eval_data = load_jsonl(data_args.validation_file)
        eval_dataset = FeynmanSFTDataset(eval_data, tokenizer, data_args)

    return train_dataset, eval_dataset, data_collator
