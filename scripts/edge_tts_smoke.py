import asyncio
import edge_tts

async def main():
    c = edge_tts.Communicate(
        "Xin chào, đây là bản kiểm tra giọng tiếng Việt.",
        voice="vi-VN-HoaiMyNeural"
    )
    await c.save(r"D:\video-localization-tool\workspace\jobs\demo_job\artifacts\tts\edge_test.mp3")
    print("ok")

asyncio.run(main())
