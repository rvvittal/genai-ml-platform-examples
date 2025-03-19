import ray
from ray import serve
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import librosa

@serve.deployment
class WhisperModel:
    def __init__(self, model_id: str):
        self.processor = WhisperProcessor.from_pretrained(model_id)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_id)
    
    async def __call__(self, request):
        data = await request.json()
        file_path = data.get("file_path")

        if not file_path:
            return {"error": "No file_path provided"}
        
        try:
            # Load the audio file
            audio, sr = librosa.load(file_path, sr=16000)

            # Process the audio with Whisper
            input_features = self.processor(audio, sampling_rate=16000, return_tensors="pt").input_features
            generated_ids = self.model.generate(input_features)
            transcription = self.processor.batch_decode(generated_ids, skip_special_tokens=True)

            return {"transcription": transcription[0]}
        except Exception as e:
            return {"error": str(e)}

app = WhisperModel.bind(model_id="openai/whisper-tiny")
