import os
import json
import sys
import signal
import traceback
import boto3
import pandas as pd
from flask import Flask, request, Response
import time
import concurrent.futures
from io import StringIO

# Import inference functions from our module
from src.inference import model_fn, input_fn, predict_fn, output_fn, batch_predict_fn

# Initialize Flask app
app = Flask(__name__)

# Environment variables for batch transform settings - set with safer defaults
MAX_CONCURRENT_TRANSFORMS = int(os.environ.get('SAGEMAKER_MAX_CONCURRENT_TRANSFORMS', '1'))
BATCH_STRATEGY = os.environ.get('SAGEMAKER_BATCH_STRATEGY', 'MULTI_RECORD')
MAX_PAYLOAD_MB = int(os.environ.get('SAGEMAKER_MAX_PAYLOAD_IN_MB', '6'))

# Print environment variables for debugging
print(f"Environment: SAGEMAKER_BATCH={os.environ.get('SAGEMAKER_BATCH', 'not set')}")
print(f"Environment: MAX_CONCURRENT_TRANSFORMS={MAX_CONCURRENT_TRANSFORMS}")
print(f"Environment: BATCH_STRATEGY={BATCH_STRATEGY}")
print(f"Environment: MAX_PAYLOAD_MB={MAX_PAYLOAD_MB}")

# Get model directory from environment variable or default to /opt/ml/model
model_dir = os.environ.get('SM_MODEL_DIR', '/opt/ml/model')
print(f"Using model directory: {model_dir}")
print(f"Model directory exists: {os.path.exists(model_dir)}")
if os.path.exists(model_dir):
    print(f"Model directory contents: {os.listdir(model_dir)}")

# Global variable to store model
model_dict = None

# Load model on startup
try:
    print(f"Loading model from {model_dir}...")
    model_dict = model_fn(model_dir)
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {str(e)}")
    traceback.print_exc()
    # Exit if model loading fails in production, but continue in debug mode
    if os.environ.get('FLASK_DEBUG') != '1':
        sys.exit(1)

@app.route('/ping', methods=['GET'])
def ping():
    """
    SageMaker health check endpoint.
    Must return 200 with empty body for Sagemaker to consider the container ready.
    """
    if model_dict is None:
        print("Health check failed: model not loaded")
        return Response(response='\n', status=503)
    
    print("Health check passed")
    return Response(response='\n', status=200)

@app.route('/execution-parameters', methods=['GET'])
def execution_parameters():
    """
    Returns the recommended execution parameters for this model.
    This enables SageMaker to optimize the model execution.
    """
    params = {
        'MaxConcurrentTransforms': MAX_CONCURRENT_TRANSFORMS,
        'BatchStrategy': BATCH_STRATEGY,
        'MaxPayloadInMB': MAX_PAYLOAD_MB
    }
    
    print(f"Responding to execution-parameters: {params}")
    return Response(response=json.dumps(params), 
                  status=200,
                  mimetype='application/json')

