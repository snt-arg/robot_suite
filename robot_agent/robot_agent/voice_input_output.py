import os
from dotenv import load_dotenv


from std_msgs.msg import String

from rclpy.node import Node

import time

import speech_recognition as sr
from piper import PiperVoice, SynthesisConfig
import pyaudio


load_dotenv()  # This loads the variables from .env file


########################################## Voice Input Output Node ############################################################################
class VoiceInOut(Node):

    # Topic to publish the user's textual query
    user_query_topic = "/user_query"

    # Topic to receive the LLM's textual responses
    llm_response_topic = "/llm_response"

    # Service to request enabling of audio input for commands
    input_audio_service = "/input_audio_service"

    # Service to request enabling of audio output for responses
    output_audio_service = "/output_audio_service"

    # Audio configuration
    format = pyaudio.paInt16
    rate = 44100
    channels = 1

    voice_gender = "female"  # or male

    # Boolean variable to decide if the node should listen for audio user input
    can_listen = True

    # Boolean variable to decide if the node should speak out loud the LLM responses
    can_talk = True

    def __init__(self):
        super().__init__("VoiceInOut_Node")

        ##### PUBLISHERS AND SUBSCRIBERS
        self.llm_response_sub = None
        self.user_query_pub = None

        # INITIALIZE AUDIO SPEECH RECOGNITION

        # ---> Initialize variable to decide when to recognize speech
        self.stop_listening = None

        # ---> Initialize speech-to-text recognizer
        self.stt_recognizer = sr.Recognizer()
        self.stt_recognizer.pause_threshold = (
            1.5  # seconds of non-speaking audio before a phrase is considered complete
        )

        # ---> Initialize microphone for speech input
        tmp_mic = sr.Microphone(sample_rate=22050)
        with tmp_mic as source:
            self.stt_recognizer.adjust_for_ambient_noise(source, duration=2)
        self.get_logger().debug("Microphone calibrated.")

        self.stt_mic = sr.Microphone(sample_rate=22050)

        self.start_listening()

        ##### INITIALIZE TEXT-TO-SPEECH ENGINE
        # ---> Models
        self.model_names = {
            "female": "en_US-amy-medium.onnx",
            "male": "en_US-kusal-medium.onnx",
        }
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(
            current_file_dir,
            "models",
            self.voice_gender,
            self.model_names[self.voice_gender],
        )

        # ---> Load TTS voice with configuration
        self.tts_voice = PiperVoice.load(model_path)
        self.syn_config = SynthesisConfig(
            volume=1.0,  # half as loud
            length_scale=1.0,  # twice as slow
            noise_scale=1.0,  # more audio variation
            noise_w_scale=1.0,  # more speaking variation
            normalize_audio=True,  # use raw audio from voice
        )
        self.stop_tts = False  # variable to stop TTS if needed
        self.talking = False  # variable to indicate if currently talking

        # --> Start output audio stream
        self.pya = pyaudio.PyAudio()
        self.stream = self.pya.open(
            format=self.format, channels=self.channels, rate=self.rate, output=True
        )

        ##### ANNOUNCE INITIALIZATION OF SPEECH
        self.speak("Voice input output node initialized.")
        self.speak("Listening for your commands.")

        ##### INITIALIZE PARAMETERS, PUBLISHERS, SUBSCRIPTIONS
        self._init_parameters()
        self._init_publishers()
        self._init_subscriptions()

    ########################################## Initialization Methods ############################################################################

    def _init_parameters(self) -> None:
        """Method to initialize parameters such as ROS topics' names"""
        self.declare_parameter("user_query_topic", self.user_query_topic)
        self.declare_parameter("llm_response_topic", self.llm_response_topic)

        self.declare_parameter("input_audio_service", self.input_audio_service)
        self.declare_parameter("output_audio_service", self.output_audio_service)

        self.declare_parameter("voice_gender", self.voice_gender)
        self.declare_parameter("can_listen", self.can_listen)
        self.declare_parameter("can_talk", self.can_talk)

        self.user_query_topic = (
            self.get_parameter("user_query_topic").get_parameter_value().string_value
        )

        self.llm_response_topic = (
            self.get_parameter("llm_response_topic").get_parameter_value().string_value
        )

        self.input_audio_service = (
            self.get_parameter("input_audio_service").get_parameter_value().string_value
        )
        self.output_audio_service = (
            self.get_parameter("output_audio_service")
            .get_parameter_value()
            .string_value
        )

        self.voice_gender = (
            self.get_parameter("voice_gender").get_parameter_value().string_value
        )

        self.can_listen = (
            self.get_parameter("can_listen").get_parameter_value().bool_value
        )
        self.can_talk = self.get_parameter("can_talk").get_parameter_value().bool_value

    def _init_publishers(self) -> None:
        """Method to initialize publishers"""
        self.user_query_pub = self.create_publisher(String, self.user_query_topic, 10)

    def _init_subscriptions(self) -> None:
        """Method to initialize subscriptions"""
        self.llm_response_sub = self.create_subscription(
            String, self.llm_response_topic, self.llm_response_callback, 10
        )

    ##########################################  Speech-to-text Methods ############################################################################

    def start_listening(self) -> None:
        """Method to start the listening for voice input"""
        self.get_logger().debug(
            f"Started listening for user query at {self.get_clock().now()}"
        )

        print(
            f"\n\n*************\n[\033[92m The stream {self.stt_mic.stream}\033[0m] \n\n"
        )
        self.stop_listening = self.stt_recognizer.listen_in_background(
            self.stt_mic, self.publish_audio_as_text
        )

    def pause_listening(self) -> None:
        """Method to pause the listening. this should be used when the text is being spoken out loud"""
        if self.stop_listening is not None:
            self.stop_listening(wait_for_stop=False)
            self.get_logger().debug(
                f"Stopped listening for user query at {self.get_clock().now()}."
            )
            self.stop_listening = None  # Important to set to None to close the previous context in which the mic is.

    def publish_audio_as_text(self, recognizer, audio_input):
        if self.can_listen:
            if self.talking:
                self.get_logger().debug("Currently talking; ignoring audio input.")
                return
            else:
                self.get_logger().debug(
                    "Processing audio input for speech recognition."
                )
                try:
                    user_query = recognizer.recognize_faster_whisper(
                        audio_input, language="en", model="small"
                    )
                    if user_query.strip() == "":
                        self.get_logger().debug("No speech detected.")
                    else:
                        user_query_msg = String()
                        user_query_msg.data = user_query
                        self.user_query_pub.publish(user_query_msg)
                        self.get_logger().debug(
                            f"Published user query: {user_query_msg.data}"
                        )
                except sr.UnknownValueError:
                    self.get_logger.error("Whisper could not understand audio")
                except sr.RequestError as e:
                    self.get_logger.error(
                        f"Could not request results from Whisper; {e}"
                    )

    ########################################## Text-to-speech Methods ############################################################################
    def speak(self, text: str) -> None:
        """Method to speak out loud the given text"""
        if self.can_talk:
            try:
                self.stop_tts = False
                self.talking = True
                # self.pause_listening()
                self.get_logger().debug(f"Now speaking at {self.get_clock().now()}.")

                for chunk in self.tts_voice.synthesize(
                    text, syn_config=self.syn_config
                ):
                    if self.stop_tts:
                        self.get_logger().debug("TTS aborted.")
                        break
                    self.stream.write(chunk.audio_int16_bytes)

                time.sleep(0.1)
                self.get_logger().debug(
                    f"LLM response should have been spoken out loud at {self.get_clock().now()}."
                )
                # self.start_listening()
            except Exception as e:
                self.get_logger().error(f"Error during TTS: {e}")
        else:
            self.get_logger().debug("can_talk is disabled; not speaking out loud.")

    ########################################## Subscriber callback ############################################################################
    def llm_response_callback(self, msg):
        """Callback method to receive the LLM response and save/stream it as audio"""
        self.get_logger().debug(f"Received LLM response: {msg.data}")
        self.speak(str(msg.data))

    def destroy_node(self):
        """Destructor to clean up audio resources"""
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.pya.terminate()
        except Exception as e:
            self.get_logger().warn(f"Error closing audio resources: {e}")

        # Call base class destructor
        super().destroy_node()
