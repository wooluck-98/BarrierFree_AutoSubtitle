#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import wave
import shutil
import argparse
import subprocess
import numpy as np
from tqdm import tqdm
from deepspeech import Model, version 
from segmentAudio import silenceRemoval
from audioProcessing import extract_audio, convert_samplerate
from writeToFile import write_to_file
import urllib3
import json
import base64
import requests

# Line count for SRT file
line_count = 0

def sort_alphanumeric(data):
    """Sort function to sort os.listdir() alphanumerically
    Helps to process audio files sequentially after splitting 

    Args:
        data : file name
    """
    
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    
    return sorted(data, key = alphanum_key)

def audio_tagging_func(audio_file):
    command = "CUDA_VISIBLE_DEVICES=0 python audioset_tagging_cnn/pytorch/inference.py audio_tagging --sample_rate=16000 --window_size=512 --hop_size=160 --mel_bins=64 --fmin=50 --fmax=8000 --model_type='Cnn14_16k' --checkpoint_path='audioset_tagging_cnn/Cnn14_16k_mAP=0.438.pth' --audio_path='" + audio_file + "' --cuda"
    ans = subprocess.run(command, shell=True, capture_output = True, text=True)
    tagging_result = ans.stdout.split("\n")[-2]
    # os.chdir("/content/drive/MyDrive/AutoSub")
    return tagging_result

def stt_tagging_func(audio_file):
    client_id = "q4lbl67c55"
    client_secret = "MWinqUW25K0Lpt5hq1iQfSGeVZsIs6S4QubuNaMS"
    lang = "Kor" # 언어 코드 ( Kor, Jpn, Eng, Chn )
    url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt?lang=" + lang
    data = open(audio_file, 'rb')
    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret,
        "Content-Type": "application/octet-stream"
    }
    response = requests.post(url,  data=data, headers=headers)
    rescode = response.status_code
    if(rescode == 200):
        return response.text[9:-2]
    else:
        return "Error : " + response.text
    
    
    return (str(response.data,"utf-8").split('"')[-2])

def event_audio(audio_file, file_handle):  

    global line_count
 
    infered_text = audio_tagging_func(audio_file)
    
    # File name contains start and end times in seconds. Extract that
    limits = audio_file.split(os.sep)[-1][:-4].split("_")[-1].split("-")
    
    if len(infered_text) != 0:
        line_count += 1
        write_to_file(file_handle, infered_text, line_count, limits)

def speech_audio(audio_file, file_handle):  

    global line_count
 
    infered_text = stt_tagging_func(audio_file)
    
    # File name contains start and end times in seconds. Extract that
    limits = audio_file.split(os.sep)[-1][:-4].split("_")[-1].split("-")
    
    if len(infered_text) != 0:
        line_count += 1
        write_to_file(file_handle, infered_text, line_count, limits)


def main():
    global line_count
    print("AutoSub v0.1\n")
        
    parser = argparse.ArgumentParser(description="AutoSub v0.1")
    parser.add_argument('--type', required=True,
                        help='event or Speech')
    parser.add_argument('--file', required=True,
                        help='Input video file')
    args = parser.parse_args()
        
    input_file = args.file
    print("\nInput file:", input_file)
    
    base_directory = os.getcwd()
    output_directory = os.path.join(base_directory, "output")
    audio_directory = os.path.join(base_directory, "audio")
    video_file_name = input_file.split(os.sep)[-1].split(".")[0]
    audio_file_name = os.path.join(audio_directory, video_file_name + ".wav")
    srt_file_name = os.path.join(output_directory, video_file_name + ".srt")
       
    print("Splitting on silent parts in audio file")
    silenceRemoval(audio_file_name)
    
    # Output SRT file
    file_handle = open(srt_file_name, "a+")

    print("\nRunning inference:")
    
    for file in tqdm(sort_alphanumeric(os.listdir(audio_directory))):
        audio_segment_path = os.path.join(audio_directory, file)
        
        # Dont run inference on the original audio file
        if args.type == 'event':
            if audio_segment_path.split(os.sep)[-1] != audio_file_name.split(os.sep)[-1]:
                event_audio(audio_segment_path, file_handle)
        if args.type == 'speech':
            if audio_segment_path.split(os.sep)[-1] != audio_file_name.split(os.sep)[-1]:
                speech_audio(audio_segment_path, file_handle)

            
    print("\nSRT file saved to", srt_file_name)
    file_handle.close()

    # Clean audio/ directory 
    shutil.rmtree(audio_directory)
    os.mkdir(audio_directory)
        
if __name__ == "__main__":
    main()
