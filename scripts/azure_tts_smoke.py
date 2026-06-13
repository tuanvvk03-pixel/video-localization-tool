import os

import azure.cognitiveservices.speech as speechsdk

# Read credentials from the environment — never hard-code keys in source.
#   PowerShell:  $env:AZURE_SPEECH_KEY = "..."; $env:AZURE_SPEECH_REGION = "eastus"
speech_key = os.environ.get("AZURE_SPEECH_KEY", "")
service_region = os.environ.get("AZURE_SPEECH_REGION", "eastus")
if not speech_key:
    raise SystemExit("Set AZURE_SPEECH_KEY (and optionally AZURE_SPEECH_REGION) before running this smoke test.")

out_wav = os.environ.get("AZURE_SMOKE_OUT", "azure_smoke.wav")

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_synthesis_voice_name = "vi-VN-HoaiMyNeural"
audio_config = speechsdk.audio.AudioOutputConfig(filename=out_wav)

synthesizer = speechsdk.SpeechSynthesizer(
    speech_config=speech_config,
    audio_config=audio_config
)

result = synthesizer.speak_text_async("Xin chào, đây là bản kiểm tra Azure tiếng Việt.").get()

print("reason:", result.reason)
print("result_id:", getattr(result, "result_id", None))
