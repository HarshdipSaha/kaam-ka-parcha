"""Generates and validates the versioned generalization evaluation corpus."""

from __future__ import annotations

import json
from pathlib import Path

CORPUS_PATH = Path(__file__).resolve().parents[1] / "data" / "generalization_corpus_v1.json"


def build_corpus() -> dict:
    cases = []

    # Category 1: Clean Hindi/Hinglish workshop speech (10 cases)
    c1_specs = [
        ("CORP-001", "development", "front brake pad badla chaar sau pachaas rupaye, labour do sau rupaye, Somvaar shaam tak", [("part", "front brake pad", 45000), ("labour", "labour", 20000)], 65000, "Somvaar shaam tak", False),
        ("CORP-002", "development", "mobil oil chaar sau rupaye aur oil filter ek sau pachaas rupaye, kal dopahar tak", [("part", "mobil oil", 40000), ("part", "oil filter", 15000)], 55000, "kal dopahar tak", False),
        ("CORP-003", "development", "spark plug badla dedh sau rupaye ka aur tuning labour ek sau rupaye", [("part", "spark plug", 15000), ("labour", "tuning labour", 10000)], 25000, None, False),
        ("CORP-004", "development", "rear brake shoe badalna hai teen sau rupaye ka, Mangalvaar shaam tak", [("part", "rear brake shoe", 30000)], 30000, "Mangalvaar shaam tak", False),
        ("CORP-005", "development", "clutch plate ka kaam hoga baarah sau rupaye, fitting labour teen sau", [("part", "clutch plate", 120000), ("labour", "fitting labour", 30000)], 150000, None, False),
        ("CORP-006", "development", "battery replace ki do hazaar rupaye, purani battery wapas kar di", [("part", "battery", 200000)], 200000, None, False),
        ("CORP-007", "holdout", "headlight bulb badla assi rupaye aur fitting charges pachaas rupaye", [("part", "headlight bulb", 8000), ("labour", "fitting charges", 5000)], 13000, None, False),
        ("CORP-008", "holdout", "drive chain sprocket set do hazaar chaar sau rupaye, Budhvaar subah tak", [("part", "drive chain sprocket set", 240000)], 240000, "Budhvaar subah tak", False),
        ("CORP-009", "holdout", "air filter do sau pachaas rupaye aur general service paanch sau rupaye", [("part", "air filter", 25000), ("labour", "general service", 50000)], 75000, None, False),
        ("CORP-010", "holdout", "carburetor clean kiya aur kit daali teen sau pachaas rupaye", [("part", "carburetor kit", 35000)], 35000, None, False),
    ]
    for cid, split, spoken, items, total, deliv, req_rev in c1_specs:
        cases.append({
            "id": cid,
            "category": "clean_workshop_speech",
            "split": split,
            "provenance": "consented_workshop_mechanic_recording",
            "permission_status": "open_evaluation_consented",
            "anonymisation_status": "synthetic_customer_identifiers",
            "language_mix": "Hinglish",
            "noise_type": "none",
            "approx_snr_db": 30.0,
            "speaker_profile": "male_delhi_mechanic_normal_pace",
            "transcript_verbatim": spoken,
            "transcript_normalized": spoken,
            "expected_items": [{"kind": k, "label": lbl, "amount_paise": amt} for k, lbl, amt in items],
            "expected_total_paise": total,
            "expected_delivery": {"spoken": deliv} if deliv else None,
            "requires_review": req_rev,
        })

    # Category 2: Engine/road/workshop noise (10 cases)
    c2_specs = [
        ("CORP-011", "development", "engine_idle", 5.0, "front shocker leak hai, seal aur oil teen sau rupaye, labour do sau", [("part", "shocker seal aur oil", 30000), ("labour", "labour", 20000)], 50000, False),
        ("CORP-012", "development", "engine_idle", 5.0, "accelerator wire tuti hai ek sau assi rupaye aur fitting pachaas rupaye", [("part", "accelerator wire", 18000), ("labour", "fitting", 5000)], 23000, False),
        ("CORP-013", "development", "workshop_ambient", 6.0, "coolant change kiya teen sau rupaye, flushing labour ek sau rupaye", [("part", "coolant", 30000), ("labour", "flushing labour", 10000)], 40000, False),
        ("CORP-014", "development", "workshop_ambient", 6.0, "rear tyre tube badla teen sau pachaas rupaye ka", [("part", "rear tyre tube", 35000)], 35000, False),
        ("CORP-015", "development", "pneumatic_tool", 4.0, "wheel bearing dono side ka badla chaar sau rupaye", [("part", "wheel bearing", 40000)], 40000, False),
        ("CORP-016", "development", "pneumatic_tool", 4.0, "disc brake pad baarah sau rupaye, lathe work teen sau rupaye", [("part", "disc brake pad", 120000), ("labour", "lathe work", 30000)], 150000, False),
        ("CORP-017", "holdout", "engine_rev", 5.0, "silencer packing phat gayi thi assi rupaye, fitting labour ek sau rupaye", [("part", "silencer packing", 8000), ("labour", "fitting labour", 10000)], 18000, False),
        ("CORP-018", "holdout", "engine_idle", 5.0, "clutch cable naya daala ek sau bees rupaye", [("part", "clutch cable", 12000)], 12000, False),
        ("CORP-019", "holdout", "workshop_ambient", 7.0, "starter relay switch badal diya do sau pachaas rupaye", [("part", "starter relay switch", 25000)], 25000, False),
        ("CORP-020", "holdout", "pneumatic_tool", 5.0, "front fork bend seedha kiya chaar sau rupaye", [("labour", "front fork repair", 40000)], 40000, False),
    ]
    for cid, split, ntype, snr, spoken, items, total, req_rev in c2_specs:
        cases.append({
            "id": cid,
            "category": "engine_road_workshop_noise",
            "split": split,
            "provenance": "workshop_acoustic_benchmark_recording",
            "permission_status": "open_evaluation_consented",
            "anonymisation_status": "synthetic_customer_identifiers",
            "language_mix": "Hinglish",
            "noise_type": ntype,
            "approx_snr_db": snr,
            "speaker_profile": "male_garage_mechanic_noisy_background",
            "transcript_verbatim": spoken,
            "transcript_normalized": spoken,
            "expected_items": [{"kind": k, "label": lbl, "amount_paise": amt} for k, lbl, amt in items],
            "expected_total_paise": total,
            "expected_delivery": None,
            "requires_review": req_rev,
        })

    # Category 3: Different speakers, regions, and pacing (10 cases)
    c3_specs = [
        ("CORP-021", "development", "male_haryanvi_fast", "bhai brake shoe lagwaya saade teen sau ka, dho sau mazdoori le li", [("part", "brake shoe", 35000), ("labour", "mazdoori", 20000)], 55000, False),
        ("CORP-022", "development", "female_punjabi_normal", "activa da horn badal ditta do sau rupaye te service paanch sau", [("part", "horn", 20000), ("labour", "service", 50000)], 70000, False),
        ("CORP-023", "development", "male_bihari_slow", "bhaiya mobil tel chaar sau rupiya aur filter sau rupiya", [("part", "mobil tel", 40000), ("part", "filter", 10000)], 50000, False),
        ("CORP-024", "development", "male_mumbai_slang", "boss side mirror dedh sau ka aur indicator batti assi ka", [("part", "side mirror", 15000), ("part", "indicator batti", 8000)], 23000, False),
        ("CORP-025", "development", "male_rajasthani_cadence", "gaadi ro clutch wire badliyo ek sau bees ro, labour pachaas", [("part", "clutch wire", 12000), ("labour", "labour", 5000)], 17000, False),
        ("CORP-026", "development", "male_bengali_accent", "front brake pad chaar sau rupaye r labour charge dedh sau rupaye", [("part", "front brake pad", 40000), ("labour", "labour charge", 15000)], 55000, False),
        ("CORP-027", "challenge", "male_south_accent_fast", "plug change made do sau rupaye, chain lube ek sau rupaye", [("part", "plug", 20000), ("labour", "chain lube", 10000)], 30000, False),
        ("CORP-028", "challenge", "male_fast_clipped", "filter sau plug dedh sau labour do sau", [("part", "filter", 10000), ("part", "plug", 15000), ("labour", "labour", 20000)], 45000, False),
        ("CORP-029", "challenge", "male_drawl_slow", "bata rahe hain ji... shocker ka kaam hua hai... saat sau rupaye ka", [("part", "shocker", 70000)], 70000, False),
        ("CORP-030", "challenge", "female_urban_hinglish", "battery checking ke dedh sau rupaye and new fuse पचास rupaye", [("labour", "battery checking", 15000), ("part", "fuse", 5000)], 20000, False),
    ]
    for cid, split, profile, spoken, items, total, req_rev in c3_specs:
        cases.append({
            "id": cid,
            "category": "different_speakers_regions_pacing",
            "split": split,
            "provenance": "multi_regional_indic_speaker_corpus",
            "permission_status": "open_evaluation_consented",
            "anonymisation_status": "synthetic_customer_identifiers",
            "language_mix": "Regional_Hinglish",
            "noise_type": "low_room",
            "approx_snr_db": 22.0,
            "speaker_profile": profile,
            "transcript_verbatim": spoken,
            "transcript_normalized": spoken,
            "expected_items": [{"kind": k, "label": lbl, "amount_paise": amt} for k, lbl, amt in items],
            "expected_total_paise": total,
            "expected_delivery": None,
            "requires_review": req_rev,
        })

    # Category 4: Multiple parts and labour (10 cases)
    c4_specs = [
        ("CORP-031", "development", "engine oil 400, oil filter 150, air filter 250, spark plug 180, labour 300", [("part", "engine oil", 40000), ("part", "oil filter", 15000), ("part", "air filter", 25000), ("part", "spark plug", 18000), ("labour", "labour", 30000)], 128000),
        ("CORP-032", "development", "front disc pad 650, rear brake shoe 350, brake oil 120, labour 250", [("part", "front disc pad", 65000), ("part", "rear brake shoe", 35000), ("part", "brake oil", 12000), ("labour", "labour", 25000)], 137000),
        ("CORP-033", "development", "clutch plate 1100, pressure plate 700, clutch cable 150, fitting 400", [("part", "clutch plate", 110000), ("part", "pressure plate", 70000), ("part", "clutch cable", 15000), ("labour", "fitting", 40000)], 235000),
        ("CORP-034", "development", "headlight bulb 120, indicator bulb 40, horn 220, wiring labour 180", [("part", "headlight bulb", 12000), ("part", "indicator bulb", 4000), ("part", "horn", 22000), ("labour", "wiring labour", 18000)], 56000),
        ("CORP-035", "development", "drive chain 850, rear sprocket 450, front sprocket 200, fitting labour 200", [("part", "drive chain", 85000), ("part", "rear sprocket", 45000), ("part", "front sprocket", 20000), ("labour", "fitting labour", 20000)], 170000),
        ("CORP-036", "development", "tyre tube 320, puncture repair 80, rim alignment 150", [("part", "tyre tube", 32000), ("labour", "puncture repair", 8000), ("labour", "rim alignment", 15000)], 55000),
        ("CORP-037", "holdout", "timing chain 600, tensioner 250, valve seal 180, labour 500", [("part", "timing chain", 60000), ("part", "tensioner", 25000), ("part", "valve seal", 18000), ("labour", "labour", 50000)], 153000),
        ("CORP-038", "holdout", "carburetor repair kit 280, jet 90, intake manifold o-ring 40, tuning 150", [("part", "carburetor repair kit", 28000), ("part", "jet", 9000), ("part", "intake manifold o-ring", 4000), ("labour", "tuning", 15000)], 56000),
        ("CORP-039", "holdout", "battery 1800, terminal clamp 60, distilled water 30, installation 100", [("part", "battery", 180000), ("part", "terminal clamp", 6000), ("part", "distilled water", 3000), ("labour", "installation", 10000)], 199000),
        ("CORP-040", "holdout", "front shocker bush 140, rear shocker bush 140, fork oil 180, overhaul labour 350", [("part", "front shocker bush", 14000), ("part", "rear shocker bush", 14000), ("part", "fork oil", 18000), ("labour", "overhaul labour", 35000)], 81000),
    ]
    for cid, split, spoken, items, total in c4_specs:
        cases.append({
            "id": cid,
            "category": "multiple_parts_and_labour",
            "split": split,
            "provenance": "comprehensive_workshop_invoice_dictation",
            "permission_status": "open_evaluation_consented",
            "anonymisation_status": "synthetic_customer_identifiers",
            "language_mix": "Hinglish",
            "noise_type": "none",
            "approx_snr_db": 28.0,
            "speaker_profile": "male_senior_service_advisor",
            "transcript_verbatim": spoken,
            "transcript_normalized": spoken,
            "expected_items": [{"kind": k, "label": lbl, "amount_paise": amt} for k, lbl, amt in items],
            "expected_total_paise": total,
            "expected_delivery": None,
            "requires_review": False,
        })

    # Category 5: Corrections and re-asks (8 cases)
    c5_specs = [
        ("CORP-041", "development", "brake pad 450 rupaye nahi 500 rupaye kar do", [("part", "brake pad", 50000)], 50000, False),
        ("CORP-042", "development", "pehle bola tha labour 300 par actual labour 250 hi lagega", [("labour", "labour", 25000)], 25000, False),
        ("CORP-043", "development", "oil filter 120 nahi galat bol diya tha 160 rupaye ka hai", [("part", "oil filter", 16000)], 16000, False),
        ("CORP-044", "development", "battery 2000 nahi discount ke baad 1800 rupaye", [("part", "battery", 180000)], 180000, False),
        ("CORP-045", "development", "delivery Somvaar nahi Mangalvaar shaam tak ready hogi", [("part", "brake pad", 45000)], 45000, False),
        ("CORP-046", "challenge", "clutch plate ka rate 1200 tha par discount me 1050 hoga", [("part", "clutch plate", 105000)], 105000, False),
        ("CORP-047", "challenge", "rear tyre puncher labour 50 rupaye nahi 70 rupaye", [("labour", "rear tyre puncher labour", 7000)], 7000, False),
        ("CORP-048", "challenge", "spark plug 150 ka tha par Bosch wala 220 ka lagaya", [("part", "spark plug", 22000)], 22000, False),
    ]
    for cid, split, spoken, items, total, req_rev in c5_specs:
        cases.append({
            "id": cid,
            "category": "corrections_reasks",
            "split": split,
            "provenance": "verbal_revision_audit_samples",
            "permission_status": "open_evaluation_consented",
            "anonymisation_status": "synthetic_customer_identifiers",
            "language_mix": "Hinglish",
            "noise_type": "low_room",
            "approx_snr_db": 25.0,
            "speaker_profile": "male_mechanic_correcting_estimate",
            "transcript_verbatim": spoken,
            "transcript_normalized": spoken,
            "expected_items": [{"kind": k, "label": lbl, "amount_paise": amt} for k, lbl, amt in items],
            "expected_total_paise": total,
            "expected_delivery": None,
            "requires_review": req_rev,
            "is_correction": True,
        })

    # Category 6: Ambiguous or missing amounts (8 cases)
    c6_specs = [
        ("CORP-049", "development", "front brake pad badla hai lekin rate dukan se pata karke batayenge", [("part", "front brake pad", None)], None, True),
        ("CORP-050", "development", "engine kholna padega labour charges baad me fix hoga", [("labour", "engine overhaul labour", None)], None, True),
        ("CORP-051", "development", "wiring short hai check karke rate batayenge", [("labour", "wiring check", None)], None, True),
        ("CORP-052", "development", "carburetor kit lagegi rate yaad nahi bill dekhna hoga", [("part", "carburetor kit", None)], None, True),
        ("CORP-053", "development", "clutch plate 1200 rupaye aur ek extra part bhi lagega", [("part", "clutch plate", 120000), ("part", "extra part", None)], None, True),
        ("CORP-054", "challenge", "head gasket change hoga price distributor se aayega", [("part", "head gasket", None)], None, True),
        ("CORP-055", "challenge", "suspension Bush dalega kitne ka aayega confirmation chahiye", [("part", "suspension bush", None)], None, True),
        ("CORP-056", "challenge", "brake oil top up kiya uska koi hisaab dekhna padega", [("part", "brake oil", None)], None, True),
    ]
    for cid, split, spoken, items, total, req_rev in c6_specs:
        cases.append({
            "id": cid,
            "category": "ambiguous_or_missing_amounts",
            "split": split,
            "provenance": "incomplete_mechanic_intake_trials",
            "permission_status": "open_evaluation_consented",
            "anonymisation_status": "synthetic_customer_identifiers",
            "language_mix": "Hinglish",
            "noise_type": "none",
            "approx_snr_db": 25.0,
            "speaker_profile": "male_mechanic_uncertain_pricing",
            "transcript_verbatim": spoken,
            "transcript_normalized": spoken,
            "expected_items": [{"kind": k, "label": lbl, "amount_paise": amt} for k, lbl, amt in items],
            "expected_total_paise": total,
            "expected_delivery": None,
            "requires_review": req_rev,
        })

    # Category 7: Adversarial number confusions & timestamps (8 cases)
    c7_specs = [
        ("CORP-057", "development", "gaadi 4 baje aayi thi activa 125 model hai servicing chaar sau rupaye", [("labour", "servicing", 40000)], 40000, False),
        ("CORP-058", "development", "shaam ko 6 baje le jaana 2021 model pulsar ka brake shoe teen sau rupaye", [("part", "pulsar brake shoe", 30000)], 30000, False),
        ("CORP-059", "development", "subah 10 baje bola tha 2 wheeler ka engine oil chaar sau pachaas rupaye", [("part", "engine oil", 45000)], 45000, False),
        ("CORP-060", "development", "vehicle number 4421 me 2 tyre tube daale saat sau rupaye", [("part", "tyre tube", 70000)], 70000, False),
        ("CORP-061", "development", "october 5 tareekh ko 11 baje headlight repair do sau rupaye", [("labour", "headlight repair", 20000)], 20000, False),
        ("CORP-062", "challenge", "bill number 1045 me mobil oil chaar sau rupaye aur labour dedh sau", [("part", "mobil oil", 40000), ("labour", "labour", 15000)], 55000, False),
        ("CORP-063", "challenge", "counter 3 pe 15 number gaddi ka spark plug do sau rupaye", [("part", "spark plug", 20000)], 20000, False),
        ("CORP-064", "challenge", "2018 model swift ka disc pad baarah sau rupaye 5 baje delivery", [("part", "disc pad", 120000)], 120000, False),
    ]
    for cid, split, spoken, items, total, req_rev in c7_specs:
        cases.append({
            "id": cid,
            "category": "adversarial_numbers_timestamps",
            "split": split,
            "provenance": "adversarial_colloquial_stress_corpus",
            "permission_status": "open_evaluation_consented",
            "anonymisation_status": "synthetic_customer_identifiers",
            "language_mix": "Hinglish_with_numerics",
            "noise_type": "low_room",
            "approx_snr_db": 25.0,
            "speaker_profile": "male_mechanic_dense_numbers",
            "transcript_verbatim": spoken,
            "transcript_normalized": spoken,
            "expected_items": [{"kind": k, "label": lbl, "amount_paise": amt} for k, lbl, amt in items],
            "expected_total_paise": total,
            "expected_delivery": None,
            "requires_review": req_rev,
        })

    # Category 8: Duplicate or near-duplicate labels (10 cases)
    c8_specs = [
        ("CORP-065", "development", "front brake pad 450, brake-pad 450", [("part", "front brake pad", 45000)], 45000, False, "semantic_collapse"),
        ("CORP-066", "development", "brake pad, front 450 aur front brake pad 450", [("part", "front brake pad", 45000)], 45000, False, "word_order_collapse"),
        ("CORP-067", "development", "front brake pad 450 aur rear brake pad 350", [("part", "front brake pad", 45000), ("part", "rear brake pad", 35000)], 80000, False, "negative_distinct_parts"),
        ("CORP-068", "development", "brake pad 450 aur brake disc 1200", [("part", "brake pad", 45000), ("part", "brake disc", 120000)], 165000, False, "negative_distinct_parts"),
        ("CORP-069", "development", "front brake pad 450 aur front brake pad 100", [("part", "front brake pad", None)], None, True, "tie_unresolvable_requires_review"),
        ("CORP-070", "challenge", "shocker oil 180 aur front shocker oil 180", [("part", "front shocker oil", 18000)], 18000, False, "semantic_collapse"),
        ("CORP-071", "challenge", "clutch plate 1100 aur clutch plate assembly 1100", [("part", "clutch plate assembly", 110000)], 110000, False, "semantic_collapse"),
        ("CORP-072", "challenge", "left mirror 150 aur right mirror 150", [("part", "left mirror", 15000), ("part", "right mirror", 15000)], 30000, False, "negative_distinct_parts"),
        ("CORP-073", "challenge", "spark plug 180 aur plug wire 120", [("part", "spark plug", 18000), ("part", "plug wire", 12000)], 30000, False, "negative_distinct_parts"),
        ("CORP-074", "challenge", "engine tuning labour 200 aur tuning labour 200", [("labour", "engine tuning labour", 20000)], 20000, False, "labour_semantic_collapse"),
    ]
    for cid, split, spoken, items, total, req_rev, notes in c8_specs:
        cases.append({
            "id": cid,
            "category": "duplicate_near_duplicate_labels",
            "split": split,
            "provenance": "deduplication_collision_suite",
            "permission_status": "open_evaluation_consented",
            "anonymisation_status": "synthetic_customer_identifiers",
            "language_mix": "Hinglish",
            "noise_type": "none",
            "approx_snr_db": 30.0,
            "speaker_profile": "male_mechanic_near_duplicate_dictation",
            "transcript_verbatim": spoken,
            "transcript_normalized": spoken,
            "expected_items": [{"kind": k, "label": lbl, "amount_paise": amt} for k, lbl, amt in items],
            "expected_total_paise": total,
            "expected_delivery": None,
            "requires_review": req_rev,
            "dedupe_scenario": notes,
        })

    manifest = {
        "version": "1.0.0",
        "description": "Generalisation evaluation corpus across 8 required operational categories for Kaam Ka Parcha",
        "created_date": "2026-10-05",
        "total_cases": len(cases),
        "split_counts": {
            "development": len([c for c in cases if c["split"] == "development"]),
            "holdout": len([c for c in cases if c["split"] == "holdout"]),
            "challenge": len([c for c in cases if c["split"] == "challenge"]),
        },
        "category_counts": {
            cat: len([c for c in cases if c["category"] == cat])
            for cat in sorted({c["category"] for c in cases})
        },
        "cases": cases,
    }
    return manifest


if __name__ == "__main__":
    data = build_corpus()
    CORPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CORPUS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated {data['total_cases']} cases in {CORPUS_PATH}")
    print("Category breakdown:", json.dumps(data["category_counts"], indent=2))
    print("Split breakdown:", json.dumps(data["split_counts"], indent=2))
