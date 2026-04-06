"""Full automated test suite — simulates real customer scenarios across all device types and risk classes."""

import csv
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from prompts.system_prompt import SYSTEM_PROMPT, SUMMARY_TABLE_INSTRUCTION

from anthropic import Anthropic

# --- Customer personas mapped to test cases ---

TEST_CASES = [
    # === PERSONA 1: Startup QE, Class IIa, EU — most common customer ===
    {
        "name": "P1-T1: Pulse Oximeter (startup QE, Class IIa, EU+US)",
        "persona": "Quality Engineer at 15-person startup, first medical device",
        "device_type": "Patient monitoring (Vital signs, Wearable)",
        "description": "Fingertip pulse oximeter with SpO2 and heart rate display. Battery-powered, Bluetooth connectivity to mobile app. LED emitters at 660nm and 940nm.",
        "intended_use": "Non-invasive monitoring of arterial oxygen saturation in adult patients. Home and clinical use.",
        "subsystems": ["Electrical", "RF/Wireless/EMC", "Software/Firmware/AI", "Battery/Portable", "Optical/Laser", "Patient contact surfaces"],
        "risk_class": "Class IIa", "market": ["EU (CE marking / MDR)", "US (FDA 510(k) / PMA)"], "num_risks": 5,
    },
    {
        "name": "P1-T2: Wearable ECG Patch (startup, AI algorithm)",
        "persona": "Startup founder doing regulatory work themselves",
        "device_type": "Patient monitoring (Vital signs, Wearable)",
        "description": "Continuous single-lead ECG patch worn on chest for 14 days. Adhesive, waterproof, BLE to smartphone. AI-based arrhythmia detection algorithm trained on 50,000 ECGs.",
        "intended_use": "Ambulatory cardiac monitoring for atrial fibrillation detection in adults. Prescribed by physicians.",
        "subsystems": ["Electrical", "RF/Wireless/EMC", "Software/Firmware/AI", "Battery/Portable", "Patient contact surfaces", "Cybersecurity/Data"],
        "risk_class": "Class IIa", "market": ["US (FDA 510(k) / PMA)"], "num_risks": 5,
    },
    # === PERSONA 2: Regulatory consultant, multiple device types ===
    {
        "name": "P2-T3: Infusion Pump (consultant, Class IIb, complex)",
        "persona": "Independent regulatory consultant, $300/hr, doing risk file for client",
        "device_type": "Therapeutic (Drug delivery, Stimulation, Ablation)",
        "description": "Portable volumetric infusion pump for IV drug delivery. Peristaltic mechanism, 0.1-999 mL/hr, touchscreen, WiFi for EHR integration, rechargeable Li-ion battery.",
        "intended_use": "Continuous IV infusion in hospital and home care. Operated by nurses and trained home patients.",
        "subsystems": ["Electrical", "Mechanical", "Software/Firmware/AI", "Fluid/Gas systems", "Battery/Portable", "Patient contact surfaces", "RF/Wireless/EMC", "Cybersecurity/Data", "Ergonomic/Human factors"],
        "risk_class": "Class IIb", "market": ["EU (CE marking / MDR)", "US (FDA 510(k) / PMA)"], "num_risks": 7,
    },
    {
        "name": "P2-T4: Surgical Robot (consultant, Class III, highest risk)",
        "persona": "Consultant handling Class III submission for surgical company",
        "device_type": "Surgical (Robotic, Endoscopic, Powered instruments)",
        "description": "Robotic-assisted surgical system with 4 articulated arms, 3D HD vision, master-slave console. Electrosurgical capability, instrument exchange mechanism, force feedback.",
        "intended_use": "Minimally invasive surgery: general, urological, gynecological. Operated by trained surgeons in hospital OR.",
        "subsystems": ["Electrical", "Mechanical", "Software/Firmware/AI", "Thermal", "Optical/Laser", "Ergonomic/Human factors"],
        "risk_class": "Class III", "market": ["EU (CE marking / MDR)", "US (FDA 510(k) / PMA)"], "num_risks": 7,
    },
    # === PERSONA 3: Mid-size company RA specialist ===
    {
        "name": "P3-T5: Blood Analyzer IVD (mid-size, lab equipment)",
        "persona": "RA Specialist at 80-person diagnostics company, IVD focus",
        "device_type": "In-vitro diagnostic (IVD)",
        "description": "Automated hematology analyzer for CBC. 120 samples/hour, impedance + optical detection, reagent cartridges, barcode tracking, LIS connectivity.",
        "intended_use": "Quantitative blood cell analysis in clinical laboratories. Operated by trained lab technicians.",
        "subsystems": ["Electrical", "Mechanical", "Software/Firmware/AI", "Fluid/Gas systems", "Optical/Laser", "Biological (infection risk)", "Chemical/Toxicological", "Cybersecurity/Data"],
        "risk_class": "Class IIa", "market": ["EU (CE marking / MDR)"], "num_risks": 7,
    },
    {
        "name": "P3-T6: Digital Thermometer (simple device, quick analysis)",
        "persona": "RA Specialist needs quick risk file for simple Class IIa device",
        "device_type": "Diagnostic (In-vitro, Blood analysis, Monitoring)",
        "description": "Digital infrared tympanic thermometer. Single-use probe covers, 2-second measurement, LCD display, fever alarm, battery powered.",
        "intended_use": "Ear temperature measurement for fever screening. Home use by general population including children.",
        "subsystems": ["Electrical", "Battery/Portable", "Patient contact surfaces", "Ergonomic/Human factors"],
        "risk_class": "Class IIa", "market": ["EU (CE marking / MDR)"], "num_risks": 5,
    },
    # === PERSONA 4: Edge cases and specialty devices ===
    {
        "name": "P4-T7: Implantable Pacemaker (Class III, highest stakes)",
        "persona": "Large company risk manager validating AI tool against manual analysis",
        "device_type": "Implantable (Pacemaker, Stent, Prosthetic)",
        "description": "Dual-chamber cardiac pacemaker with rate-responsive pacing. Titanium housing, silicone leads, lithium-iodine battery (8yr). MRI conditional. Wireless telemetry for remote monitoring.",
        "intended_use": "Treatment of bradycardia and heart block. Implanted by cardiologists, monitored remotely by cardiac nurses.",
        "subsystems": ["Electrical", "RF/Wireless/EMC", "Software/Firmware/AI", "Battery/Portable", "Patient contact surfaces", "Magnetic field", "Cybersecurity/Data", "Sterilization/Reprocessing", "Biological (infection risk)"],
        "risk_class": "Class III", "market": ["EU (CE marking / MDR)", "US (FDA 510(k) / PMA)"], "num_risks": 7,
    },
    {
        "name": "P4-T8: X-ray System (ionizing radiation)",
        "persona": "Startup entering imaging market, needs radiation hazard coverage",
        "device_type": "Imaging (MRI, CT, X-ray, Ultrasound)",
        "description": "Portable digital X-ray system for bedside imaging. Flat panel detector, battery-powered generator, wireless image transfer, AI-assisted positioning and exposure optimization.",
        "intended_use": "Diagnostic radiography in emergency departments and ICU. Operated by radiographers and trained nurses.",
        "subsystems": ["Electrical", "Radiation (ionizing)", "Software/Firmware/AI", "Battery/Portable", "RF/Wireless/EMC", "Mechanical", "Ergonomic/Human factors"],
        "risk_class": "Class IIb", "market": ["US (FDA 510(k) / PMA)"], "num_risks": 5,
    },
    {
        "name": "P4-T9: Home Dialysis Machine (fluid + patient contact + complex)",
        "persona": "Startup QE, complex home-use device with multiple hazard types",
        "device_type": "Therapeutic (Drug delivery, Stimulation, Ablation)",
        "description": "Home peritoneal dialysis cycler. Automated fluid exchange with 4 bag connections, touchscreen, cellular connectivity for remote monitoring, heated solution path.",
        "intended_use": "Automated peritoneal dialysis during sleep for end-stage renal disease patients. Home use by patients after training.",
        "subsystems": ["Electrical", "Fluid/Gas systems", "Thermal", "Software/Firmware/AI", "Patient contact surfaces", "Biological (infection risk)", "RF/Wireless/EMC", "Ergonomic/Human factors", "Cybersecurity/Data", "Chemical/Toxicological"],
        "risk_class": "Class IIb", "market": ["EU (CE marking / MDR)", "US (FDA 510(k) / PMA)"], "num_risks": 7,
    },
    {
        "name": "P4-T10: Dental Laser (optical + thermal + Class IIb)",
        "persona": "Small dental device company, first regulatory submission",
        "device_type": "Therapeutic (Drug delivery, Stimulation, Ablation)",
        "description": "Dental diode laser, 810nm, 0.5-10W, fiber optic delivery, foot pedal activation. For soft tissue surgery, teeth whitening, and pain therapy.",
        "intended_use": "Soft tissue oral surgery and teeth whitening in dental offices. Operated by licensed dentists.",
        "subsystems": ["Electrical", "Optical/Laser", "Thermal", "Mechanical", "Software/Firmware/AI", "Patient contact surfaces", "Ergonomic/Human factors"],
        "risk_class": "Class IIb", "market": ["EU (CE marking / MDR)", "US (FDA 510(k) / PMA)"], "num_risks": 5,
    },
]


