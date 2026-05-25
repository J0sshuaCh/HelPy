import threading
import whisper

def test():
    print("Trying to load whisper in thread...")
    import whisper
    print("Whisper loaded in thread")

if __name__ == "__main__":
    t = threading.Thread(target=test)
    t.start()
    t.join()
