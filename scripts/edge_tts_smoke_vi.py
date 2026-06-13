import asyncio
import edge_tts

TEXT = "Người trong làng tôi mỗi khi đến 18 tuổi."
VOICE = "vi-VN-HoaiMyNeural"
OUT = r"D:\video-localization-tool\workspace\jobs\demo_job\artifacts\tts\smoke_vi.mp3"

async def main():
    c = edge_tts.Communicate(TEXT, voice=VOICE)
    await c.save(OUT)
    print("ok")

asyncio.run(main())
