
import torch.utils.data

from open_clip_train.data import *
from open_clip_train.train import *

from open_clip.factory import  _natural_key
from pathlib import Path
import torch_xla.core.xla_model as xm
import torch_xla.distributed.parallel_loader as pl
import torch_xla.distributed.xla_backend

torch.cuda.is_bf16_supported = lambda: True

def scan_model_configs():
    _MODEL_CONFIG_PATHS = [Path(__file__).parent / f"cfg/"]
    _MODEL_CONFIGS = {}
    config_ext = ('.json',)
    config_files = []
    for config_path in _MODEL_CONFIG_PATHS:
        if config_path.is_file() and config_path.suffix in config_ext:
            config_files.append(config_path)
        elif config_path.is_dir():
            for ext in config_ext:
                config_files.extend(config_path.glob(f'*{ext}'))

    for cf in config_files:
        with open(cf, 'r') as f:
            model_cfg = json.load(f)
            if all(a in model_cfg for a in ('embed_dim', 'vision_cfg', 'text_cfg')):
                _MODEL_CONFIGS[cf.stem] = model_cfg

    _MODEL_CONFIGS = {k: v for k, v in sorted(_MODEL_CONFIGS.items(), key=lambda x: _natural_key(x[0]))}

    return _MODEL_CONFIGS


# NON-TRAINING UTILS
def print_metric_data(metric_name, metric_value):
    print(
        METRIC_LOGS_PREFIX + ": " + metric_name + "=" + str(metric_value) + ";", flush=True
    )
