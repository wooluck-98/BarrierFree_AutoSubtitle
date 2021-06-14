import os
import re
import requests
import numpy as np
from tqdm import tqdm
from autosub.writeToFile import write_to_file

import librosa
import torch

from audioset_tagging_cnn.pytorch.models import *
from audioset_tagging_cnn.pytorch.pytorch_utils import move_data_to_device
from audioset_tagging_cnn.utils import config
from google_trans_new import google_translator  


line_count = 0
def sort_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    
    return sorted(data, key = alphanum_key)

def audio_tagging_func(input_file):

    # Arugments & parameters
    sample_rate = 16000
    window_size = 512
    hop_size = 160
    mel_bins = 64
    fmin = 50
    fmax = 8000
    model_type = 'Cnn14_16k'
    checkpoint_path = 'audioset_tagging_cnn/Cnn14_16k_mAP=0.438.pth'
    audio_path = input_file
    device = torch.device('cuda')
    
    classes_num = config.classes_num
    labels = config.labels

    # Model
    Model = eval(model_type)
    model = Model(sample_rate=sample_rate, window_size=window_size, 
        hop_size=hop_size, mel_bins=mel_bins, fmin=fmin, fmax=fmax, 
        classes_num=classes_num)
    
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model'])

    # Parallel
    if 'cuda' in str(device):
        model.to(device)
        print('GPU number: {}'.format(torch.cuda.device_count()))
        model = torch.nn.DataParallel(model)
    else:
        print('Using CPU.')
    
    # Load audio
    try:
        (waveform, _) = librosa.core.load(audio_path, sr=sample_rate, mono=True)

        waveform = waveform[None, :]    # (1, audio_length)
        waveform = move_data_to_device(waveform, device)

        # Forward
        with torch.no_grad():
            model.eval()
            batch_output_dict = model(waveform, None)

        clipwise_output = batch_output_dict['clipwise_output'].data.cpu().numpy()[0]
        """(classes_num,)"""

        sorted_indexes = np.argsort(clipwise_output)[::-1]
        for i in range(3):
            result = np.array(labels)[sorted_indexes[i]]
            print(result, "acc : ", sorted(clipwise_output, reverse=True)[i])
        result = np.array(labels)[sorted_indexes[0]]
        result_acc = sorted(clipwise_output, reverse=True)[0]
        result = google_translator().translate(result, lang_src='en', lang_tgt='ko')  

        if result_acc > 0.6:
            print("♪ :", result)
            return result
        else:
            return ''
    except:
        return ' '

def stt_tagging_func(audio_file):
    client_id = "write_ID"
    client_secret = "write_Secret"
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

def event_audio(audio_file, file_handle):  

    global line_count
 
    infered_text = audio_tagging_func(audio_file)
    if infered_text != "":
        infered_text = "♪ : [ " + infered_text + ' ]'
    
    # File name contains start and end times in seconds. Extract that
    limits = audio_file.split(os.sep)[-1][:-4].split("_")[-1].split("-")

    if len(infered_text) != 0:
        line_count += 1
        write_to_file(file_handle, infered_text, line_count, limits)

def speech_audio(audio_file, file_handle):  

    global line_count
 
    infered_text = stt_tagging_func(audio_file)
    print(infered_text)
    
    # File name contains start and end times in seconds. Extract that
    limits = audio_file.split(os.sep)[-1][:-4].split("_")[-1].split("-")
    
    if len(infered_text) != 0:
        line_count += 1
        write_to_file(file_handle, infered_text, line_count, limits)

# if __name__ == '__main__':
#     audio_tagging_func('output_audio/extracted_audio00.mp3')