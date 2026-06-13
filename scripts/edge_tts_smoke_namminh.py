import asyncio
import edge_tts

TEXT = "Xin chào, đây là bản kiểm tra."
VOICE = "vi-VN-NamMinhNeural"
OUT = r"D:\video-localization-tool\workspace\jobs\demo_job\artifacts\tts\smoke_namminh.mp3"

async def main():
    c = edge_tts.Communicate(TEXT, voice=VOICE)
    await c.save(OUT)
    print("ok")

asyncio.run(main())
