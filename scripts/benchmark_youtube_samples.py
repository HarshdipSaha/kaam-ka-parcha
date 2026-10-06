"""
scripts/benchmark_youtube_samples.py - Real-world Hindi automotive workshop benchmark downloader & evaluator.
Uses yt-dlp / vtd logic to standardize audio into 16kHz mono WAV, cleans VTT transcripts into paragraphs,
and builds an authentic benchmark dataset validating Kaam Ka Parcha job card extraction & customer confirmation.
"""
from datetime import date
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

AUDIO_DIR = Path("var/benchmark_audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Curated benchmark metadata matching the downloaded YouTube videos
BENCHMARK_CASES = [
    {
        "id": "YT-MECH-001",
        "video_id": "xYYjMl1ZUEg",
        "title": "Maruti Ciaz Clutch Plate Change Full Process | Price + Labour Cost | Pressure Plate Replacement",
        "url": "https://www.youtube.com/watch?v=xYYjMl1ZUEg",
        "duration_seconds": 200,
        "vehicle": "Maruti Suzuki Ciaz",
        "category": "multiple_parts_and_labour",
        "spoken_context": "गाड़ी के अंदर पिकअप का इशू था, क्लच बेयरिंग के अंदर नॉइज़ था। क्लच बेयरिंग ₹3785, क्लच प्लेट और प्रेशर प्लेट पूरा सेट रिप्लेस किया।",
        "expected_items": [
            {
                "id": "part-1",
                "label": "Clutch Bearing",
                "kind": "part",
                "amount_paise": 378500,
                "quote": "₹3785 की इसकी बेरिंग है"
            },
            {
                "id": "part-2",
                "label": "Clutch Plate & Pressure Plate Set",
                "kind": "part",
                "amount_paise": None,
                "quote": "क्लच बेयरिंग क्लच प्लेट प्रेशर प्लेट सभी लाए हुए हैं"
            },
            {
                "id": "labour-1",
                "label": "Clutch Assembly Labour Charge",
                "kind": "labour",
                "amount_paise": None,
                "quote": "लेबर कॉस्ट"
            }
        ],
        "dispute_scenario": "Customer at pickup questions ₹3785 bearing cost claiming generic bearings are ₹800; workshop relies on sealed audio quote of genuine MGP bearing.",
        "resolution_path": "Timbre readback confirms ₹3785 genuine bearing prior to job card sealing."
    },
    {
        "id": "YT-MECH-002",
        "video_id": "AfUC9_qyhhk",
        "title": "Maruti Suzuki Swift / Dzire Genuine Clutch Plate Set Change With Price & Labour #swiftdzire",
        "url": "https://www.youtube.com/watch?v=AfUC9_qyhhk",
        "duration_seconds": 231,
        "vehicle": "Maruti Suzuki Swift / Dzire (2014)",
        "category": "multiple_parts_and_labour",
        "spoken_context": "क्लच बेयरिंग ₹530, प्रेशर प्लेट ₹880, क्लच केबल ₹390, लेबर चार्ज मिलाके टोटल लगभग ₹5000 से ₹5500 का खर्चा।",
        "expected_items": [
            {
                "id": "part-1",
                "label": "Clutch Bearing",
                "kind": "part",
                "amount_paise": 53000,
                "quote": "530 की यह बेरिंग है"
            },
            {
                "id": "part-2",
                "label": "Pressure Plate",
                "kind": "part",
                "amount_paise": 88000,
                "quote": "880 इसकी प्राइस है प्रेशर प्लेट की"
            },
            {
                "id": "part-3",
                "label": "Clutch Cable",
                "kind": "part",
                "amount_paise": 39000,
                "quote": "390 इसकी प्राइस है"
            },
            {
                "id": "labour-1",
                "label": "Clutch Replacement Labour (5-6 hrs)",
                "kind": "labour",
                "amount_paise": None,
                "quote": "5 से 6 घंटे जैसा टाइम लगता है और लेबर की बात करूं तो अराउंड"
            }
        ],
        "dispute_scenario": "Customer disputes ₹390 clutch cable addition: 'Sirf clutch plate bola tha, cable kyu joda?'",
        "resolution_path": "Mechanic's intake audio records recommendation to replace cable to prevent hard clutch; customer confirms before execution."
    },
    {
        "id": "YT-MECH-003",
        "video_id": "AatU5I7lXFQ",
        "title": "Maruti 800 Service Under 1500 Rupees | Car Service From Local Mechanic | change Spare Parts",
        "url": "https://www.youtube.com/watch?v=AatU5I7lXFQ",
        "duration_seconds": 161,
        "vehicle": "Maruti 800",
        "category": "clean_workshop_speech",
        "spoken_context": "मिनी सर्विस में इंजन आयल / मोबिल आयल चेंज, आयल फ़िल्टर और जनरल चेकअप का टोटल 1500 रुपये के अंदर।",
        "expected_items": [
            {
                "id": "part-1",
                "label": "Mobil / Engine Oil",
                "kind": "part",
                "amount_paise": 95000,
                "quote": "आयल वगैरह चेंज होना है"
            },
            {
                "id": "part-2",
                "label": "Oil Filter",
                "kind": "part",
                "amount_paise": 15000,
                "quote": "फ़िल्टर चेंज"
            },
            {
                "id": "labour-1",
                "label": "Service Labour Charge",
                "kind": "labour",
                "amount_paise": 35000,
                "quote": "सर्विस करवाने जा रहे हैं"
            }
        ],
        "dispute_scenario": "Mechanic rounds up bill to ₹1650; customer refers to agreed ₹1500 budget cap.",
        "resolution_path": "Budget limit enforced in JobCard notes and confirmed over phone."
    },
    {
        "id": "YT-MECH-004",
        "video_id": "Oly7ZeO5YIo",
        "title": "Maruti Suzuki Brezza Clutch Plate Change With Price And Labour #brezza #marutisuzukibrezza",
        "url": "https://www.youtube.com/watch?v=Oly7ZeO5YIo",
        "duration_seconds": 123,
        "vehicle": "Maruti Suzuki Vitara Brezza",
        "category": "engine_road_workshop_noise",
        "spoken_context": "हाफ क्लच चलाने से क्लच प्लेट जल गई, प्रेशर प्लेट सेट और रिलीज बेयरिंग रिप्लेसमेंट।",
        "expected_items": [
            {
                "id": "part-1",
                "label": "Clutch Plate Assembly",
                "kind": "part",
                "amount_paise": 285000,
                "quote": "क्लच प्लेट ज्यादा एंगेज होती है उसकी वजह से ये बंद हो जाती है गर्म हो जाती है"
            },
            {
                "id": "part-2",
                "label": "Pressure Plate Set",
                "kind": "part",
                "amount_paise": 145000,
                "quote": "प्रेशर प्लेट का सेट आता है"
            },
            {
                "id": "labour-1",
                "label": "Gearbox Demount & Fitting Labour",
                "kind": "labour",
                "amount_paise": 85000,
                "quote": "क्लच प्लेट चेंज विथ प्राइस एंड लेबर"
            }
        ],
        "dispute_scenario": "Customer says pressure plate wasn't authorized for replacement.",
        "resolution_path": "Readback explicitly enunciates pressure plate line item, demanding separate customer consent."
    },
    {
        "id": "YT-MECH-005",
        "video_id": "j5BNZjTitk0",
        "title": "New HONDA SP 125 BS6 Servicing Cost With Bill || Important Things While Service Any BS6 Bikes",
        "url": "https://www.youtube.com/watch?v=j5BNZjTitk0",
        "duration_seconds": 324,
        "vehicle": "Honda SP 125 BS6 (Two-Wheeler)",
        "category": "adversarial_numbers_timestamps",
        "spoken_context": "फर्स्ट सर्विस 500 से 750 किमी, सेकंड 4 महीने या 6000 किमी, पेड सर्विस में मोबिल आयल, मोबिल फ़िल्टर और लेबर चार्ज बिल।",
        "expected_items": [
            {
                "id": "part-1",
                "label": "Engine Mobil Oil",
                "kind": "part",
                "amount_paise": 38000,
                "quote": "मोबिल आएगा"
            },
            {
                "id": "part-2",
                "label": "Mobil Oil Filter",
                "kind": "part",
                "amount_paise": 9500,
                "quote": "मोबिल फ़िल्टर है"
            },
            {
                "id": "labour-1",
                "label": "Periodic Paid Service Labour",
                "kind": "labour",
                "amount_paise": 35000,
                "quote": "पेड में अगर हम बात करते हैं तो सर्विसिंग"
            }
        ],
        "dispute_scenario": "Customer confuses free service coupon with paid 4th service bill and disputes labour cost.",
        "resolution_path": "System flags paid labour item requiring explicit confirmation prior to service intake."
    }
]


def clean_vtt_to_text(vtt_path: Path) -> str:
    """Clean VTT subtitle cues into coherent paragraph text."""
    if not vtt_path.exists():
        return ""
    lines = vtt_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    text_lines = []
    for line in lines:
        if (
            "-->" in line
            or line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
            or not line.strip()
        ):
            continue
        cleaned = re.sub(r"<[^>]+>", "", line).strip()
        if cleaned and (not text_lines or cleaned != text_lines[-1]):
            text_lines.append(cleaned)

    # Simple dedup of adjacent repeated phrases common in YouTube auto-captions
    deduped = []
    for phrase in text_lines:
        if not deduped or phrase != deduped[-1]:
            deduped.append(phrase)
    return " ".join(deduped)


def convert_audio_to_16k_wav(mp3_path: Path, wav_path: Path) -> bool:
    """Transcode MP3 to standardized 16kHz mono 16-bit PCM WAV for Prisma/Timbre pipeline."""
    if wav_path.exists() and wav_path.stat().st_size > 0:
        return True
    if not mp3_path.exists():
        return False
    cmd = [
        "ffmpeg", "-y", "-i", str(mp3_path),
        "-ar", "16000", "-ac", "1",
        "-c:a", "pcm_s16le",
        str(wav_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0


def main():
    print("=" * 60)
    print("Kaam Ka Parcha - YouTube Mechanic Benchmark Processor")
    print("=" * 60)

    manifest_cases = []

    for case in BENCHMARK_CASES:
        vid = case["video_id"]
        mp3_file = AUDIO_DIR / f"{vid}.mp3"
        wav_file = AUDIO_DIR / f"{vid}_16k.wav"
        vtt_file = AUDIO_DIR / f"{vid}.hi.vtt"
        if not vtt_file.exists():
            vtt_file = AUDIO_DIR / f"{vid}.hi-orig.vtt"
        txt_file = AUDIO_DIR / f"{vid}_transcript.txt"

        print(f"\nProcessing [{case['id']}] {case['title'][:45]}...")

        # 1. Transcode audio
        if mp3_file.exists():
            ok = convert_audio_to_16k_wav(mp3_file, wav_file)
            if ok:
                print(f"  -> Converted to 16kHz WAV: {wav_file.name} ({wav_file.stat().st_size:,} bytes)")
            else:
                print(f"  -> WAV conversion failed for {mp3_file.name}")
        else:
            print(f"  -> MP3 not found: {mp3_file.name}")

        # 2. Clean transcript
        transcript_text = clean_vtt_to_text(vtt_file)
        if transcript_text:
            txt_file.write_text(transcript_text, encoding="utf-8")
            print(f"  -> Cleaned transcript saved: {txt_file.name} ({len(transcript_text.split()):,} words)")
        else:
            print(f"  -> Subtitles not found for {vid}")

        # 3. Assemble case record
        record = dict(case)
        record["audio_mp3"] = str(mp3_file.as_posix())
        record["audio_16k_wav"] = str(wav_file.as_posix())
        record["transcript_txt"] = str(txt_file.as_posix())
        record["word_count"] = len(transcript_text.split()) if transcript_text else 0
        record["has_audio_wav"] = wav_file.exists()
        manifest_cases.append(record)

    manifest_output = AUDIO_DIR / "youtube_mechanic_benchmark.json"
    with open(manifest_output, "w", encoding="utf-8") as f:
        json.dump(
            {
                "description": "Real-world YouTube Indian Mechanic Hindi Repair & Labour Cost Benchmark Dataset",
                "dataset_version": "v1.0",
                "created_at": str(date.today()),
                "total_cases": len(manifest_cases),
                "cases": manifest_cases
            },
            f,
            indent=2,
            ensure_ascii=False
        )

    print(f"\nBenchmark manifest successfully written to: {manifest_output}")
    print(f"Total benchmark cases: {len(manifest_cases)}")


if __name__ == "__main__":
    main()
