import json
import argparse

from llama_cpp import Llama

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", type=str, default="DeepSeek-R1-Distill-Llama-70B-Q4_0.gguf")
args = parser.parse_args()

# for example, for a .16xlarge instance, set n_threads=64
llm = Llama(model_path=args.model,
            n_threads=64)

output = llm(
"Question: How to build a visually appealing website in ten steps? Answer: ",
max_tokens=512,
echo=True,
)