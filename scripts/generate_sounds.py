"""クイズ用の短いWAV効果音を生成する。"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 44_100
AMPLITUDE = 0.42
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"


def tone(frequency: float, duration: float, volume: float = 1.0) -> list[float]:
    """クリック音を避けた、短い正弦波を作る。"""

    count = int(SAMPLE_RATE * duration)
    fade_count = max(1, int(SAMPLE_RATE * 0.012))
    samples: list[float] = []
    for index in range(count):
        envelope = min(1.0, index / fade_count, (count - index - 1) / fade_count)
        samples.append(
            math.sin(2 * math.pi * frequency * index / SAMPLE_RATE)
            * AMPLITUDE
            * volume
            * max(0.0, envelope)
        )
    return samples


def bell(frequency: float, duration: float, volume: float = 1.0) -> list[float]:
    """短く余韻が消える、ベルらしい音を作る。"""

    count = int(SAMPLE_RATE * duration)
    samples: list[float] = []
    for index in range(count):
        elapsed = index / SAMPLE_RATE
        envelope = math.exp(-11 * elapsed)
        fundamental = math.sin(2 * math.pi * frequency * elapsed)
        overtone = 0.28 * math.sin(2 * math.pi * frequency * 2.01 * elapsed)
        samples.append((fundamental + overtone) * AMPLITUDE * volume * envelope)
    return samples


def silence(duration: float) -> list[float]:
    return [0.0] * int(SAMPLE_RATE * duration)


def buzz(duration: float) -> list[float]:
    """低い2音を混ぜたブザー音を作る。"""

    first = tone(145, duration, 0.9)
    second = tone(172, duration, 0.55)
    return [a + b for a, b in zip(first, second)]


def write_wav(path: Path, samples: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = b"".join(
        struct.pack("<h", max(-32768, min(32767, round(sample * 32767))))
        for sample in samples
    )
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(frames)


def main() -> None:
    pingpong = bell(1_318.5, 0.22, 0.82) + silence(0.06) + bell(1_046.5, 0.36)
    wrong = buzz(0.62)
    write_wav(OUTPUT_DIR / "correct_pingpong.wav", pingpong)
    write_wav(OUTPUT_DIR / "wrong_buzz.wav", wrong)


if __name__ == "__main__":
    main()
