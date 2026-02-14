#!/usr/bin/env python3
"""
JARVIS Desktop GUI
A simple graphical interface for JARVIS-AGI
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress warnings
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

class JarvisGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("JARVIS - AI Assistant")
        self.root.geometry("600x500")
        self.root.configure(bg='#1a1a2e')

        # Message queue for thread-safe UI updates
        self.msg_queue = queue.Queue()

        # State
        self.is_running = False
        self.modules_loaded = False

        self.setup_ui()
        self.process_queue()

    def setup_ui(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#1a1a2e')
        title_frame.pack(pady=20)

        title = tk.Label(
            title_frame,
            text="J.A.R.V.I.S",
            font=('Helvetica', 32, 'bold'),
            fg='#00d4ff',
            bg='#1a1a2e'
        )
        title.pack()

        subtitle = tk.Label(
            title_frame,
            text="Just A Rather Very Intelligent System",
            font=('Helvetica', 10),
            fg='#888888',
            bg='#1a1a2e'
        )
        subtitle.pack()

        # Status indicator
        self.status_frame = tk.Frame(self.root, bg='#1a1a2e')
        self.status_frame.pack(pady=10)

        self.status_dot = tk.Canvas(
            self.status_frame,
            width=20, height=20,
            bg='#1a1a2e',
            highlightthickness=0
        )
        self.status_dot.pack(side=tk.LEFT, padx=5)
        self.status_circle = self.status_dot.create_oval(5, 5, 15, 15, fill='#666666')

        self.status_label = tk.Label(
            self.status_frame,
            text="Idle",
            font=('Helvetica', 12),
            fg='#888888',
            bg='#1a1a2e'
        )
        self.status_label.pack(side=tk.LEFT)

        # Conversation log
        log_frame = tk.Frame(self.root, bg='#1a1a2e')
        log_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        self.log = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#0f0f1a',
            fg='#ffffff',
            insertbackground='white',
            height=15
        )
        self.log.pack(fill=tk.BOTH, expand=True)
        self.log.config(state=tk.DISABLED)

        # Input frame
        input_frame = tk.Frame(self.root, bg='#1a1a2e')
        input_frame.pack(pady=10, padx=20, fill=tk.X)

        self.input_entry = tk.Entry(
            input_frame,
            font=('Helvetica', 12),
            bg='#2a2a4e',
            fg='#ffffff',
            insertbackground='white'
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_entry.bind('<Return>', self.send_text)

        send_btn = tk.Button(
            input_frame,
            text="Send",
            command=self.send_text,
            bg='#00d4ff',
            fg='#000000',
            font=('Helvetica', 10, 'bold'),
            relief=tk.FLAT,
            padx=15
        )
        send_btn.pack(side=tk.RIGHT)

        # Control buttons
        btn_frame = tk.Frame(self.root, bg='#1a1a2e')
        btn_frame.pack(pady=20)

        self.start_btn = tk.Button(
            btn_frame,
            text="Start Listening",
            command=self.toggle_listening,
            bg='#00ff88',
            fg='#000000',
            font=('Helvetica', 12, 'bold'),
            relief=tk.FLAT,
            padx=30,
            pady=10
        )
        self.start_btn.pack(side=tk.LEFT, padx=10)

        quit_btn = tk.Button(
            btn_frame,
            text="Quit",
            command=self.quit_app,
            bg='#ff4444',
            fg='#ffffff',
            font=('Helvetica', 12, 'bold'),
            relief=tk.FLAT,
            padx=30,
            pady=10
        )
        quit_btn.pack(side=tk.LEFT, padx=10)

    def log_message(self, message, tag=None):
        """Thread-safe logging"""
        self.msg_queue.put(('log', message, tag))

    def update_status(self, status, color):
        """Thread-safe status update"""
        self.msg_queue.put(('status', status, color))

    def process_queue(self):
        """Process messages from queue"""
        try:
            while True:
                msg_type, *args = self.msg_queue.get_nowait()
                if msg_type == 'log':
                    message, tag = args
                    self.log.config(state=tk.NORMAL)
                    self.log.insert(tk.END, message + '\n')
                    self.log.see(tk.END)
                    self.log.config(state=tk.DISABLED)
                elif msg_type == 'status':
                    status, color = args
                    self.status_label.config(text=status, fg=color)
                    self.status_dot.itemconfig(self.status_circle, fill=color)
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def load_modules(self):
        """Load JARVIS modules"""
        if self.modules_loaded:
            return True

        try:
            self.update_status("Loading...", '#ffaa00')
            self.log_message("[JARVIS] Loading AI modules...")

            # Import modules directly (not from IMPORTS to avoid all the init)
            import os
            from dotenv import load_dotenv
            from groq import Groq
            from ENGINE.STT.DevsDoCode import SpeechToTextListener
            from ENGINE.TTS.edge_tts import speak
            from TOOLS import Alpaca_DS_Converser

            load_dotenv()

            self.listener = SpeechToTextListener(language="en-IN")
            self.speak_func = speak
            self.groq_client = Groq(api_key=os.environ.get('GROQ_AI'))
            self.history_manager = Alpaca_DS_Converser.ConversationHistoryManager(history_offset=700)

            self.modules_loaded = True
            self.log_message("[JARVIS] Modules loaded successfully!")
            self.update_status("Ready", '#00ff88')
            return True

        except Exception as e:
            self.log_message(f"[Error] Failed to load: {str(e)}")
            self.update_status("Error", '#ff4444')
            import traceback
            self.log_message(traceback.format_exc())
            return False

    def toggle_listening(self):
        if not self.is_running:
            self.start_listening()
        else:
            self.stop_listening()

    def start_listening(self):
        threading.Thread(target=self._start_listening_thread, daemon=True).start()

    def _start_listening_thread(self):
        if not self.load_modules():
            return

        self.is_running = True
        self.root.after(0, lambda: self.start_btn.config(text="Stop Listening", bg='#ff4444'))
        self.update_status("Listening...", '#00ff88')
        self.log_message("[JARVIS] Voice recognition started...")
        self.listen_loop()

    def stop_listening(self):
        self.is_running = False
        self.start_btn.config(text="Start Listening", bg='#00ff88')
        self.update_status("Ready", '#666666')
        self.log_message("[JARVIS] Voice recognition stopped.")

    def listen_loop(self):
        """Background listening loop"""
        try:
            while self.is_running:
                self.update_status("Listening...", '#00ff88')
                speech = self.listener.listen()

                if speech and self.is_running:
                    self.log_message(f"[You] {speech}")
                    self.update_status("Processing...", '#ffaa00')
                    self.process_input(speech)

        except Exception as e:
            self.log_message(f"[Error] {str(e)}")
            self.update_status("Error", '#ff4444')
        finally:
            self.root.after(0, lambda: self.start_btn.config(text="Start Listening", bg='#00ff88'))

    def send_text(self, event=None):
        """Send text input"""
        text = self.input_entry.get().strip()
        if text:
            self.input_entry.delete(0, tk.END)
            self.log_message(f"[You] {text}")
            threading.Thread(target=self._send_text_thread, args=(text,), daemon=True).start()

    def _send_text_thread(self, text):
        if not self.load_modules():
            return
        self.process_input(text)

    def process_input(self, text):
        """Process user input with AI"""
        try:
            self.update_status("Thinking...", '#ffaa00')

            # Get AI response using Groq
            completion = self.groq_client.chat.completions.create(
                model='llama-3.1-8b-instant',
                messages=[
                    {'role': 'system', 'content': 'You are JARVIS, a helpful AI assistant. Keep responses short and concise.'},
                    {'role': 'user', 'content': text}
                ],
                max_tokens=256
            )
            response = completion.choices[0].message.content

            if response:
                self.log_message(f"[JARVIS] {response}")
                self.history_manager.update_file(text, response)

                # Speak response
                self.update_status("Speaking...", '#00d4ff')
                try:
                    self.speak_func(response)
                except Exception as e:
                    self.log_message(f"[TTS Error] {str(e)}")

            self.update_status("Ready" if not self.is_running else "Listening...",
                             '#666666' if not self.is_running else '#00ff88')

        except Exception as e:
            self.log_message(f"[Error] {str(e)}")
            self.update_status("Error", '#ff4444')

    def quit_app(self):
        self.is_running = False
        self.root.quit()
        self.root.destroy()

    def run(self):
        self.log_message("[JARVIS] System ready.")
        self.log_message("[JARVIS] Type a message or click 'Start Listening'")
        self.log_message("")
        self.root.mainloop()


if __name__ == "__main__":
    print("Made By @DevsDoCode")
    app = JarvisGUI()
    app.run()