@app.route('/invocations', methods=['POST'])
def invoke():
    """
    SageMaker invocation endpoint for batch transform.
    """
    try:
        # Get content type from headers or default to text/plain
        content_type = request.content_type or 'text/plain'
        accept_type = request.headers.get('Accept') or 'application/json'
        
        # Log request information
        print(f"Received inference request with content type: {content_type}")
        print(f"Request size: {len(request.get_data())} bytes")
        
        # Check if this is a batch manifest file (special case for optimized processing)
        if content_type == 'application/json' and request.get_data():
            try:
                data = json.loads(request.get_data())
                print(f"Parsed JSON data type: {type(data)}")
                
                if isinstance(data, dict):
                    print(f"JSON data keys: {list(data.keys())}")
                    
                    if 'batch_manifest' in data:
                        print("Detected batch manifest, processing with optimized handler")
                        return process_batch_manifest(data, accept_type)
                    elif 'all_texts_with_metadata' in data:
                        print("Detected all_texts_with_metadata, processing as batch manifest")
                        data['batch_manifest'] = True  # Add the flag to ensure proper processing
                        return process_batch_manifest(data, accept_type)
            except Exception as e:
                print(f"Error parsing JSON: {str(e)}")
                traceback.print_exc()
                # Not a batch manifest, continue with normal processing
                pass
        
        # Validate the model is loaded
        if model_dict is None:
            error_msg = "Model not loaded, cannot perform inference"
            print(error_msg)
            return Response(response=json.dumps({"error": error_msg}), 
                           status=503, 
                           mimetype='application/json')
        
        # Process input data
        try:
            input_data = input_fn(request.get_data(), content_type)
            print(f"Processed input data: {len(input_data)} items")
            
            # Make prediction
            prediction = predict_fn(input_data, model_dict)
            print(f"Generated predictions: {len(prediction)} results")
            
            # Format output
            result = output_fn(prediction, accept_type)
            
            # Return prediction result
            return Response(response=result, status=200, mimetype=accept_type)
        except Exception as e:
            error_msg = f"Error during inference processing: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            
            # Try to handle raw text as fallback
            try:
                if content_type.startswith('text/'):
                    raw_text = request.get_data().decode('utf-8')
                    print(f"Attempting fallback processing with raw text: {raw_text[:100]}...")
                    
                    # Process as simple text
                    df = pd.DataFrame({"content": [raw_text]})
                    predictions = batch_predict_fn(df, model_dict)
                    
                    # Format and return result
                    result = json.dumps({"predictions": predictions[0]})
                    return Response(response=result, status=200, mimetype='application/json')
            except Exception as fallback_error:
                print(f"Fallback processing also failed: {str(fallback_error)}")
                traceback.print_exc()
            
            # Return the original error if fallback fails
            return Response(response=json.dumps({"error": error_msg}), 
                           status=400, 
                           mimetype='application/json')
    
    except Exception as e:
        error_msg = f"Error during inference: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return Response(response=json.dumps({"error": error_msg}), 
                       status=500, 
                       mimetype='application/json')

