"""Automated test runner for MedRisk AI — runs test cases and checks output quality."""

import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from prompts.system_prompt import SYSTEM_PROMPT, SUMMARY_TABLE_INSTRUCTION

from anthropic import Anthropic

TEST_CASES = [
    {
        "name": "Test 1: Pulse Oximeter (simple)",
        "device_type": "Patient monitoring (Vital signs, Wearable)",
        "description": "Fingertip pulse oximeter with SpO2 and heart rate display. Battery-powered, Bluetooth connectivity to mobile app. LED emitters at 660nm and 940nm.",
        "intended_use": "Non-invasive monitoring of arterial oxygen saturation in adult patients. Home and clinical use.",
        "subsystems": ["Electrical", "RF/Wireless", "Software/Firmware", "Battery/Portable", "Optical/Laser", "Patient contact surfaces"],
        "risk_class": "Class IIa",
        "market": ["EU (CE marking / MDR)", "US (FDA 510(k) / PMA)"],
        "num_risks": 5,
    },
    {
        "name": "Test 2: Infusion Pump (complex)",
        "device_type": "Therapeutic (Drug delivery, Stimulation, Ablation)",
        "description": "Portable volumetric infusion pump for IV drug delivery. Peristaltic mechanism, 0.1-999 mL/hr flow rate, touchscreen, WiFi for EHR integration, rechargeable Li-ion battery.",
        "intended_use": "Continuous and intermittent IV infusion of medications in hospital and home care. Operated by trained nurses and home care patients.",
        "subsystems": ["Electrical", "Mechanical", "Software/Firmware", "Fluid/Gas systems", "Battery/Portable", "Patient contact surfaces", "RF/Wireless"],
        "risk_class": "Class IIb",
        "market": ["EU (CE marking / MDR)", "US (FDA 510(k) / PMA)"],
        "num_risks": 5,
    },
    {
        "name": "Test 3: Digital Thermometer (minimal)",
        "device_type": "Diagnostic (In-vitro, Blood analysis, Monitoring)",
        "description": "Digital clinical thermometer with infrared tympanic sensor. Single-use probe covers. 2-second measurement, LCD display, fever alarm.",
        "intended_use": "Temperature measurement in ear canal for fever screening. Home use by general population including children.",
        "subsystems": ["Electrical", "Battery/Portable", "Patient contact surfaces"],
        "risk_class": "Class IIa",
        "market": ["EU (CE marking / MDR)"],
        "num_risks": 5,
    },
    {
        "name": "Test 4: Wearable ECG (mid-complexity)",
        "device_type": "Patient monitoring (Vital signs, Wearable)",
        "description": "Continuous single-lead ECG patch worn on chest for 14 days. Adhesive, waterproof, Bluetooth Low Energy to smartphone app. AI-based arrhythmia detection.",
        "intended_use": "Ambulatory cardiac monitoring for atrial fibrillation detection in adult patients. Prescribed by physicians.",
        "subsystems": ["Electrical", "RF/Wireless", "Software/Firmware", "Battery/Portable", "Patient contact surfaces"],
        "risk_class": "Class IIa",
        "market": ["US (FDA 510(k) / PMA)"],
        "num_risks": 5,
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


def check_quality(name, result):
    """Run automated quality checks on the output."""
    checks = []
    text = result.lower()

    # Check 1: Has risk IDs
    risk_ids = re.findall(r'risk.?id.*?risk[_ ]?\d+', text, re.IGNORECASE)
    risk_count = len(re.findall(r'###?\s*risk\s+\[?\d+\]?', text, re.IGNORECASE))
    checks.append(("Risks generated", risk_count > 0, f"{risk_count} risks found"))

    # Check 2: Has P/S scoring
    pre_scores = re.findall(r'p1\s*=\s*\d', text)
    post_scores = re.findall(r'p2\s*=\s*\d', text)
    checks.append(("Pre-control scores (P1)", len(pre_scores) > 0, f"{len(pre_scores)} found"))
    checks.append(("Post-control scores (P2)", len(post_scores) > 0, f"{len(post_scores)} found"))

    # Check 3: Has verification tables
    has_verification = "| test" in text or "| method" in text or "pass criterion" in text
    checks.append(("Verification tables", has_verification, ""))

    # Check 4: Has IEC references
    iec_refs = re.findall(r'iec\s+6[0-9]{3}', text)
    iso_refs = re.findall(r'iso\s+[0-9]{4,5}', text)
    checks.append(("IEC/ISO references", len(iec_refs) + len(iso_refs) > 0, f"{len(iec_refs)} IEC + {len(iso_refs)} ISO"))

    # Check 5: Has summary table
    has_summary = "risk summary" in text
    checks.append(("Summary table", has_summary, ""))

    # Check 6: Has quantitative values (numbers with units)
    quant = re.findall(r'\d+\s*(?:µa|ma|mv|kv|°c|mm|mw|db|hz|khz|mhz|kω|ω|ohm)', text)
    checks.append(("Quantitative criteria", len(quant) > 2, f"{len(quant)} values with units"))

    # Check 7: Has control type labels
    has_design = "safety by design" in text or "inherent safety" in text
    has_protective = "protective" in text
    has_info = "information" in text or "labeling" in text or "training" in text
    checks.append(("Control hierarchy (design/protective/info)", has_design and has_protective, ""))

    # Check 8: No "adequate" or vague criteria
    vague = re.findall(r'(?:adequate|acceptable|appropriate|sufficient)\s+(?:testing|level|protection)', text)
    checks.append(("No vague criteria", len(vague) == 0, f"{len(vague)} vague terms found" if vague else "clean"))

    # Check 9: Has A* risk (not all acceptable)
    has_astar = "a*" in text or "a\\*" in text or "benefit-risk" in text
    checks.append(("At least one A* risk", has_astar, "realistic scoring" if has_astar else "may be too optimistic"))

    # Check 10: Has residual risk summary
    has_residual = "residual risk summary" in text
    checks.append(("Residual risk summary", has_residual, ""))

    return checks


def main():
    api_key = None
    # Try secrets.toml
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
        print("ERROR: No API key found. Set in .streamlit/secrets.toml or ANTHROPIC_API_KEY env var")
        sys.exit(1)

    client = Anthropic(api_key=api_key)
    os.makedirs(os.path.join(os.path.dirname(__file__), "results"), exist_ok=True)

    total_pass = 0
    total_checks = 0
    total_cost = 0

    for i, tc in enumerate(TEST_CASES):
        print(f"\n{'='*60}")
        print(f"  {tc['name']}")
        print(f"{'='*60}")

        prompt = build_prompt(tc)
        print(f"  Generating ({tc['num_risks']} risks)...", end=" ", flush=True)
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

        print(f"done ({elapsed:.0f}s, ${cost:.3f})")
        total_cost += cost

        # Save result
        out_path = os.path.join(os.path.dirname(__file__), "results", f"test_{i+1}.md")
        with open(out_path, "w") as f:
            f.write(f"# {tc['name']}\n\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"Time: {elapsed:.0f}s | Cost: ${cost:.3f}\n\n---\n\n")
            f.write(result)
        print(f"  Saved: {out_path}")

        # Quality checks
        checks = check_quality(tc["name"], result)
        passed = sum(1 for _, ok, _ in checks if ok)
        total = len(checks)
        total_pass += passed
        total_checks += total

        print(f"\n  Quality: {passed}/{total} checks passed")
        for label, ok, detail in checks:
            status = "PASS" if ok else "FAIL"
            extra = f" — {detail}" if detail else ""
            print(f"    [{status}] {label}{extra}")

    print(f"\n{'='*60}")
    print(f"  TOTAL: {total_pass}/{total_checks} checks passed across {len(TEST_CASES)} tests")
    print(f"  Total API cost: ${total_cost:.3f}")
    print(f"  Results saved in tests/results/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
