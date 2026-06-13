import asyncio
import edge_tts

TEXT = "Nguoi trong lang toi moi khi den 18 tuoi"
VOICE = "vi-VN-HoaiMyNeural"
OUT = r"D:\video-localization-tool\workspace\jobs\demo_job\artifacts\tts\smoke_raw.mp3"

async def main():
    c = edge_tts.Communicate(TEXT, voice=VOICE)
    await c.save(OUT)
    print("ok")

asyncio.run(main())
