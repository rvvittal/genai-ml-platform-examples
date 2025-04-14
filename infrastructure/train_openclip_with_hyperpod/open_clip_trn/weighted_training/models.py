

import torch.utils.data


from open_clip_train.train import *


def unwrap_model(model):
    if hasattr(model, 'module'):
        if hasattr(model.module, 'model'):
            return model.module.model
        else:
            return model.module
    else:
        if hasattr(model, 'model'):
            return model.model
        else:
            return model