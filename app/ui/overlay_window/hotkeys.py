from pynput import keyboard

class HotkeyManager:
    def __init__(self, window):
        self.window = window
        self.hotkeys = None
        self.init_hotkeys()

    def init_hotkeys(self):
        def on_activate():
            self.window.assistant.send_buffer_to_llm()

        def on_toggle_record():
            self.window.toggle_recording()

        def on_toggle_collapse():
            self.window.toggle_collapsed()

        self.hotkeys = keyboard.GlobalHotKeys({
            "<alt_gr>+\\": on_activate,
            "<alt_gr>+g": on_toggle_record,
            "<alt_gr>+h": on_toggle_collapse,
        })
        self.hotkeys.start()

    def stop(self):
        if self.hotkeys:
            self.hotkeys.stop()
