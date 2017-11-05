import wave
import struct
import sys
import argparse


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
    elif params.sampwidth == 4:
        mask = (1 << 32) - (1 << num_lsb)
        sample_format = "{}I".format(samples_num)
    else:
        print("Unsupported Format")

    max_bytes_hide = (samples_num * num_lsb) // 8
    print("You can hide only {} bytes".format(max_bytes_hide - 4))



    sound_data = struct.unpack(sample_format, frames)

    with open(file_to_hide, "rb") as f:
        input_data = f.read()
    print("Your files: {} bytes".format(len(input_data)))

    if len(input_data) > max_bytes_hide - 4:
        print("ERROR, too big file")
        sys.exit(2)

    input_data = struct.pack('I', len(input_data)) + input_data
    bit_input_data = bits(input_data)

    res_data = []
    for i in range(len(sound_data)):
        if i < (len(input_data) * 8) / num_lsb:
            buffer = 0
            buffer_count = 0
            while buffer_count < num_lsb:
                try:
                    buffer = buffer << 1 | next(bit_input_data)
                    buffer_count += 1
                except StopIteration:
                    buffer = buffer << 1 | 0
                    buffer_count += 1

            res_data.append(struct.pack(
                sample_format[-1], (sound_data[i] & mask) | buffer))
        else:
            res_data.append(struct.pack(sample_format[-1], sound_data[i]))

    sound_steg = wave.open(output_file, "w")
    sound_steg.setparams(params)
    sound_steg.writeframes(b"".join(res_data))
    sound_steg.close()
    print("hide done!")


def recover(input_file, output_file, num_lsb):
    in_sound = wave.open(input_file, "r")
    params = in_sound.getparams()
    samples_num = params.nframes * params.nchannels

    if params.sampwidth == 1:
        sample_format = "{}B".format(samples_num)
    elif params.sampwidth == 2:
        sample_format = "{}H".format(samples_num)
    elif params.sampwidth == 4:
        sample_format = "{}I".format(samples_num)
    else:
        print("Unsupported Format")
    mask = (1 << num_lsb) - 1

    raw_data = list(
        struct.unpack(
            sample_format,
            in_sound.readframes(
                params.nframes)))

    # Буфер - отсаток считывания если нечетное количество LSB
    res_data = extract_data(mask, raw_data, num_lsb)
    with open(output_file, 'wb') as f:
        f.write(res_data)
    print("recover done!")

def extract_data(mask, raw_data, num_lsb):
    data_len, index, buffer, buffer_length = calculate_length(
        mask, raw_data, num_lsb)
    res_data = b''
    recovered_bytes = 0
    while recovered_bytes < data_len:
        buffer = buffer << num_lsb | (raw_data[index] & mask)
        index += 1
        buffer_length += num_lsb
        while buffer_length >= 8:
            res_data += struct.pack("B", buffer >> (buffer_length - 8))
            buffer = buffer & ((1 << (buffer_length - 8)) - 1)
            buffer_length -= 8
            recovered_bytes += 1
    return res_data

def calculate_length(mask, raw_data, num_lsb):
    buffer = 0
    buffer_length = 0
    data_len_bytes = []
    index = 0
    recovered_bytes = 0
    while recovered_bytes < 4:
        buffer = buffer << num_lsb | (raw_data[index] & mask)
        index += 1
        buffer_length += num_lsb
        while buffer_length >= 8:
            data_len_bytes.append(buffer >> (buffer_length - 8))
            buffer = buffer & ((1 << (buffer_length - 8)) - 1)
            buffer_length -= 8
            recovered_bytes += 1
    data_len = struct.unpack('<I', bytes(data_len_bytes[:4]))[0]

    return data_len, index, buffer, buffer_length


def bits(bytes_data):
    for b in bytes_data:
        for i in range(7, -1, -1):
            yield (b >> i) & 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--hide', help='To hide data in a sound file',action="store_true")
    parser.add_argument('--rec', help = 'To recover data from a sound file',action="store_true")
    parser.add_argument('-s', '--sound', help = 'Path to a .wav file')
    parser.add_argument('-f', '--file', help ='Path to a file to hide in the sound file')
    parser.add_argument('-o', '--output', help= 'Path to an output file')
    parser.add_argument('-n', '--LSBs', help='How many LSBs to use', type=int, default=1)

    args = parser.parse_args()

    if args.hide and args.sound and args.file and args.output:
        hide(args.sound, args.file, args.output, args.LSBs)
    if args.rec and args.sound and args.output:
        recover(args.sound, args.output, args.LSBs)

    # hide("song_short2.wav", "pal1.bmp", "output.wav", 16)
    # recover("output.wav", "output.bmp", 16)
