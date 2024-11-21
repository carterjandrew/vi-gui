import os
import shutil
import cv2
import torch
import argparse
import numpy as np
import math

from tqdm import tqdm

from torch.nn import functional as F
from core.utils import flow_viz
from core.pipeline import Pipeline

import warnings
warnings.filterwarnings("ignore")

# Set device for doing inference
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# No idea what this does yet except set up the enviroment
# This uses a global variable passed in as an argument to set up the enviroment
def init_exp_env():
    torch.set_grad_enabled(False)
    if torch.cuda.is_available():
        torch.backends.cudnn.enabled = True
        torch.backends.cudnn.demo = True

# Main funciton that does our interpolation???
# PPL is our model in a pipeline. No idea what this pipeline is really

def interp_imgs(ppl, ori_img0, ori_img1):
    img0 = (torch.tensor(ori_img0.transpose(2, 0, 1)).to(DEVICE) / 255.).unsqueeze(0)
    img1 = (torch.tensor(ori_img1.transpose(2, 0, 1)).to(DEVICE) / 255.).unsqueeze(0)

    n, c, h, w = img0.shape
    divisor = 2 ** (PYR_LEVEL-1+2)

    if (h % divisor != 0) or (w % divisor != 0):
        ph = ((h - 1) // divisor + 1) * divisor
        pw = ((w - 1) // divisor + 1) * divisor
        padding = (0, pw - w, 0, ph - h)
        img0 = F.pad(img0, padding, "constant", 0.5)
        img1 = F.pad(img1, padding, "constant", 0.5)

    interp_img, bi_flow = ppl.inference(img0, img1,
            time_period=TIME_PERIOID,
            pyr_level=PYR_LEVEL)
    interp_img = interp_img[:, :, :h, :w]
    bi_flow = bi_flow[:, :, :h, :w]

    overlay_input = (ori_img0 * 0.5 + ori_img1 * 0.5).astype("uint8")
    interp_img = (interp_img[0] * 255).byte().cpu().numpy().transpose(1, 2, 0)
    return interp_img

def interp_video(video_path, output_video_path):
    # Init enviroment
    init_exp_env()
    # Load in input video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f'Video file at path: {video_path} not found')
    # Get information about video we have loaded
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # Set globals for model
    global PYR_LEVEL 
    PYR_LEVEL = math.ceil(math.log2(frame_width/448) + 3)
    global TIME_PERIOID 
    TIME_PERIOID = 0.5
    # Initalize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps * 2, (frame_width, frame_height))
    # Initialize model pipeline
    model_cfg_dict = dict(
        load_pretrain = True,
        model_size = 'base',
        model_file = './checkpoints/upr-base.pkl'
    )
    ppl = Pipeline(model_cfg_dict)
    ppl.eval()
    # Intitalize first frame. Holds the previous frame so we only read next frame and have two
    _, first_frame = cap.read()
    for i in tqdm(range(total_frames - 1)):
        second_ret, second_frame = cap.read()
        if not second_ret:
            break
        # Use first and second frame in ml model to make between frame
        interp_frame = interp_imgs(ppl, first_frame, second_frame)
        # Write first frame into video
        out.write(first_frame)
        # Write generated frame into video
        out.write(interp_frame)
        # Set first frame to be second frame
        first_frame = second_frame
    # Write final frame
    out.write(first_frame)
    # Release input and output videos
    cap.release()
    out.release()

if __name__ == "__main__":
    video_path = 'demo/videos/bbb.mp4'
    output_path = 'demo/videos/output.mp4'
    interp_video(video_path, output_path)
