def merge_srt(srt_name):
    sub_list = []
    with open('output_srt/vocal.srt', 'r') as f:
        vocal_srt = f.readlines()
        for i in range(len(vocal_srt)-2):
            if vocal_srt[i].rstrip().isdigit():
                if vocal_srt[i+2].startswith('Error'):
                    continue
                else:
                    sub_list.append(vocal_srt[i+1] + vocal_srt[i+2])
                i+=3

    with open('output_srt/environment.srt', 'r') as f:
        env_srt = f.readlines()
        for i in range(len(env_srt)-2):
            if env_srt[i].rstrip().isdigit():
                if '연설' in env_srt[i+2]:
                    continue
                else:
                    sub_list.append(env_srt[i+1] + env_srt[i+2])
                    i+=3

    sub_list.sort()
    idx = 1
    with open('output_srt/'+ srt_name +'.srt', 'w', encoding='utf-8') as f:
        for i in sub_list:
            f.write(str(idx) +'\n')
            f.write(i)
            idx += 1
    print("---- Finish Merge srt files ----")