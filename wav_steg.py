import wave
import struct
import sys

def hide(input_file, file_to_hide, output_file, num_lsb):

    sound = wave.open(input_file)
    params = sound.getparams()
    frames = sound.readframes(params.nframes)
    sound.close()

    samples_num = params.nframes * params.nchannels
    if params.sampwidth == 1:
        sample_format = "{}B".format(samples_num)
        mask = (1 << 8) - (1 << num_lsb)
    elif params.sampwidth == 2:
        mask = (1 << 16) - (1 << num_lsb)
        sample_format = "{}H".format(samples_num)
    elif params.sampwidth == 3:
        mask = (1 << 24) - (1 << num_lsb)
        sample_format = "{}B".format(samples_num * 3)



    max_bytes_hide = (samples_num * num_lsb) // 8
    print("You can hide only {} bytes".format(max_bytes_hide - 4))

    sound_data = struct.unpack(sample_format, frames)

    with open(file_to_hide, "rb") as f:
        input_data = f.read()
    print("Your files: {} bytes".format(len(input_data)))
    input_data = struct.pack('I',len(input_data)) + input_data
    bit_input_data = bits(input_data)

    res_data = []
    t = 0
    for i in range(len(sound_data)):
        if i < len(input_data)*8/num_lsb:
            buffer = 0
            buffer_count = 0
            while buffer_count < num_lsb:
                try:
                    buffer = buffer <<1 | next(bit_input_data)
                    buffer_count +=1
                    t+=1
                except StopIteration:
                    buffer = buffer << 1 | 0
                    buffer_count += 1

            print(mask)
            res_data.append(struct.pack(sample_format[-1], (sound_data[i] & mask) | buffer))
        else:
            res_data.append(struct.pack(sample_format[-1], sound_data[i]))

    sound_steg = wave.open(output_file, "w")
    sound_steg.setparams(params)
    sound_steg.writeframes(b"".join(res_data))
    sound_steg.close()
    print("hide done!")


def recover(input_file, num_lsb):
    in_sound = wave.open(input_file, "r")
    params = in_sound.getparams()
    samples_num = params.nframes * params.nchannels

    if params.sampwidth == 1:
        sample_format = "{}B".format(samples_num)
    elif params.sampwidth == 2:
        sample_format = "{}H".format(samples_num)
    elif params.sampwidth == 3:
        sample_format = "{}B".format(samples_num * 3)
    mask = (1 << num_lsb) - 1

    raw_data = list(struct.unpack(sample_format, in_sound.readframes(params.nframes)))

    data_len = calculate_length(mask, raw_data, num_lsb)
    # res_data = extract_data(data_len, mask, raw_data)
    # with open('output.bmp', 'wb') as f:
    #     f.write(res_data)
    # print("recover done!")


def extract_data(data_len, mask, raw_data):
    buffer = 0
    res_data = b''
    for i in range(32, data_len * 8 + 33):
        if i % 8 == 0 and i != 32:
            res_data += struct.pack('1B', buffer)
            buffer = 0
        buffer = buffer << 1 | raw_data[i] & mask
    return res_data

def calculate_length(mask, raw_data, num_lsb):
    buffer = 0
    buffer_length = 0
    data_len_bytes = []
    index = 0
    recovered_bytes = 0
    while recovered_bytes < 4:
        buffer = buffer << num_lsb |(raw_data[index] & mask)
        index += 1
        buffer_length += num_lsb
        while buffer_length >= 8:
            data_len_bytes.append(buffer % (1 << 8))
            buffer >>= 8
            buffer_length -=8
            recovered_bytes += 1


    # buffer = 0
    # data_len_bytes = []
    # for i in range(32//num_lsb):
    #     if i % 8 == 0 and i != 0:
    #         data_len_bytes.append(buffer)
    #         buffer = 0
    #     buffer = buffer << num_lsb | raw_data[i] & mask
    # data_len_bytes.append(buffer)
    data_len = struct.unpack('<I', bytes(data_len_bytes))[0]
    print(data_len)
    return data_len

def bits(bytes_data):
    for b in bytes_data:
        for i in range(7,-1,-1):
            yield (b >> i) & 1


if __name__ == "__main__":
    hide("song_short2.wav", "pal1.bmp", "output.wav", 3)
    recover("output.wav", 3)

