import os
import shutil
from separate_audio import separate_audio
from sound_extract import sound_extract
from audio_segments import silenceRemoval
from audio_tagging import *
from srt_merge import merge_srt

if __name__ == '__main__':
    os.makedirs('output_audio')
    sound_extract()
    
    file_list = os.listdir("output_audio")
    os.makedirs('output_audio/vocal')
    os.makedirs('output_audio/environment')

    num = 0
    for i in file_list:    
        separate_audio(i.split("/")[-1])
        silenceRemoval("output_audio/vocal/vocal.wav", num)
        silenceRemoval("output_audio/environment/environment.wav", num)
        num += 1
        print("---- Finish Audio Segmente ----")

    to_do = ['environment', 'vocal']
    for work in to_do:
        srt_file_name = 'output_srt/' + work + '.srt'
        audio_directory = 'output_audio/' + work + '/'
        video_file_name = work
        audio_file_name = os.path.join(audio_directory, video_file_name + ".wav")
        file_handle = open(srt_file_name, "a+")

        for file in tqdm(sort_alphanumeric(os.listdir(audio_directory))):
            audio_segment_path = os.path.join(audio_directory, file)
            
            if work == 'environment':
                if audio_segment_path.split(os.sep)[-1] != audio_file_name.split(os.sep)[-1]:
                    event_audio(audio_segment_path, file_handle)

            if work == 'vocal':
                if audio_segment_path.split(os.sep)[-1] != audio_file_name.split(os.sep)[-1]:
                    speech_audio(audio_segment_path, file_handle)
        
        print("\nSRT file saved to", srt_file_name)
        file_handle.close()

        print("---- Finish Create " + work + ' srt file ----')

    shutil.rmtree('output_audio')
    moive_file_name = os.listdir('input_moive')[0].split('.')[0]
    merge_srt(moive_file_name)
    print("====== Finish the Work! Check the output_srt folder =====")
    
            
    