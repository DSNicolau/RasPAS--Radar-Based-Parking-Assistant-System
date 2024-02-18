from utils_notes import NOTE_MAP
from Tone import Tone
import threading
import time


class Note:
    """
    A class representing a musical note.

    Attributes:
        duration (float): The duration of the note in seconds.
        is_resting (bool): Indicates whether the note is a rest or not.
        note (str): The name of the note (e.g., 'C', 'D#', 'F').
        frequency (float): The frequency of the note in Hz.

    Methods:
        play: Plays the note using a sine wave.
        rest: Creates a rest note with a specified duration.
        play_chord: Plays a chord (multiple notes) simultaneously.
    """

    def __init__(self, note, duration=1):
        """
        Initializes a Note object.

        Parameters:
            note (str): The name of the note (e.g., 'C', 'D#', 'F').
            duration (float): The duration of the note in seconds.
        """
        self.duration = duration
        if note == 'rest':
            self.is_resting = True
            return
        else:
            self.is_resting = False

        # Ensures the first character of note is uppercase
        main_note = note[0].upper()
        self.note = main_note + note[1:]
        self.frequency = NOTE_MAP[self.note]

    def play(self, speaker=None):
        """
        Plays the note using a sine wave.

        Parameters:
            speaker: Speaker object to play the note through.
        """
        if not self.is_resting:
            Tone.sine(self.frequency, duration=self.duration, speaker=speaker)
        else:
            time.sleep(self.duration)

    @staticmethod
    def rest(duration):
        """
        Creates a rest note with a specified duration.

        Parameters:
            duration (float): The duration of the rest note in seconds.
        """
        return Note('rest', duration)

    @staticmethod
    def play_chord(notes):
        """
        Plays a chord (multiple notes) simultaneously.

        Parameters:
            notes (list): A list of Note objects.
        """
        threads = []
        for note in notes:
            thread = threading.Thread(target=note.play)
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
