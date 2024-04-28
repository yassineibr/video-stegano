# pylint: disable=import-error,no-name-in-module
from PIL.Image import Image
from image import AbstractImageStegano
from video import VideoStegano
from audio import AbstractAudioStegano
from stegano import lsb
import wave


class MyImage(AbstractImageStegano):
    def hide(self, image: str, message: str) -> Image:
        return lsb.hide(image, message)

    def unhide(self, image: str) -> str:
        return lsb.reveal(image)


class MyAudio(AbstractAudioStegano):

    def hide(self, audio_path: str, output_audio: str, message: str):
        song = wave.open(audio_path, mode='rb') # Read frames and convert to byte array
        frame_bytes = bytearray(list(song.readframes(song.getnframes())))

        # The "secret" text message
        string = message

        # Append dummy data to fill out rest of the bytes. Receiver shall detect and remove these characters.
        string = string + int((len(frame_bytes)-(len(string)*8*8))/8) * '#'
        # Convert text to bit array
        bits = list(
            map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8, '0') for i in string])))

        # Replace LSB of each byte of the audio data by one bit from the text bit array
        for i, bit in enumerate(bits):
            frame_bytes[i] = (frame_bytes[i] & 254) | bit
        # Get the modified bytes
        frame_modified = bytes(frame_bytes)

        # Write bytes to a new wave audio file
        with wave.open(output_audio, 'wb') as fd:
            fd.setparams(song.getparams())
            fd.writeframes(frame_modified)

        song.close()

    def unhide(self, audio_path: str) -> str:
        song = wave.open(audio_path, mode='rb')
        # Convert audio to byte array
        frame_bytes = bytearray(list(song.readframes(song.getnframes())))

        # Extract the LSB of each byte
        extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
        # Convert byte array back to string
        string = "".join(chr(
            int("".join(map(str, extracted[i:i+8])), 2)) for i in range(0, len(extracted), 8))
        # Cut off at the filler characters
        decoded = string.split("###")[0]

        song.close()

        # Print the extracted text
        print("Sucessfully decoded: "+decoded)

        return decoded


if __name__ == "__main__":
    img = MyImage()
    aud = MyAudio()
    vid = VideoStegano(img, aud)
    vid.hide("./test_vid.mkv", "abcd"*10+ "a")

    print(vid.unhide("./final_video.mov"))