def process_batch_manifest(manifest_data, accept_type):
    """
    Process a batch manifest file that contains all text content or references to manifest chunks.
    This allows us to process all texts at once without loading from S3 again.
    """
    try:
        print("Processing batch manifest file")
        print(f"Manifest data keys: {list(manifest_data.keys())}")
        s3_client = boto3.client('s3')
        
        # Extract S3 bucket from manifest
        s3_bucket = manifest_data.get('s3_bucket')
        
        # Check if this is a master manifest that references chunks
        if manifest_data.get('is_master_manifest'):
            print("Processing master manifest with chunks")
            manifest_chunks = manifest_data.get('manifest_chunks', [])
            output_prefix = manifest_data.get('output_prefix')
            total_texts = manifest_data.get('total_texts', 0)
            
            if not s3_bucket or not manifest_chunks or not output_prefix:
                error_msg = "Master manifest missing required fields: s3_bucket, manifest_chunks, output_prefix"
                print(error_msg)
                return Response(response=json.dumps({"error": error_msg}), 
                               status=400, 
                               mimetype='application/json')
            
            print(f"Master manifest references {len(manifest_chunks)} chunks with {total_texts} total texts")
            
            # Process each chunk and combine results
            all_results = []
            
            for i, chunk_key in enumerate(manifest_chunks):
                print(f"Processing chunk {i+1}/{len(manifest_chunks)}: {chunk_key}")
                
                # Load chunk manifest
                response = s3_client.get_object(Bucket=s3_bucket, Key=chunk_key)
                chunk_manifest = json.loads(response['Body'].read().decode('utf-8'))
                
                # Process chunk - check for new or old format
                if 'all_texts_with_metadata' in chunk_manifest:
                    chunk_results = process_text_batch(chunk_manifest.get('all_texts_with_metadata', []), model_dict, with_metadata=True)
                else:
                    # Fallback to old format
                    chunk_results = process_text_batch(chunk_manifest.get('all_texts', []), model_dict, with_metadata=False)
                
                # Save chunk results
                chunk_output_key = chunk_manifest.get('output_key')
                if chunk_output_key:
                    chunk_output_data = json.dumps(chunk_results, ensure_ascii=False)
                    s3_client.put_object(
                        Body=chunk_output_data,
                        Bucket=s3_bucket,
                        Key=chunk_output_key,
                        ContentType='application/json'
                    )
                    print(f"Saved chunk {i+1} results to s3://{s3_bucket}/{chunk_output_key}")
                
                # Add to combined results
                all_results.extend(chunk_results)
            
            # Save combined results
            combined_output_key = f"{output_prefix}/batch_results_combined.json"
            combined_output_data = json.dumps(all_results, ensure_ascii=False)
            s3_client.put_object(
                Body=combined_output_data,
                Bucket=s3_bucket,
                Key=combined_output_key,
                ContentType='application/json'
            )
            
            print(f"Saved combined results to s3://{s3_bucket}/{combined_output_key}")
            
            return Response(
                response=json.dumps({
                    "status": "success", 
                    "processed_items": len(all_results),
                    "chunks_processed": len(manifest_chunks)
                }),
                status=200,
                mimetype='application/json'
            )
        
        # Check for new format with metadata
        if 'all_texts_with_metadata' in manifest_data:
            all_texts_with_metadata = manifest_data.get('all_texts_with_metadata', [])
            output_key = manifest_data.get('output_key')
            
            if not s3_bucket or not all_texts_with_metadata or not output_key:
                error_msg = "Batch manifest missing required fields: s3_bucket, all_texts_with_metadata, output_key"
                print(error_msg)
                return Response(response=json.dumps({"error": error_msg}), 
                               status=400, 
                               mimetype='application/json')
            
            print(f"Processing manifest with {len(all_texts_with_metadata)} texts (with metadata)")
            
            # Process all texts with metadata
            start_time = time.time()
            results = process_text_batch(all_texts_with_metadata, model_dict, with_metadata=True)
            processing_time = time.time() - start_time
            
            # Save results to S3
            print(f"Saving results to S3...")
            output_data = json.dumps(results, ensure_ascii=False)
            s3_client.put_object(
                Body=output_data,
                Bucket=s3_bucket,
                Key=output_key,
                ContentType='application/json'
            )
            
            print(f"Saved batch results to s3://{s3_bucket}/{output_key}")
            print(f"Total processing time: {processing_time:.2f} seconds")
            
            # Return success response
            return Response(
                response=json.dumps({
                    "status": "success", 
                    "processed_items": len(all_texts_with_metadata),
                    "processing_time_seconds": processing_time
                }),
                status=200,
                mimetype='application/json'
            )
        
        # Handle regular manifest with all_texts (old format)
        all_texts = manifest_data.get('all_texts', [])
        output_key = manifest_data.get('output_key')
        
        if not s3_bucket or not all_texts or not output_key:
            # Check if we have s3_keys (old format) as fallback
            s3_keys = manifest_data.get('s3_keys', [])
            if s3_bucket and s3_keys and output_key:
                print(f"Using old manifest format with {len(s3_keys)} file keys")
                return process_old_manifest(manifest_data, accept_type)
            
            error_msg = f"Batch manifest missing required fields: s3_bucket, all_texts, output_key. Available keys: {list(manifest_data.keys())}"
            print(error_msg)
            return Response(response=json.dumps({"error": error_msg}), 
                           status=400, 
                           mimetype='application/json')
        
        print(f"Processing manifest with {len(all_texts)} texts (old format)")
        
        # Process all texts
        start_time = time.time()
        results = process_text_batch(all_texts, model_dict, with_metadata=False)
        processing_time = time.time() - start_time
        
        # Save results to S3
        print(f"Saving results to S3...")
        output_data = json.dumps(results, ensure_ascii=False)
        s3_client.put_object(
            Body=output_data,
            Bucket=s3_bucket,
            Key=output_key,
            ContentType='application/json'
        )
        
        print(f"Saved batch results to s3://{s3_bucket}/{output_key}")
        print(f"Total processing time: {processing_time:.2f} seconds")
        
        # Return success response
        return Response(
            response=json.dumps({
                "status": "success", 
                "processed_items": len(all_texts),
                "processing_time_seconds": processing_time
            }),
            status=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        error_msg = f"Error during batch processing: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return Response(response=json.dumps({"error": error_msg}), 
                       status=500, 
                       mimetype='application/json')