def build_prompt(tc):
    return f"""Generate a comprehensive ISO 14971 risk analysis for this medical device:

**Device type:** {tc['device_type']}
**Description:** {tc['description']}
**Intended use:** {tc['intended_use']}
**Key subsystems:** {', '.join(tc['subsystems'])}
**Risk class:** {tc['risk_class']}
**Target market:** {', '.join(tc['market'])}

Generate exactly {tc['num_risks']} risks, starting with the highest-severity hazards.
Cover all relevant hazard types for the subsystems listed.
Be specific to THIS device — not generic medical device risks.

{SUMMARY_TABLE_INSTRUCTION}
"""


def check_quality(name, result, tc):
    """Run automated quality checks on the output."""
    checks = []
    text = result.lower()

    # 1: Correct risk count
    risk_count = len(re.findall(r'###?\s*risk\s*\[?\d+\]?', text, re.IGNORECASE))
    checks.append(("Risk count matches", risk_count == tc["num_risks"], f"expected {tc['num_risks']}, got {risk_count}"))

    # 2: P1/S1 scoring
    pre_scores = re.findall(r'p1\s*=\s*(\d)', text)
    checks.append(("Pre-control scores (P1)", len(pre_scores) >= tc["num_risks"], f"{len(pre_scores)} found"))

    # 3: P2/S2 scoring
    post_scores = re.findall(r'p2\s*=\s*(\d)', text)
    checks.append(("Post-control scores (P2)", len(post_scores) >= tc["num_risks"], f"{len(post_scores)} found"))

    # 4: Verification tables
    has_verification = "| test" in text or "| method" in text or "pass criterion" in text
    checks.append(("Verification tables present", has_verification, ""))

    # 5: Multi-standard references (not just IEC 60601)
    iec_refs = re.findall(r'iec\s+6[0-9]{3,4}', text)
    iso_refs = re.findall(r'iso\s+[0-9]{4,5}', text)
    unique_standards = len(set(iec_refs + iso_refs))
    checks.append(("Multi-standard references", unique_standards >= 3, f"{unique_standards} unique standards cited"))

    # 6: Standard diversity — not just IEC 60601
    has_62304 = "iec 62304" in text or "62304" in text
    has_10993 = "iso 10993" in text or "10993" in text
    has_62366 = "iec 62366" in text or "62366" in text
    has_62443 = "iec 62443" in text or "62443" in text
    sw_subsys = any("software" in s.lower() for s in tc["subsystems"])
    contact_subsys = any("contact" in s.lower() or "biological" in s.lower() for s in tc["subsystems"])
    if sw_subsys:
        checks.append(("IEC 62304 cited (software device)", has_62304, ""))
    if contact_subsys:
        checks.append(("ISO 10993 cited (patient contact)", has_10993, ""))

    # 7: Summary table
    has_summary = "risk summary" in text
    checks.append(("Summary table", has_summary, ""))

    # 8: Quantitative values
    quant = re.findall(r'\d+\.?\d*\s*(?:µa|ma|mv|v\b|kv|°c|mm|mw|w\b|db|hz|khz|mhz|kω|ω|ohm|ppm|mgy|msv|µsv)', text)
    checks.append(("Quantitative criteria (units)", len(quant) >= 5, f"{len(quant)} values with units"))

    # 9: Control hierarchy
    has_design = "safety by design" in text or "inherent safety" in text or "by design" in text
    has_protective = "protective" in text
    checks.append(("Control hierarchy present", has_design and has_protective, ""))

    # 10: No vague criteria
    vague = re.findall(r'(?:adequate|acceptable|appropriate|sufficient)\s+(?:testing|level|protection|measures)', text)
    checks.append(("No vague criteria", len(vague) == 0, f"{len(vague)} vague terms" if vague else "clean"))

    # 11: At least one A* risk (realistic scoring)
    has_astar = "a*" in text or "a\\*" in text or "benefit-risk" in text
    checks.append(("Realistic scoring (has A*)", has_astar, ""))

    # 12: Residual risk summary
    has_residual = "residual risk summary" in text
    checks.append(("Residual risk summary", has_residual, ""))

    # 13: Subsystem coverage — each checked subsystem should appear in at least one risk
    subsystem_keywords = {
        "Electrical": ["electrical", "leakage", "insulation", "grounding"],
        "RF/Wireless/EMC": ["emi", "emc", "wireless", "bluetooth", "rf", "ble"],
        "Software/Firmware/AI": ["software", "algorithm", "firmware", "frozen", "ai"],
        "Battery/Portable": ["battery", "thermal runaway", "charging", "lithium"],
        "Optical/Laser": ["optical", "laser", "led", "radiation", "light"],
        "Patient contact surfaces": ["biocompatibility", "skin", "contact", "irritation"],
        "Fluid/Gas systems": ["fluid", "flow", "occlusion", "air", "leak", "infusion"],
        "Mechanical": ["mechanical", "moving", "pinch", "crush", "drop"],
        "Thermal": ["thermal", "burn", "temperature", "overheat"],
        "Radiation (ionizing)": ["radiation", "dose", "x-ray", "scatter"],
        "Biological (infection risk)": ["infection", "contamination", "bioburden", "sterile"],
        "Chemical/Toxicological": ["chemical", "leachable", "extractable", "toxic"],
        "Cybersecurity/Data": ["cybersecurity", "unauthorized", "data breach", "encryption"],
        "Acoustic/Noise": ["acoustic", "noise", "sound"],
        "Sterilization/Reprocessing": ["sterilization", "sterile", "reprocessing"],
        "Ergonomic/Human factors": ["use error", "usability", "ergonomic", "misuse", "human factor"],
        "Magnetic field": ["magnetic", "projectile", "ferromagnetic"],
        "Environmental (disposal)": ["disposal", "recycling", "transport", "environmental"],
    }
    covered = 0
    total_subsystems = len(tc["subsystems"])
    uncovered = []
    for sub in tc["subsystems"]:
        sub_clean = sub.split("(")[0].strip()
        keywords = subsystem_keywords.get(sub, [sub_clean.lower()])
        if any(kw in text for kw in keywords):
            covered += 1
        else:
            uncovered.append(sub_clean)
    coverage_pct = covered / total_subsystems * 100 if total_subsystems else 100
    checks.append((
        f"Subsystem coverage ({covered}/{total_subsystems})",
        coverage_pct >= 70,
        f"missing: {', '.join(uncovered)}" if uncovered else "all covered"
    ))

    # 14: P2 scoring rules (P2 should not be lower than P1 without design/protective control)
    p1_vals = [int(x) for x in re.findall(r'p1\s*=\s*(\d)', text)]
    p2_vals = [int(x) for x in re.findall(r'p2\s*=\s*(\d)', text)]
    if p1_vals and p2_vals and len(p1_vals) == len(p2_vals):
        all_reduced = all(p2 < p1 for p1, p2 in zip(p1_vals, p2_vals))
        checks.append(("P2 < P1 (controls reduce risk)", all_reduced or len(p1_vals) < 2, ""))

    return checks


