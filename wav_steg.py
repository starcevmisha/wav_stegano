import wave
import struct
from bitstring import BitArray

def hide():
    num_lsb = 1

    sound = wave.open("song_short.wav")
    params = sound.getparams()
    num_frames = sound.getnframes()
    num_channels = params.nchannels
    num_samples = num_frames * num_channels
    a = sound.readframes(params.nframes)
    sound.close()

    samples_num = params.nframes * params.nchannels
    if params.sampwidth == 1:
        sample_format = "{}B".format(samples_num)
        mask = (1 << 15) - (1 << num_lsb)
    elif params.sampwidth == 2:
        mask = (1 << 15) - (1 << num_lsb)
        sample_format = "{}H".format(samples_num)
    elif params.sampwidth == 3:
        sample_format = "{}B".format(samples_num*3)



    max_bytes_hide = (samples_num * num_lsb) // 8
    print(max_bytes_hide)

    sound_data = struct.unpack(sample_format, a)

    res_data = []

    with open("pal1.bmp", "rb") as f:
        input_data = BitArray(f.read())
    print(len(input_data))
    for i in range(len(sound_data)):
        if i < len(input_data):
            res_data.append(struct.pack('H',(sound_data[i]&mask)|input_data[i]))
        else:
            res_data.append(struct.pack('H', sound_data[i]))

    print("Ok")
    sound_steg = wave.open("123.wav", "w")
    sound_steg.setparams(params)
    sound_steg.writeframes(b"".join(res_data))
    sound_steg.close()

##############################33
def recover():
    in_sound = wave.open("123.wav", "r")
    params = in_sound.getparams()
    num_lsb = 1
    samples_num = params.nframes * params.nchannels
    if params.sampwidth == 1:
        sample_format = "{}B".format(samples_num)
    elif params.sampwidth == 2:
        sample_format = "{}H".format(samples_num)
    elif params.sampwidth == 3:
        sample_format = "{}B".format(samples_num*3)
    mask = (1 << num_lsb) - 1

    res_data = b''
    raw_data = list(struct.unpack(sample_format, in_sound.readframes(params.nframes)))
    buffer = 0
    for i in range(len(raw_data)):
        if i<9000:
            if i %8 == 0 and i!=0:
                res_data+=struct.pack('1B', buffer)
                buffer = 0
            buffer = buffer<<1|raw_data[i]&mask
        else:
            break
    with open('output.bmp', 'wb') as f:
        f.write(res_data)


if __name__ == "__main__":
    hide()
    recover()