def process_text_batch(texts, model_dict, with_metadata=False):
    """
    Process a batch of texts and return the results.
    
    Args:
        texts: Either a list of strings or a list of dictionaries with metadata
        model_dict: Dictionary containing the model and tokenizer
        with_metadata: Whether the texts include metadata
        
    Returns:
        List of prediction results, one for each input text
    """
    if not texts:
        print("No texts to process")
        return []
    
    if model_dict is None:
        print("Model not loaded, cannot perform inference")
        return []
    
    print(f"Processing batch of {len(texts)} texts")
    print(f"First text sample type: {type(texts[0])}")
    if isinstance(texts[0], dict):
        print(f"First text sample keys: {list(texts[0].keys())}")
    
    # Create DataFrame based on format
    if with_metadata:
        # Extract text and metadata
        print(f"Processing with metadata. Sample text: {texts[0] if len(texts) > 0 else 'No texts'}")
        
        # Handle different possible formats
        if isinstance(texts[0], dict) and 'text' in texts[0]:
            text_list = [item.get('text', '') for item in texts]
            filenames = [item.get('filename', f'text_{i}') for i, item in enumerate(texts)]
            file_keys = [item.get('file_key', '') for item in texts]
            print(f"Extracted {len(text_list)} texts from metadata using 'text' key")
        else:
            # Try to handle unexpected format
            print(f"Warning: Unexpected format for texts with metadata. First item: {texts[0]}")
            # Try to convert to strings if not already
            text_list = [str(item) for item in texts]
            filenames = [f'text_{i}' for i in range(len(texts))]
            file_keys = [''] * len(texts)
            print(f"Converted {len(text_list)} items to strings as fallback")
        
        df = pd.DataFrame({"content": text_list})
        print(f"Created DataFrame with {len(df)} texts from metadata")
    else:
        # Old format - just a list of texts
        if isinstance(texts[0], dict):
            # Try to extract text if it's a dict
            if 'text' in texts[0]:
                text_list = [item.get('text', '') for item in texts]
                print(f"Extracted text from dict items using 'text' key")
            elif 'content' in texts[0]:
                text_list = [item.get('content', '') for item in texts]
                print(f"Extracted text from dict items using 'content' key")
            else:
                # Convert to string as fallback
                text_list = [str(item) for item in texts]
                print(f"Converted dict items to strings as fallback")
        else:
            # Should be a list of strings
            text_list = texts
            print(f"Using text list directly")
            
        df = pd.DataFrame({"content": text_list})
        print(f"Created DataFrame with {len(df)} texts from plain list")
    
    # Determine if we should use parallel processing
    use_parallel = len(df) > 50  # Only use parallel for larger datasets
    max_workers = min(4, os.cpu_count() or 1)  # Limit workers based on CPU count
    max_chunk_size = 50  # Process in chunks of this size
    
    if use_parallel and len(df) > max_chunk_size:
        print(f"Using parallel processing with {max_workers} workers for {len(df)} texts")
        
        # Split dataframe into chunks
        chunks = []
        for i in range(0, len(df), max_chunk_size):
            end_idx = min(i + max_chunk_size, len(df))
            chunks.append(df.iloc[i:end_idx])
        
        print(f"Split into {len(chunks)} chunks of ~{max_chunk_size} texts each")
        
        # Process chunks in parallel
        all_predictions = []
        
        def process_chunk(chunk_df):
            try:
                print(f"Processing chunk with {len(chunk_df)} texts")
                return batch_predict_fn(chunk_df, model_dict)
            except Exception as e:
                print(f"Error processing chunk: {str(e)}")
                traceback.print_exc()
                return [{"error": str(e)}] * len(chunk_df)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            chunk_results = list(executor.map(process_chunk, chunks))
        
        # Combine results
        for chunk_preds in chunk_results:
            all_predictions.extend(chunk_preds)
            
        print(f"Completed parallel processing of {len(all_predictions)} predictions")
    else:
        # Run inference on the entire batch
        print("Starting batch prediction...")
        inference_start_time = time.time()
        try:
            all_predictions = batch_predict_fn(df, model_dict)
            inference_time = time.time() - inference_start_time
            print(f"Completed batch prediction in {inference_time:.2f} seconds")
        except Exception as e:
            print(f"Error during batch prediction: {str(e)}")
            traceback.print_exc()
            all_predictions = [{"error": str(e)}] * len(df)
    
    # Format results
    results = []
    for i, pred in enumerate(all_predictions):
        result = {
            "text_id": i,
            "predictions": pred
        }
        
        # Add metadata if available
        if with_metadata and i < len(texts):
            result["filename"] = texts[i].get('filename', f'text_{i}') if isinstance(texts[i], dict) else f'text_{i}'
            result["file_key"] = texts[i].get('file_key', '') if isinstance(texts[i], dict) else ''
        
        results.append(result)
    
    return results

