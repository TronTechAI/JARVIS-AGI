# ██████╗   ███████╗ ██╗    ██╗ ███████╗            ██████╗    ██████╗             ██████╗   ██████╗    ██████╗   ███████╗
# ██╔══██╗ ██╔════╝ ██║    ██║ ██╔════╝            ██╔══██╗ ██╔═══██╗          ██╔════╝ ██╔═══██╗ ██╔══██╗ ██╔════╝
# ██║    ██║ █████╗     ██║    ██║ ███████╗            ██║    ██║ ██║      ██║         ██║          ██║      ██║ ██║    ██║ █████╗  
# ██║    ██║ ██╔══╝    ╚██╗  ██╔╝ ╚════██║           ██║    ██║ ██║      ██║         ██║          ██║      ██║ ██║    ██║ ██╔══╝  
# ██████╔╝ ███████╗  ╚████╔╝  ███████║            ██████╔╝╚██████╔╝          ╚██████╗ ╚██████╔╝  ██████╔╝ ███████╗
# ╚═════╝  ╚══════╝    ╚═══╝     ╚══════╝            ╚═════╝    ╚═════╝             ╚═════╝   ╚═════╝    ╚═════╝   ╚══════╝

#  Made With 💓 By - Sree ( Devs Do Code )
#  YouTube Channel: https://www.youtube.com/@devsdocode

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

      - Support: https://buymeacoffee.com/devsdocode
      - Patreon: https://patreon.com/DevsDoCode

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

#  For any questions or concerns, reach out to us via our social media handles.
#  Our top choice for contact is Telegram: https://t.me/devsdocode
#  You can also find us on other platforms listed above. We're here to help!

#  - YouTube Channel: https://www.youtube.com/@DevsDoCode
#  - Telegram Group: https://t.me/devsdocode
#  - Discord Server: https://discord.gg/ehwfVtsAts
#  - Instagram:
#    - Personal: https://www.instagram.com/sree.shades_/
#    - Channel: https://www.instagram.com/devsdocode_/

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    - Support: https://buymeacoffee.com/devsdocode
    - Patreon: https://patreon.com/DevsDoCode

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
#  ------------------------------------------------------------------------------
#  Dive into the world of coding with Devs Do Code - where passion meets programming!
#  Make sure to hit that Subscribe button to stay tuned for exciting content!

#  Pro Tip: For optimal performance and a seamless experience, we recommend using
#  the default library versions demonstrated in this demo. Your coding journey just
#  got even better! Happy coding!
#  ----------------------------------------------------------------------------

from IMPORTS import *

while True:

    speech = listener.listen()

    speech_lower = speech.lower()
    if speech_lower.startswith("jarvis") or speech_lower.endswith("jarvis"):
        if speech_lower.startswith("jarvis"):
            speech = speech[6:].strip()
        else:
            speech = speech[:-6].strip()
        print("Updated Speech:", speech)

        history_manager.store_history(history_manager.history + [{"role": "user", "content": speech}])

        with concurrent.futures.ThreadPoolExecutor() as executor:
            response_img_or_text = executor.submit(deepInfra_TEXT.generate, [{"role": "user", "content": "Text to Classify -->" + speech}], system_prompt=BISECTORS.image_requests_v3)
            response_classifier = executor.submit(deepInfra_TEXT.generate, [{"role": "user", "content": "Text to Classify -->" + speech}], system_prompt=BISECTORS.complex_task_classifier_v6, stream=False)
            default_response = executor.submit(deepInfra_TEXT.generate, history_manager.history, system_prompt=INSTRUCTIONS.human_response_v3_AVA, stream=False)

        print("Response Classifier >> ", "\033[91m" + response_classifier.result() + "\033[0m")
        print("Image or Text Classifier >> ", "\033[91m" + response_img_or_text.result() + "\033[0m")

        if "yes" in response_img_or_text.result().lower():
            speak("Sure Sir, Generating Your Image")
            try:
                decohere_ai.generate(speech)
            except Exception as e:
                print(f"\033[91mImage generation error: {e}\033[0m")
                speak("Sorry Sir, I was unable to generate the image.")
            continue

        elif all(x in response_classifier.result().lower() for x in ("vision", "website", "call", "youtube")):
            print("\033[91mConfused with Classification. Using Default Response\033[0m")
            speak(default_response.result())
            history_manager.update_file(speech, default_response.result())

        elif "system control" in response_classifier.result().lower():
            with concurrent.futures.ThreadPoolExecutor() as executor:
                speak_future = executor.submit(speak, "Sure Sir. Setting the Required Settings")

                speech_lower = speech.lower()
                if "dark" in speech_lower or "light" in speech_lower:
                    theme = 0 if "dark" in speech_lower else 1
                    system_theme.WindowsThemeManager().set_theme(theme)
                elif any(alignment in speech_lower for alignment in ["left", "center", "centre", "right"]):
                    alignment = 0 if "left" in speech_lower else 1
                    taskbar.TaskbarCustomizer().set_alignment(alignment)
                elif "temperature" in speech_lower:
                    taskbar.TaskbarCustomizer().set_temperature_display(1)

                speak_future.result()

        elif "vision" in response_classifier.result().lower():
            speak("Analysing, Please Wait")
            image_path = camera_vision.realtime_vision()
            try:
                response_vision = deepInfra_VISION.generate(speech, system_prompt=INSTRUCTIONS.vison_realtime_v1, image_path=image_path)
                print("AI>>", response_vision)
                speak(response_vision)
            except Exception as e:
                print(f"\033[91mVision error: {e}\033[0m")
                speak("Sorry Sir, I was unable to analyse the image.")
            finally:
                if image_path and os.path.exists(image_path):
                    os.remove(image_path)

        elif "call" in response_classifier.result().lower():
            speak("Sure Sir. Calling")
            # make_call.call()

        elif "website" in response_classifier.result().lower():
            try:
                site_markdown = jenna_reader.fetch_website_content(chrome_latest_url.get_latest_chrome_url())
                response = openrouter.generate(f"METADATA: {site_markdown}\n\nQUERY: {speech}", system_prompt="Keep your responses very short and concise")
                speak(response, voice="Salli")
            except Exception as e:
                print(f"\033[91mWebsite assistant error: {e}\033[0m")
                speak("Sorry Sir, I was unable to fetch the website content.")

        else:
            print("AI>>", default_response.result())
            speak(default_response.result())
            history_manager.update_file(speech, default_response.result())

    else:
        history_manager.store_history(history_manager.history + [{"role": "user", "content": speech}])
        print("\033[93mHuman >> {}\033[0m".format(speech))

        chat_response = Hugging_Face_TEXT.generate(speech)
        print("\n\033[92mJARVIS >> {}\033[0m\n".format(chat_response))
        history_manager.update_file(speech, chat_response)
        speak(chat_response)



