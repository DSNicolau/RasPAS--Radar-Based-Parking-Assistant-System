import math
import numpy
import time
import pygame
import threading

pygame.init()
bits = 16
sample_rate = 44100
pygame.mixer.pre_init(sample_rate, bits)

def sine_x(amp, freq, time):
    """
    Generate a sine wave at a specific frequency and time.

    Parameters:
        amp (int): Amplitude of the sine wave.
        freq (float): Frequency of the sine wave in Hz.
        time (float): Time in seconds.

    Returns:
        int: The value of the sine wave at the specified time.
    """
    return int(round(amp * math.sin(2 * math.pi * freq * time)))

class Tone:
    """
    A class to generate and play tones.

    Methods:
        sine: Generate and play a sine wave tone.
        create_tone_from_list: Generate and play tones from a list of frequencies.
    """

    def sine(frequency, duration=1, speaker=None):
        """
        Generate and play a sine wave tone.

        Parameters:
            frequency (float): Frequency of the sine wave in Hz.
            duration (float): Duration of the tone in seconds.
            speaker (str): Speaker to play the sound from ('l' for left, 'r' for right).
        """
        num_samples = int(round(duration * sample_rate))

        # Setup our numpy array to handle 16 bit ints, which is what we set our mixer to expect with "bits" up above
        buf = numpy.zeros((num_samples, 2), dtype=numpy.int16)
        amplitude = 2 ** (bits - 1) - 1

        for s in range(num_samples):
            t = float(s) / sample_rate    # time in seconds

            sine = sine_x(amplitude, frequency, t)

            # Control which speaker to play the sound from
            if speaker == 'r':
                buf[s][1] = sine # right
            elif speaker == 'l':
                buf[s][0] = sine # left
            else:
                buf[s][0] = sine # left
                buf[s][1] = sine # right

        sound = pygame.sndarray.make_sound(buf)
        one_sec = 1000 # Milliseconds
        sound.play(loops=1, maxtime=int(duration * one_sec))
        time.sleep(duration)

    @staticmethod
    def create_tone_from_list(frequency_array, duration=1):
        """
        Generate and play tones from a list of frequencies.

        Parameters:
            frequency_array (list): List of frequencies in Hz.
            duration (float): Duration of each tone in seconds.
        """
        tone_threads = []

        for freq in frequency_array:
            thread = threading.Thread(target=Tone.sine, args=[freq, duration])
            tone_threads.append(thread)

        for thread in tone_threads:
            thread.start()

        for thread in tone_threads:
            thread.join()
