"""
Kubeflow 서버 (48GB VRAM) 에서 실행하는 개인화 학습 스크립트.

실행 방법:
    python train_personal.py \
        --student_id student_001 \
        --data_path qa_student_001.jsonl \
        --output_dir ./output/student_001

필요 패키지 (Kubeflow 노트북 첫 셀에서 실행):
    pip install transformers peft trl bitsandbytes datasets accelerate

가이드라인:
    - 데이터 최소 50개 이상 확보 후 실행
    - 에포크 3 기준 48GB에서 약 10~30분 소요
    - 학습 완료 후 output_dir/final 에 모델 저장됨
    - 로컬로 가져와서 ollama에 등록 필요
"""

import argparse
import json
import os

import torch
from datasets import Dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from trl import SFTConfig, SFTTrainer

# ── 설정 ──────────────────────────────────────────────
BASE_MODEL = "LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct"
MIN_SAMPLES = 50

LORA_CONFIG = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,                          # rank: 높을수록 표현력↑ 메모리↑
    lora_alpha=32,                 # scaling factor (보통 r*2)
    lora_dropout=0.05,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    bias="none",
)

TRAIN_CONFIG = SFTConfig(
    num_train_epochs=3,            # 데이터 적으면 5까지 올려도 됨
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4, # 유효 배치 = 4*4 = 16
    learning_rate=2e-4,
    warmup_ratio=0.1,
    lr_scheduler_type="cosine",
    bf16=True,
    max_seq_length=2048,
    save_strategy="epoch",
    logging_steps=10,
    report_to="none",
)
# ──────────────────────────────────────────────────────


def load_dataset(data_path):
    pairs = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line.strip())
            pairs.append({
                "text": (
                    f"### 질문\n{item['question']}\n\n"
                    f"### 답변\n{item['answer']}"
                )
            })
    return Dataset.from_list(pairs)


def train(student_id, data_path, output_dir):
    dataset = load_dataset(data_path)
    print(f"[{student_id}] 데이터 {len(dataset)}개 로드")

    if len(dataset) < MIN_SAMPLES:
        print(f"데이터 부족 ({len(dataset)}/{MIN_SAMPLES}). 학습 중단.")
        return

    # 4bit 양자화 (48GB에서도 효율적으로 사용)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    print("모델 로드 중...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    model = get_peft_model(model, LORA_CONFIG)
    model.print_trainable_parameters()

    final_dir = os.path.join(output_dir, "final")
    TRAIN_CONFIG.output_dir = output_dir

    trainer = SFTTrainer(
        model=model,
        args=TRAIN_CONFIG,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )

    print("학습 시작...")
    trainer.train()
    trainer.save_model(final_dir)
    tokenizer.save_pretrained(final_dir)
    print(f"학습 완료 → {final_dir}")
    print()
    print("=" * 50)
    print("다음 단계: GGUF 변환 후 로컬로 가져오기")
    print(f"  cd {final_dir}")
    print(f"  python convert_hf_to_gguf.py . --outfile {student_id}.gguf --outtype q4_k_m")
    print(f"  # 로컬로 복사 후:")
    print(f"  # python model_manager.py --register {student_id} --gguf {student_id}.gguf")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--student_id", required=True, help="학생 ID")
    parser.add_argument("--data_path", required=True, help="JSONL 데이터 경로")
    parser.add_argument("--output_dir", required=True, help="모델 저장 경로")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    train(args.student_id, args.data_path, args.output_dir)
