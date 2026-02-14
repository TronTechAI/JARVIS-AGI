import os
import pygame

def speak(text: str, voice: str = 'en-US-JennyNeural', subtitle_file: str = 'Subtitles_File.srt') -> None:
    """
    Function to convert text to speech using Edge TTS.

    Args:
        text (str): The text to be spoken.
        voice (str): The voice to use for speech synthesis. Defaults to "en-US-JennyNeural".
        subtitle_file (str): The path to the subtitle file. Defaults to "Subtitles_File.srt".

    Available voices:
        - en-US-JennyNeural: Clear and professional-sounding American female voice
        - en-US-GuyNeural: Professional American male voice
        - en-GB-SoniaNeural: British female voice
    """
    # Escape quotes in text
    text = text.replace('"', '\\"')

    audio_file = f"/tmp/edge_tts_output.mp3"

    # Build and run edge-tts command
    command = f'edge-tts --voice "{voice}" --text "{text}" --write-media "{audio_file}" 2>/dev/null'
    os.system(command)

    # Play with pygame
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)

if __name__ == "__main__": 
    speak("Thank you for watching! I hope you found this video informative and helpful. If you did, please give it a thumbs up and consider subscribing to my channel for more videos like this")