def process_old_manifest(manifest_data, accept_type):
    """
    Process a manifest file using the old format with s3_keys.
    This is kept for backward compatibility.
    """
    try:
        print("Processing manifest with old format (s3_keys)")
        s3_client = boto3.client('s3')
        
        # Extract S3 bucket and keys from manifest
        s3_bucket = manifest_data.get('s3_bucket')
        s3_keys = manifest_data.get('s3_keys', [])
        output_key = manifest_data.get('output_key')
        
        if not s3_bucket or not s3_keys or not output_key:
            error_msg = "Batch manifest missing required fields: s3_bucket, s3_keys, output_key"
            print(error_msg)
            return Response(response=json.dumps({"error": error_msg}), 
                           status=400, 
                           mimetype='application/json')
        
        print(f"Loading {len(s3_keys)} files from S3 bucket {s3_bucket}")
        
        # Load all documents into a single list
        start_time = time.time()
        all_texts = []
        
        # Use ThreadPoolExecutor for parallel file loading
        from io import StringIO
        import pandas as pd
        
        # Function to load a single file from S3
        def load_file(key):
            try:
                response = s3_client.get_object(Bucket=s3_bucket, Key=key)
                content = response['Body'].read().decode('utf-8')
                return content.strip().split('\n')
            except Exception as e:
                print(f"Error loading file {key}: {str(e)}")
                return []
        
        # Load files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(load_file, s3_keys))
        
        # Flatten results
        for result in results:
            all_texts.extend(result)
        
        load_time = time.time() - start_time
        print(f"Loaded {len(all_texts)} total text samples in {load_time:.2f} seconds")
        
        # Process the texts
        results = process_text_batch(all_texts, model_dict)
        
        # Save results to S3
        print(f"Saving results to S3...")
        output_data = json.dumps(results, ensure_ascii=False)
        s3_client.put_object(
            Body=output_data,
            Bucket=s3_bucket,
            Key=output_key,
            ContentType='application/json'
        )
        
        total_time = time.time() - start_time
        print(f"Saved batch results to s3://{s3_bucket}/{output_key}")
        print(f"Total processing time: {total_time:.2f} seconds")
        
        # Return success response
        return Response(
            response=json.dumps({
                "status": "success", 
                "processed_items": len(all_texts),
                "processing_time_seconds": total_time,
                "load_time_seconds": load_time
            }),
            status=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        error_msg = f"Error during batch processing: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        return Response(response=json.dumps({"error": error_msg}), 
                       status=500, 
                       mimetype='application/json')

# Handle SIGTERM for graceful shutdown with SageMaker
def sigterm_handler(signum, frame):
    print("Received SIGTERM. Shutting down...")
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

# Run server with Flask when in debug mode
if __name__ == '__main__':
    # For local debugging only - SageMaker will use gunicorn
    app.run(host='0.0.0.0', port=8080, debug=True) 