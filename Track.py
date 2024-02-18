import threading

class Track:
    """
    A class to manage playing a sequence of notes.

    Attributes:
        notes_array (list): List of Note objects.
        speaker (str): Speaker to play the notes from ('l' for left, 'r' for right).
        note_idx (int): Index of the current note being played.
        stop_flag (bool): Flag to stop playing the notes.

    Methods:
        play: Start playing the sequence of notes.
        stop: Stop playing the notes.
        note: Set the index of the current note to be played.
    """

    def __init__(self, notes_array, speaker=None):
        """
        Initialize the Track object.

        Parameters:
            notes_array (list): List of Note objects.
            speaker (str): Speaker to play the notes from ('l' for left, 'r' for right).
        """
        self.notes_array = notes_array
        self.thread = None
        self.speaker = speaker
        self.note_idx = 0
        self.stop_flag = False

    def play(self):
        """
        Start playing the sequence of notes.
        """
        def play_notes():
            """
            Helper function to play the notes in a separate thread.
            """
            while True:
                if self.stop_flag:
                    break
                self.notes_array[self.note_idx].play(speaker=self.speaker)

        self.thread = threading.Thread(target=play_notes)
        self.thread.start()

    def stop(self):
        """
        Stop playing the notes.
        """
        self.stop_flag = True
        self.thread.join()

    def note(self, note_idx):
        """
        Set the index of the current note to be played.

        Parameters:
            note_idx (int): Index of the current note.
        """
        self.note_idx = note_idx