def test_csv_extraction(result, tc):
    """Test that CSV export would work on this output."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

    # Simulate CSV extraction
    risk_blocks = re.split(r'#{2,3}\s*Risk\s*\[?\d+\]?', result)
    extracted = len(risk_blocks) - 1
    has_p1 = len(re.findall(r'P1\s*=\s*\d', result)) > 0
    has_p2 = len(re.findall(r'P2\s*=\s*\d', result)) > 0

    ok = extracted >= tc["num_risks"] - 1 and has_p1 and has_p2
    return ok, f"extracted {extracted} risks, P1={has_p1}, P2={has_p2}"


def main():
    api_key = None
    secrets_path = os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        with open(secrets_path) as f:
            for line in f:
                if "ANTHROPIC_API_KEY" in line and "=" in line:
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: No API key found")
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)

    total_pass = 0
    total_checks = 0
    total_cost = 0
    failed_tests = []

    print(f"\n{'='*70}")
    print(f"  MedRisk AI — Full Test Suite ({len(TEST_CASES)} tests)")
    print(f"  Simulating real customer scenarios across all device types")
    print(f"{'='*70}")

    for i, tc in enumerate(TEST_CASES):
        print(f"\n{'─'*70}")
        print(f"  [{i+1}/{len(TEST_CASES)}] {tc['name']}")
        print(f"  Persona: {tc['persona']}")
        print(f"  Subsystems: {len(tc['subsystems'])} | Risks: {tc['num_risks']} | Class: {tc['risk_class']}")
        print(f"{'─'*70}")

        prompt = build_prompt(tc)
        print(f"  Generating...", end=" ", flush=True)
        t0 = time.time()

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        result = response.content[0].text
        elapsed = time.time() - t0
        cost = (response.usage.input_tokens * 3 + response.usage.output_tokens * 15) / 1_000_000
        total_cost += cost
        print(f"done ({elapsed:.0f}s, ${cost:.3f}, {response.usage.output_tokens:,} tokens)")

        # Save
        out_path = os.path.join(os.path.dirname(__file__), "results", f"full_test_{i+1}.md")
        with open(out_path, "w") as f:
            f.write(f"# {tc['name']}\n")
            f.write(f"**Persona:** {tc['persona']}\n")
            f.write(f"**Time:** {elapsed:.0f}s | **Cost:** ${cost:.3f} | **Tokens:** {response.usage.output_tokens:,}\n\n---\n\n")
            f.write(result)

        # Quality checks
        checks = check_quality(tc["name"], result, tc)

        # CSV extraction test
        csv_ok, csv_detail = test_csv_extraction(result, tc)
        checks.append(("CSV export parseable", csv_ok, csv_detail))

        passed = sum(1 for _, ok, _ in checks if ok)
        total = len(checks)
        total_pass += passed
        total_checks += total

        print(f"\n  Quality: {passed}/{total} checks passed")
        for label, ok, detail in checks:
            status = "PASS" if ok else "FAIL"
            extra = f" — {detail}" if detail else ""
            if not ok:
                print(f"    [\033[91m{status}\033[0m] {label}{extra}")
                failed_tests.append(f"{tc['name']}: {label}{extra}")
            else:
                print(f"    [\033[92m{status}\033[0m] {label}{extra}")

    # Final summary
    pass_rate = total_pass / total_checks * 100 if total_checks else 0
    print(f"\n{'='*70}")
    print(f"  FINAL RESULTS")
    print(f"{'='*70}")
    print(f"  Tests: {len(TEST_CASES)}")
    print(f"  Checks: {total_pass}/{total_checks} passed ({pass_rate:.1f}%)")
    print(f"  Total cost: ${total_cost:.3f}")
    print(f"  Avg time: {total_cost/len(TEST_CASES)*1000:.0f}ms per risk")

    if failed_tests:
        print(f"\n  FAILURES ({len(failed_tests)}):")
        for f in failed_tests:
            print(f"    - {f}")
    else:
        print(f"\n  ALL CHECKS PASSED")

    print(f"\n  Results saved in tests/results/full_test_*.md")
    print(f"{'='*70}\n")

    # Save summary JSON
    summary = {
        "total_tests": len(TEST_CASES),
        "total_checks": total_checks,
        "passed": total_pass,
        "failed": total_checks - total_pass,
        "pass_rate": f"{pass_rate:.1f}%",
        "total_cost": f"${total_cost:.3f}",
        "failures": failed_tests,
    }
    with open(os.path.join(os.path.dirname(__file__), "results", "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
