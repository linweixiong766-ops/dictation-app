import asyncio
import edge_tts

async def test():
    voice = "zh-CN-XiaoxiaoNeural"
    communicate = edge_tts.Communicate("玻", voice)
    await communicate.save("scripts/test-b.mp3")
    print("Done!")

asyncio.run(test())
