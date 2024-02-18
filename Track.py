import threading

class Track:
    def __init__(self, notes_array, speaker=None):
        self.notes_array = notes_array
        self.thread = None
        self.speaker = speaker
        self.note_idx = 0
        self.stop_flag = False
     

    def play(self):
        def play_notes():
            while True:
                if self.stop_flag:
                    break
                self.notes_array[self.note_idx].play(speaker=self.speaker)
             

        self.thread = threading.Thread(target=play_notes)
        self.thread.start()

    def stop(self):
        self.stop_flag = True
        self.thread.join()

    def note(self, note_idx ):
        self.note_idx = note_idx
