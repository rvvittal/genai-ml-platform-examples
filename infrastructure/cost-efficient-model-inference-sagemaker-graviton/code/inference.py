import json
import logging
import os
from llama_cpp import Llama
from multiprocessing import cpu_count

worker_count = os.environ.get('SAGEMAKER_MODEL_SERVER_WORKERS', cpu_count())

def input_fn(request_body, request_content_type, context):
    return json.loads(request_body)

def model_fn(model_dir):
    model=Llama(
        # model_path=f'{model_dir}/Llama-3.2-3B-Instruct-Q4_0.gguf',
        model_path=f"{model_dir}/DeepSeek-R1-Distill-Llama-8B-Q5_K_S.gguf",
        verbose=False,
        n_threads=cpu_count() // int(worker_count) # Graviton has 1 vCPU = 1 physical core
    )
    logging.info("Loaded model successfully")
    return model

def predict_fn(input_data, model, context):
    response = model.create_chat_completion(
        messages=input_data
    )
    return response

def output_fn(prediction, response_content_type, context):
    return json.dumps(prediction)
