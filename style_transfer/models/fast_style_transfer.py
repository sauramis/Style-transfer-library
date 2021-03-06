import os
import sys
import numpy as np
import torch
import re
from torchvision import transforms
from .lib.fast_style_transfer.transformer_net import *
from .lib.fast_style_transfer.utils import *
from pathlib import Path
from utils import Utils
import torch.onnx
from urllib import request
import zipfile

class FastStyleTransfer(object):
    MODEL_DOWNLOAD_URL = "https://www.dropbox.com/s/lrvwfehqdcxoza8/saved_models.zip?dl=1"

    def __init__(self, args, device):
        self.device = device
        self.content_image = load_image(args["content_image"], scale=args["content_scale"])
        self.style_model_type = args["style_model_type"]
        self.model_dir = os.path.join(Path(os.path.abspath(__file__)).parent, "lib/fast_style_transfer/saved_models")

    def download_model(self):
        download_dest = os.path.join(self.model_dir, "saved_models.zip")

        request.urlretrieve(self.MODEL_DOWNLOAD_URL, download_dest)

        with zipfile.ZipFile(download_dest) as zf:
            zf.extractall(path=Path(self.model_dir).parent)

    def resolve_model_path(self):
        model_path = Path(os.path.join(self.model_dir, self.style_model_type + ".pth"))

        if not model_path.is_file():
            print("Model not found. Downloading.....")
            self.download_model()

        if not model_path.is_file():
            raise Exception("Model not found in the download also. Please check.")

        return model_path

    def inference(self):
        content_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Lambda(lambda x: x.mul(255))
        ])

        content_image = content_transform(self.content_image)
        content_image = content_image.unsqueeze(0).to(self.device)

        with torch.no_grad():
            style_model = TransformerNet()
            state_dict = torch.load(self.resolve_model_path())
            for k in list(state_dict.keys()):
                if re.search(r'in\d+\.running_(mean|var)$', k):
                    del state_dict[k]

            style_model.load_state_dict(state_dict)
            style_model.to(self.device)
            output = style_model(content_image).cpu()[0]

        return extract_image(output)