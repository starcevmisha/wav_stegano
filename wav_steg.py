import hashlib
import wave
import struct
import sys
import argparse
import tarfile
import os

class IncorrectFileException(Exception):
    pass

def hide(input_wav, files, output_wav, num_lsb):

    sound = wave.open(input_wav)
    params = sound.getparams()
    frames = sound.readframes(params.nframes)
    sound.close()

    mask, sample_format = get_format_and_mask(num_lsb, params)

    max_bytes_hide = (params.nframes * params.nchannels * num_lsb) // 8
    print("You can hide only {} bytes".format(max_bytes_hide - 4))
    sound_data = list(struct.unpack(sample_format, frames))
    input_data = make_tar_file(files)
    print("Your files: {} bytes".format(len(input_data)))
    if len(input_data) > max_bytes_hide - 4:
        print("ERROR, too big file")
        sys.exit(2)
    hash = hashlib.md5(input_data).digest()
    input_data = struct.pack('I', len(input_data)+len(hash)) + input_data + hash
    print(len(input_data))

    sound_data = add_data_to_sound(input_data, mask, num_lsb, sample_format, sound_data)

    sound_steg = wave.open(output_wav, "w")
    sound_steg.setparams(params)
    sound_steg.writeframes(sound_data)
    sound_steg.close()
    print("hide done!")

def recover(input_wav, num_lsb, dir, names, spec_files):
    in_sound = wave.open(input_wav)
    params = in_sound.getparams()

    _, sample_format = get_format_and_mask(num_lsb, params)
    mask = (1 << num_lsb) - 1

    raw_data = list(
        struct.unpack(
            sample_format,
            in_sound.readframes(
                params.nframes)))
    in_sound.close()
    res_data, hash = extract_data(mask, raw_data, num_lsb)
    if hashlib.md5(res_data).digest() != hash:
        print("ERROR. Something bad happens")

    extract_files_from_tar(dir, names, res_data, spec_files)

def add_data_to_sound(input_data, mask, num_lsb, sample_format, sound_data):
    bit_input_data = bits(input_data)
    for i in range(len(sound_data)):
        if i < (len(input_data) * 8) / num_lsb:
            buffer = 0
            buffer_count = 0
            while buffer_count < num_lsb:
                try:
                    buffer = buffer << 1 | next(bit_input_data)
                    buffer_count += 1
                except StopIteration:  ## Если длина файла не делится на 8
                    buffer = buffer << 1 | 0
                    buffer_count += 1
            sound_data[i] = sound_data[i] & mask | buffer
        else:
            break
    sound_data = struct.pack(sample_format, *sound_data)
    return sound_data


def extract_files_from_tar(dir, names, res_data, spec_files):
    with open('temp.tar', 'wb') as f:
        f.write(res_data)
    with tarfile.open("temp.tar", "r") as tar:
        if names:
            for name in tar.getnames():
                print(name)
        if not spec_files is None:
            for file in spec_files:
                tar.extract(file, path=dir)
        else:
            tar.extractall(dir)
    os.remove("temp.tar")

def make_tar_file(files):
    with tarfile.open("temp.tar", "w") as tar:
        for file in files:
            tar.add(file)
    with open("temp.tar", "rb") as f:
        input_data = f.read()
    os.remove("temp.tar")
    return input_data
def get_format_and_mask(num_lsb, params):
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
        raise IncorrectFileException()
    return mask, sample_format

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
    hash = res_data[-16:]
    return res_data[:-16], hash
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
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--hide', help='To hide data in a sound file',action="store_true")
    group.add_argument('--rec', help = 'To recover data from a sound file',action="store_true")
    parser.add_argument('-s', '--sound', help = 'Path to a .wav file')
    parser.add_argument('-f', '--files', help ='Path to a file(s) to hide in the sound file', nargs='*')
    parser.add_argument('-o', '--output', help= 'Path to an output wav file')
    parser.add_argument('--names', help= 'Print names of hided files',action="store_true")
    parser.add_argument('--spec', help= 'Get a specific file', nargs='*')

    parser.add_argument('-n', '--LSBs', help='How many LSBs to use', type=int, default=1)
    parser.add_argument('-d', '--dir', help='directory for recovered files', default="recovered")


    args = parser.parse_args()

    if args.hide and args.files is None:
        msg = ''
        print('Enter message: (end with ^Z or ^D)')
        for line in sys.stdin:
            msg += line
        with open("input.txt", "w") as f:
            f.write(msg)
        args.files = ["input.txt"]

    import time
    start = time.time()

    if args.hide and args.sound and args.files and args.output:
        hide(args.sound, args.files, args.output, args.LSBs)
    if args.rec and args.sound:
        recover(args.sound, args.LSBs, args.dir, args.names, args.spec)

    print("\n ### It taked {:.3} seconds".format(time.time() - start))
