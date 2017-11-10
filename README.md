# WAV Steganography
It uses least significant bit steganography to hide a file in the samples of a .wav file.
For each sample in the audio file, we overwrite the least significant bits with the data from
our file.

### How to use
requires Python 3

Run wav_steg.py with the following command line arguments:

      -h, --help            show this help message and exit
      --hide                To hide data in a sound file
      --rec                 To recover data from a sound file
      -s SOUND, --sound SOUND
                            Path to a .wav file
      -f [FILES [FILES ...]], --files [FILES [FILES ...]]
                            Path to a file(s) to hide in the sound file
      -o OUTPUT, --output OUTPUT
                            Path to an output wav file
      -n LSBS, --LSBs LSBS  How many LSBs to use
      -d DIR, --dir DIR     directory for recovered files


Examples:

    To hide pal1.bmp in song.wav:
       $ wav_steg.py --hide -s song.wav -f pal1.bmp msg.txt -o output.wav -n 4

    To recover file from output.wav:
       $ wav_steg.py --rec -s output.wav -n 4

    To know hided files:
       $ wav_steg.py --rec -s test.wav --names

    Extract specific files:
        $ wav_steg.py --rec -s test.wav --spec input.txt
