import transformers
import torch

hf_model_id = f"meta-llama/Llama-2-70b-chat-hf"
model_config = transformers.AutoConfig.from_pretrained(hf_model_id)
bnb_config = transformers.BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

tokenizer = transformers.AutoTokenizer.from_pretrained(hf_model_id)
model = transformers.AutoModelForCausalLM.from_pretrained(
    hf_model_id,
    trust_remote_code=True,
    config=model_config,
    quantization_config=bnb_config,
    device_map="auto",
)

model.eval()

torch.no_grad()

generate_text = transformers.pipeline(
    model=model, tokenizer=tokenizer, task="text-generation"
)
