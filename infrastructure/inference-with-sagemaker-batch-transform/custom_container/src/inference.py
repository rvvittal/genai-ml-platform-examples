import os
import json
import torch

# Disable PyTorch compiler optimizations to avoid C compiler dependency
try:
    import torch._dynamo
    torch._dynamo.config.suppress_errors = True
    os.environ["TORCH_INDUCTOR_DISABLE"] = "1"
    os.environ["TORCH_COMPILE_MODE"] = "reduce-overhead"
    torch._dynamo.reset()
except ImportError:
    pass

try:
    from torch.optim.lr_scheduler import LRScheduler
except ImportError:
    from torch.optim.lr_scheduler import _LRScheduler as LRScheduler
    torch.optim.lr_scheduler.LRScheduler = LRScheduler
import logging
import pandas as pd
from pathlib import Path
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def model_fn(model_dir, context=None):
    """
    Load the model and tokenizer from the model directory.

    Parameters:
        model_dir (str): Directory where model artifacts are stored. The directory should contain a 'model_files' subdirectory with model weights, tokenizer, configuration, and label mapping.
        context (optional): Additional context passed by the inference runtime (ignored).

    Returns:
        dict: A dictionary containing the loaded model, tokenizer, the label mapping (id2label), and the device used.
    """
    print(f"model_fn called with model_dir: {model_dir}")
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        logger.info(f"Loading model from {model_dir}")
        
        # Check directory structure
        if not os.path.exists(model_dir):
            raise ValueError(f"Model directory {model_dir} does not exist")
            
        logger.info(f"Model directory contents: {os.listdir(model_dir)}")
        
        # First, check if model files are directly in the model_dir
        config_path = os.path.join(model_dir, 'config.json')
        if os.path.exists(config_path):
            model_files_dir = model_dir
            logger.info("Using model_dir directly as it contains config.json")
        else:
            # Next, check for standard SageMaker extraction paths
            potential_paths = [
                os.path.join(model_dir, 'model_files'),  # Our custom structure
                os.path.join(model_dir, 'model'),        # Common SageMaker path
                *[os.path.join(model_dir, d) for d in os.listdir(model_dir) if os.path.isdir(os.path.join(model_dir, d))]  # All subdirs
            ]
            
            model_files_dir = None
            for path in potential_paths:
                if os.path.exists(os.path.join(path, 'config.json')):
                    model_files_dir = path
                    logger.info(f"Found model files in {path}")
                    break
            
            if model_files_dir is None:
                raise ValueError(f"Could not find model files in {model_dir} or its subdirectories")
        
        # Check for CUDA availability
        try:
            # Print detailed CUDA information
            logger.info(f"PyTorch version: {torch.__version__}")
            cuda_available = torch.cuda.is_available()
            logger.info(f"CUDA available: {cuda_available}")
            
            if cuda_available:
                logger.info(f"CUDA device count: {torch.cuda.device_count()}")
                logger.info(f"CUDA version: {torch.version.cuda}")
                logger.info(f"CUDA device name: {torch.cuda.get_device_name(0)}")
                logger.info(f"CUDA device capability: {torch.cuda.get_device_capability(0)}")
                logger.info(f"CUDA device properties: {torch.cuda.get_device_properties(0)}")
                device = torch.device("cuda")
                logger.info("Using CUDA device for inference")
            else:
                # Check why CUDA is not available
                if hasattr(torch, '_C'):
                    try:
                        # Try to get more detailed error information
                        _ = torch._C._cuda_getDeviceCount()
                    except Exception as cuda_err:
                        logger.warning(f"CUDA initialization error: {str(cuda_err)}")
                
                # Check if NVIDIA drivers are installed
                try:
                    nvidia_smi = subprocess.run(['nvidia-smi'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if nvidia_smi.returncode == 0:
                        logger.info(f"NVIDIA-SMI output: {nvidia_smi.stdout}")
                    else:
                        logger.warning(f"NVIDIA-SMI error: {nvidia_smi.stderr}")
                except Exception as e:
                    logger.warning(f"Failed to run nvidia-smi: {str(e)}")
                
                logger.info("CUDA is not available, using CPU")
                device = torch.device("cpu")
        except Exception as e:
            logger.warning(f"Error checking CUDA: {str(e)}")
            device = torch.device("cpu")
            logger.info("Defaulting to CPU due to error checking CUDA")
        
        # Load model and tokenizer
        try:
            logger.info(f"Loading model from {model_files_dir}")
            model = AutoModelForSequenceClassification.from_pretrained(model_files_dir)
            tokenizer = AutoTokenizer.from_pretrained(model_files_dir)
            
            # Move model to the appropriate device
            model = model.to(device)
            logger.info(f"Model loaded and moved to {device}")
            
            # Load label mapping
            label_mapping_path = os.path.join(model_files_dir, 'label_mapping.csv')
            if os.path.exists(label_mapping_path):
                label_df = pd.read_csv(label_mapping_path)
                # Check column names and use appropriate mapping
                if 'theme' in label_df.columns and 'id' in label_df.columns:
                    id2label = {row['id']: row['theme'] for _, row in label_df.iterrows()}
                    logger.info(f"Loaded label mapping with {len(id2label)} labels using 'theme' column")
                elif 'label' in label_df.columns and 'id' in label_df.columns:
                    id2label = {row['id']: row['label'] for _, row in label_df.iterrows()}
                    logger.info(f"Loaded label mapping with {len(id2label)} labels using 'label' column")
                else:
                    # Log the actual columns for debugging
                    logger.warning(f"Label mapping CSV has unexpected columns: {label_df.columns.tolist()}")
                    # Use first column after 'id' as the label column
                    columns = label_df.columns.tolist()
                    if 'id' in columns and len(columns) > 1:
                        label_col = [col for col in columns if col != 'id'][0]
                        id2label = {row['id']: row[label_col] for _, row in label_df.iterrows()}
                        logger.info(f"Using '{label_col}' column for labels, found {len(id2label)} labels")
                    else:
                        # Fallback to model's built-in mapping
                        id2label = model.config.id2label if hasattr(model.config, 'id2label') else {}
                        logger.warning(f"Could not determine label column, using model's built-in mapping with {len(id2label)} labels")
            else:
                # Use model's built-in mapping if available
                id2label = model.config.id2label if hasattr(model.config, 'id2label') else {}
                logger.info(f"Using model's built-in label mapping with {len(id2label)} labels")
            
            return {
                'model': model,
                'tokenizer': tokenizer,
                'id2label': id2label,
                'device': device
            }
        
        except Exception as e:
            logger.error(f"Error loading model from {model_files_dir}: {str(e)}")
            logger.error(f"Model files directory contents: {os.listdir(model_files_dir)}")
            
            # Try alternative loading approach
            logger.info("Attempting to load model with alternative path structure...")
            try:
                # Try loading with explicit paths
                from transformers import PretrainedConfig, AutoConfig
                
                config = AutoConfig.from_pretrained(os.path.join(model_files_dir, 'config.json'))
                
                # Check if we're dealing with a safetensors file
                if os.path.exists(os.path.join(model_files_dir, 'model.safetensors')):
                    # Use from_pretrained with the directory, which will automatically handle safetensors
                    logger.info("Loading model using safetensors format")
                    model = AutoModelForSequenceClassification.from_pretrained(
                        model_files_dir,
                        config=config,
                    )
                else:
                    # Fall back to PyTorch format if safetensors is not available
                    logger.info("Loading model using PyTorch format")
                    model = AutoModelForSequenceClassification.from_pretrained(
                        model_files_dir,
                        config=config,
                        state_dict=torch.load(os.path.join(model_files_dir, 'pytorch_model.bin'), map_location=device)
                    )
                
                tokenizer = AutoTokenizer.from_pretrained(
                    model_files_dir,
                    tokenizer_file=os.path.join(model_files_dir, 'tokenizer.json')
                )
                
                # Move model to the appropriate device
                model = model.to(device)
                
                # Load label mapping with the same flexible approach as above
                label_mapping_path = os.path.join(model_files_dir, 'label_mapping.csv')
                if os.path.exists(label_mapping_path):
                    label_df = pd.read_csv(label_mapping_path)
                    # Check column names and use appropriate mapping
                    if 'theme' in label_df.columns and 'id' in label_df.columns:
                        id2label = {row['id']: row['theme'] for _, row in label_df.iterrows()}
                    elif 'label' in label_df.columns and 'id' in label_df.columns:
                        id2label = {row['id']: row['label'] for _, row in label_df.iterrows()}
                    else:
                        # Use first column after 'id' as the label column
                        columns = label_df.columns.tolist()
                        if 'id' in columns and len(columns) > 1:
                            label_col = [col for col in columns if col != 'id'][0]
                            id2label = {row['id']: row[label_col] for _, row in label_df.iterrows()}
                        else:
                            # Fallback to model's built-in mapping
                            id2label = model.config.id2label if hasattr(model.config, 'id2label') else {}
                else:
                    # Use model's built-in mapping if available
                    id2label = model.config.id2label if hasattr(model.config, 'id2label') else {}
                
                logger.info("Successfully loaded model with alternative approach")
                return {
                    'model': model,
                    'tokenizer': tokenizer,
                    'id2label': id2label,
                    'device': device
                }
            except Exception as alt_e:
                logger.error(f"Alternative loading also failed: {str(alt_e)}")
                raise
    
    except Exception as e:
        logger.error(f"Error in model_fn: {str(e)}")
        logger.error(f"Model directory contents: {os.listdir(model_dir)}")
        raise

def input_fn(request_body, request_content_type):
    """
    Deserialize and prepare the prediction input.
    Supports both JSON and plain text inputs.
    """
    logger.info(f"Received request with content type: {request_content_type}")
    logger.info(f"Request body type: {type(request_body)}")
    
    try:
        # Handle bytes input
        if isinstance(request_body, bytes):
            request_body = request_body.decode('utf-8')
        
        # Log sample of request body for debugging
        if isinstance(request_body, str):
            logger.info(f"Request body sample: {request_body[:200]}...")  # Log first 200 chars
        else:
            logger.info(f"Request body sample: {str(request_body)[:200]}...")
        
        # Process based on content type
        if request_content_type == 'application/json':
            input_data = json.loads(request_body)
            # Handle both string and list of strings
            if isinstance(input_data, str):
                return [input_data]
            elif isinstance(input_data, dict) and 'text' in input_data:
                return [input_data['text']]
            elif isinstance(input_data, dict) and 'inputs' in input_data:
                # Handle HuggingFace format
                return [input_data['inputs']] if isinstance(input_data['inputs'], str) else input_data['inputs']
            elif isinstance(input_data, list):
                if all(isinstance(text, str) for text in input_data):
                    return input_data
                elif all(isinstance(item, dict) and 'text' in item for item in input_data):
                    return [item['text'] for item in input_data]
            
            logger.error(f"Invalid input format: {input_data}")
            raise ValueError("Input must be a string, list of strings, or dict with 'text'/'inputs' field")
        
        elif request_content_type == 'text/plain' or request_content_type == 'text/csv':
            # For plain text, just return the text as a single-item list
            return [request_body]
        
        else:
            logger.error(f"Unsupported content type: {request_content_type}")
            raise ValueError(f"Unsupported content type: {request_content_type}. Supported: application/json, text/plain, text/csv")
            
    except Exception as e:
        logger.error(f"Error processing input: {str(e)}")
        raise

def predict_fn(input_data, model_dict, context=None):
    """
    Apply model to the input data.

    Parameters:
        input_data: List of text strings to classify
        model_dict (dict): Dictionary containing the model and tokenizer
        context (optional): Additional context passed by the inference runtime (ignored)

    Returns:
        List of prediction results, one for each input text
    """
    try:
        # Ensure PyTorch compiler optimizations are disabled
        try:
            import torch._dynamo
            torch._dynamo.config.suppress_errors = True
            if not os.environ.get("TORCH_INDUCTOR_DISABLE"):
                os.environ["TORCH_INDUCTOR_DISABLE"] = "1"
                logger.info("Explicitly disabled PyTorch Inductor in predict_fn")
        except ImportError:
            pass
            
        model = model_dict['model']
        tokenizer = model_dict['tokenizer']
        id2label = model_dict['id2label']
        device = model_dict['device']
        
        logger.info(f"Processing {len(input_data)} inputs")
        
        batch_size = 32  # Adjust based on your model and memory requirements
        all_results = []
        
        # Process in batches
        for i in range(0, len(input_data), batch_size):
            batch = input_data[i:i + batch_size]
            
            # Tokenize batch
            inputs = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Perform inference
            with torch.no_grad():
                outputs = model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                top_k_values, top_k_indices = torch.topk(predictions, k=3, dim=1)
            
            # Format batch results
            for text_scores, text_indices in zip(top_k_values.cpu(), top_k_indices.cpu()):
                text_results = []
                for score, idx in zip(text_scores, text_indices):
                    text_results.append({
                        'theme': id2label[idx.item()],
                        'confidence': float(score.item())  # Ensure JSON serializable
                    })
                all_results.append(text_results)
        
        return all_results
        
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        raise

def output_fn(prediction_output, accept):
    """
    Serialize and prepare the prediction output.
    Ensures all values are JSON serializable.
    """
    logger.info(f"Preparing output with accept type: {accept}")
    
    try:
        if accept == 'application/json' or accept is None:
            return json.dumps(prediction_output, ensure_ascii=False)
        elif accept == 'text/csv':
            # Create a simple CSV format if needed
            if not prediction_output:
                return ""
            
            # Assuming prediction_output is a list of prediction lists
            csv_lines = []
            for predictions in prediction_output:
                themes = [pred['theme'] for pred in predictions]
                confidences = [str(pred['confidence']) for pred in predictions]
                csv_lines.append(",".join(themes) + "," + ",".join(confidences))
            
            return "\n".join(csv_lines)
        else:
            logger.warning(f"Unsupported accept type: {accept}, defaulting to application/json")
            return json.dumps(prediction_output, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"Error in output_fn: {str(e)}")
        # Fall back to string representation
        return str(prediction_output)

def batch_predict_fn(data, model_dict):
    """
    Efficiently process a large batch of texts at once, similar to the notebook approach.
    This is optimized for processing many texts in a single call.
    
    Parameters:
        data: Either a DataFrame with a 'content' column or a list of text strings
        model_dict: Dictionary containing the model and tokenizer
        
    Returns:
        List of prediction results, one for each input text
    """
    try:
        # Ensure PyTorch compiler optimizations are disabled
        try:
            import torch._dynamo
            torch._dynamo.config.suppress_errors = True
            if not os.environ.get("TORCH_INDUCTOR_DISABLE"):
                os.environ["TORCH_INDUCTOR_DISABLE"] = "1"
                logger.info("Explicitly disabled PyTorch Inductor in batch_predict_fn")
        except ImportError:
            pass
            
        model = model_dict['model']
        tokenizer = model_dict['tokenizer']
        id2label = model_dict['id2label']
        device = model_dict['device']
        
        # Convert to list of texts if DataFrame is provided
        if isinstance(data, pd.DataFrame) and 'content' in data.columns:
            texts = data['content'].tolist()
            logger.info(f"Processing DataFrame with {len(texts)} texts")
        elif isinstance(data, pd.DataFrame) and 'text' in data.columns:
            texts = data['text'].tolist()
            logger.info(f"Processing DataFrame with {len(texts)} texts (using 'text' column)")
        elif isinstance(data, list) and all(isinstance(item, dict) and 'text' in item for item in data):
            texts = [item['text'] for item in data]
            logger.info(f"Processing list of dictionaries with {len(texts)} texts")
        else:
            texts = data if isinstance(data, list) else [data]
            logger.info(f"Processing list with {len(texts)} texts")
        
        # Filter out empty texts
        if any(not text for text in texts):
            logger.warning(f"Found {sum(1 for t in texts if not t)} empty texts, filtering them out")
            texts = [text for text in texts if text]
            
        if not texts:
            logger.warning("No valid texts to process after filtering")
            return []
            
        logger.info(f"Processing {len(texts)} valid texts")
        
        # Determine optimal batch size based on device and text count
        if device.type == "cuda":
            # Adjust batch size based on text count and available GPU memory
            total_memory = torch.cuda.get_device_properties(0).total_memory
            free_memory = torch.cuda.memory_reserved(0) - torch.cuda.memory_allocated(0)
            logger.info(f"GPU total memory: {total_memory / 1e9:.2f} GB, free memory: {free_memory / 1e9:.2f} GB")
            
            # Adjust batch size based on available memory
            if free_memory > 8e9:  # More than 8GB free
                batch_size = 128
            elif free_memory > 4e9:  # More than 4GB free
                batch_size = 64
            else:  # Less memory available
                batch_size = 32
                
            # Further adjust based on text count
            if len(texts) > 1000:
                batch_size = min(batch_size, 64)  # Cap at 64 for very large datasets
        else:
            # Smaller batch size for CPU to avoid memory issues
            if len(texts) > 500:
                batch_size = 16
            else:
                batch_size = 32
            
        logger.info(f"Using batch size {batch_size} for device {device.type} with {len(texts)} texts")
        
        # Process in batches
        all_results = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        logger.info(f"Processing in {total_batches} batches of size {batch_size}")
        
        # Memory-efficient approach for large datasets
        if len(texts) > 1000 or device.type == "cpu":
            logger.info("Using memory-efficient approach for large dataset or CPU processing")
            
            # Process in smaller batches without trying to tokenize all at once
            for i in range(0, len(texts), batch_size):
                batch_end = min(i + batch_size, len(texts))
                batch = texts[i:batch_end]
                batch_num = i // batch_size + 1
                logger.info(f"Processing batch {batch_num}/{total_batches}")
                
                # Tokenize just this batch
                inputs = tokenizer(
                    batch,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt"
                ).to(device)
                
                # Perform inference
                with torch.no_grad():
                    outputs = model(**inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
                # Get top predictions
                top_k_values, top_k_indices = torch.topk(predictions, k=3, dim=1)
                
                # Format results for this batch
                for text_scores, text_indices in zip(top_k_values.cpu(), top_k_indices.cpu()):
                    text_results = []
                    for score, idx in zip(text_scores, text_indices):
                        text_results.append({
                            'theme': id2label[idx.item()],
                            'confidence': float(score.item())
                        })
                    
                    # Add predicted class (top theme)
                    predicted_class = id2label[text_indices[0].item()]
                    all_results.append({
                        'predicted_class': predicted_class,
                        'top_predictions': text_results
                    })
                
                # Clear GPU memory if using CUDA
                if device.type == "cuda":
                    del inputs, outputs, predictions, top_k_values, top_k_indices
                    torch.cuda.empty_cache()
                    
                # Log memory usage for GPU
                if device.type == "cuda" and batch_num % 10 == 0:
                    allocated = torch.cuda.memory_allocated(0) / 1e9
                    reserved = torch.cuda.memory_reserved(0) / 1e9
                    logger.info(f"GPU memory: allocated={allocated:.2f}GB, reserved={reserved:.2f}GB")
            
            logger.info(f"Completed memory-efficient processing of {len(texts)} texts")
            return all_results
        
        # Notebook-like approach: tokenize all texts at once if possible
        try:
            # For smaller datasets, try to tokenize all at once (like in notebook)
            logger.info("Using notebook-like approach: tokenizing all texts at once")
            
            # Tokenize all texts
            inputs = tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            
            # Process in batches to avoid OOM
            all_predictions = []
            for i in range(0, len(texts), batch_size):
                batch_end = min(i + batch_size, len(texts))
                batch_inputs = {k: v[i:batch_end].to(device) for k, v in inputs.items()}
                
                # Perform inference
                with torch.no_grad():
                    outputs = model(**batch_inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                    all_predictions.append(predictions)
            
            # Combine predictions
            predictions = torch.cat(all_predictions, dim=0)
            top_k_values, top_k_indices = torch.topk(predictions, k=3, dim=1)
            
            # Format results
            for text_scores, text_indices in zip(top_k_values.cpu(), top_k_indices.cpu()):
                text_results = []
                for score, idx in zip(text_scores, text_indices):
                    text_results.append({
                        'theme': id2label[idx.item()],
                        'confidence': float(score.item())
                    })
                
                # Add predicted class (top theme)
                predicted_class = id2label[text_indices[0].item()]
                all_results.append({
                    'predicted_class': predicted_class,
                    'top_predictions': text_results
                })
            
            logger.info(f"Completed notebook-like batch processing of {len(texts)} texts")
            return all_results
                
        except RuntimeError as e:
            logger.warning(f"Notebook-like approach failed with error: {str(e)}")
            logger.warning("Falling back to batch-by-batch processing")
            all_results = []
        
        # Standard batch-by-batch approach
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1
            logger.info(f"Processing batch {batch_num}/{total_batches}")
            
            # Tokenize batch
            inputs = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt"
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Perform inference
            with torch.no_grad():
                outputs = model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                top_k_values, top_k_indices = torch.topk(predictions, k=3, dim=1)
            
            # Format batch results
            for text_scores, text_indices in zip(top_k_values.cpu(), top_k_indices.cpu()):
                text_results = []
                for score, idx in zip(text_scores, text_indices):
                    text_results.append({
                        'theme': id2label[idx.item()],
                        'confidence': float(score.item())
                    })
                
                # Add predicted class (top theme)
                predicted_class = id2label[text_indices[0].item()]
                all_results.append({
                    'predicted_class': predicted_class,
                    'top_predictions': text_results
                })
        
        logger.info(f"Completed batch processing of {len(texts)} texts")
        return all_results
        
    except Exception as e:
        logger.error(f"Error during batch prediction: {str(e)}")
        raise 