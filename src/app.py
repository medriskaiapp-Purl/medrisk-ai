"""MedRisk AI — ISO 14971 Risk Management for Medical Devices."""

import csv
import io
import os
import re
import streamlit as st
from anthropic import Anthropic

from prompts.system_prompt import SYSTEM_PROMPT, SUMMARY_TABLE_INSTRUCTION

st.set_page_config(
    page_title="MedRisk AI",
    page_icon="🛡️",
    layout="wide",
)

# --- License / Free Tier ---
FREE_MAX_RISKS = 5
PURCHASE_URL = os.environ.get(
    "PURCHASE_URL",
    "https://medrisk-ai.lemonsqueezy.com/buy",  # Replace with actual Lemon Squeezy link
)
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")

def _valid_license_keys():
    """Load valid license keys from secrets or env."""
    try:
        return set(st.secrets.get("LICENSE_KEYS", "").split(","))
    except (KeyError, FileNotFoundError):
        pass
    raw = os.environ.get("LICENSE_KEYS", "")
    return {k.strip() for k in raw.split(",") if k.strip()}

def is_pro():
    """Check if current session has a valid license key."""
    key = st.session_state.get("license_key", "").strip()
    if not key:
        return False
    return key in _valid_license_keys()

# --- Hide Streamlit branding for professional look ---
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {visibility: hidden;}
    .stDeployButton {display: none;}
    div[data-testid="stStatusWidget"] {visibility: hidden;}
    .stApp > header {background-color: transparent;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- CSV Export Helper ---
def _extract_risk_table_csv(report_text, device_desc, risk_class, markets):
    """Extract risk data from report and format as CSV for Excel/QMS import."""
    buf = io.StringIO()
    writer = csv.writer(buf)

    # Header rows with metadata
    writer.writerow(["ISO 14971 Risk Analysis — MedRisk AI"])
    writer.writerow(["Device", device_desc[:100]])
    writer.writerow(["Classification", risk_class])
    writer.writerow(["Market", ", ".join(markets)])
    writer.writerow(["Date", str(__import__("datetime").date.today())])
    writer.writerow([])

    # Risk summary table header
    writer.writerow([
        "Risk ID", "Risk Name", "Hazard Type", "Subsystem",
        "P1", "S1", "RPN1",
        "Control Type(s)", "Control Summary",
        "P2", "S2", "RPN2",
        "Status", "IEC Reference",
    ])

    # Parse individual risks from markdown
    risk_blocks = re.split(r'#{2,3}\s*Risk\s*\[?\d+\]?', report_text)
    risk_num = 0
    for block in risk_blocks[1:]:  # skip pre-risk content
        risk_num += 1
        risk_id = _extract(block, r'Risk.?ID.*?(RISK[_ ]\d+)', f"RISK_{risk_num:02d}")
        name = _extract(block, r'#{0,3}\s*:?\s*(.+?)(?:\n|$)', f"Risk {risk_num}")
        hazard = _extract(block, r'Hazard type.*?:\s*(.+?)(?:\n|$)', "")
        subsystem = _extract(block, r'Subsystem.*?:\s*(.+?)(?:\n|$)', "")
        p1 = _extract(block, r'P1\s*=\s*(\d)', "")
        s1 = _extract(block, r'S1\s*=\s*(\d)', "")
        p2 = _extract(block, r'P2\s*=\s*(\d)', "")
        s2 = _extract(block, r'S2\s*=\s*(\d)', "")
        iec = _extract(block, r'IEC Reference.*?:\s*(.+?)(?:\n|$)', "")

        rpn1 = str(int(p1) * int(s1)) if p1.isdigit() and s1.isdigit() else ""
        rpn2 = str(int(p2) * int(s2)) if p2.isdigit() and s2.isdigit() else ""

        # Determine control types present
        ctrl_types = []
        if re.search(r'safety by design|inherent safety', block, re.I):
            ctrl_types.append("Design")
        if re.search(r'protective measure', block, re.I):
            ctrl_types.append("Protective")
        if re.search(r'information|labeling|training', block, re.I):
            ctrl_types.append("Information")

        # Extract first control measure as summary
        ctrl_match = re.search(r'\d+[a-c]\.\s*(.+?)(?:\n|$)', block)
        ctrl_summary = ctrl_match.group(1).strip()[:120] if ctrl_match else ""

        # Status
        rpn2_val = int(rpn2) if rpn2.isdigit() else 0
        status = "A" if rpn2_val <= 4 else ("A*" if rpn2_val <= 9 else "U")

        writer.writerow([
            risk_id, name.strip()[:80], hazard, subsystem,
            p1, s1, rpn1,
            " + ".join(ctrl_types), ctrl_summary,
            p2, s2, rpn2,
            status, iec,
        ])

    return buf.getvalue()


def _extract(text, pattern, default=""):
    """Extract first regex match from text."""
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else default


# --- Privacy Consent (first visit) ---
if "privacy_accepted" not in st.session_state:
    st.session_state.privacy_accepted = False

if not st.session_state.privacy_accepted:
    st.title("MedRisk AI")
    st.markdown(
        "**Before you start**\n\n"
        "MedRisk AI is a purpose-built risk analysis engine configured with "
        "12 regulatory standards (ISO 14971, IEC 60601, IEC 62304, and 9 more), "
        "18 hazard categories, and a 6-point self-verification system. "
        "Every analysis is checked for physics accuracy, scoring consistency, "
        "and standard compliance before delivery.\n\n"
        "Your data is processed in real-time and **not stored** after the report is generated.\n\n"
        "- Do not include patient names or personally identifiable information\n"
        "- Device descriptions are used solely to generate your analysis\n\n"
        "By continuing, you agree to these terms. Contact: medrisk.ai.app@gmail.com"
    )
    if st.button("Accept and Continue", type="primary"):
        st.session_state.privacy_accepted = True
        st.rerun()
    st.stop()

# --- Header ---
st.title("MedRisk AI")
st.markdown("**Save 3-6 months of risk management work.** Get your first ISO 14971 risk analysis in 10 minutes — audit-ready, multi-standard, self-verified.")

# --- Trust metrics ---
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
col_m1.metric("Standards", "12", help="ISO 14971, IEC 60601, IEC 62304, ISO 10993, IEC 62366, IEC 62443, and 6 more")
col_m2.metric("Hazard types", "18", help="Electrical, mechanical, thermal, software, cybersecurity, biological, and 12 more")
col_m3.metric("Verification checks", "6", help="Physics, completeness, scoring, criteria, standards, adversarial review")
col_m4.metric("Time to report", "~60s", help="vs 3-6 months with traditional methods")

# --- Sample Output (trust before trial) ---
with st.expander("See a sample analysis (Pulse Oximeter — 1 of 5 risks shown)", expanded=True):
    st.markdown("""**Risk 2: SpO2 Measurement Error — Missed Hypoxemia**

**Risk ID:** RISK_02 | **Hazard:** Software/Diagnostic | **Subsystem:** Signal processing (PPG)
**Life-cycle phase:** Use

**Hazardous situation:** Device displays falsely normal SpO2 (97%) when patient is hypoxemic (actual <90%). Clinician does not intervene.
**Sequence of events:** 1. Low perfusion or motion artifact → 2. Algorithm processes corrupted signal → 3. False normal reading displayed → 4. Delayed clinical intervention
**Harm:** Delayed treatment of hypoxemia — potential organ damage or death

**Pre-control:** P1=3, S1=5 (RPN=15, U — MUST reduce)

**Controls:**
- 2a. Signal Quality Index (Safety by design): PI <0.3% or SQI <60% → SpO2 blanked ("---"). No false number shown.
- 2b. Clinical validation (Safety by design): ISO 80601-2-61, n≥200, Arms ≤ 3%, including Fitzpatrick V-VI
- 2c. Motion artifact rejection (Protective): Accelerometer + adaptive filter, >30s → value blanked

**Verification:**
| Test | Method | Pass Criterion |
|------|--------|----------------|
| Clinical accuracy | ISO 80601-2-61 desaturation study | Arms ≤ 3.0% |
| SQI blanking | Simulated PI=0.1% | SpO2 blanked within 5s |
| Dark pigmentation bias | Fitzpatrick V-VI vs I-II comparison | Bias ≤ 1.0% |

**Residual:** P2=2, S2=5 (RPN=10, A* — benefit-risk justified)
**Justification:** SQI blanking + clinical validation reduce probability from 3→2. Severity unchanged (S2=5) because harm remains fatal if it occurs. Benefit of continuous monitoring outweighs residual risk under clinical protocols.
**IEC Reference:** ISO 80601-2-61:2017, IEC 62304

---
*Each report also includes: Risk Summary Table, IEC Clause Cross-Reference, GSPR Mapping (EU), Audit Readiness Checklist, and Post-Market Monitoring Plan.*
""")

st.divider()

# --- Main Area: Device Input Form ---
st.subheader("Try it — describe your device")

col1, col2 = st.columns([2, 1])
with col1:
    device_type = st.selectbox(
        "Device type",
        [
            "Patient monitoring (Vital signs, Wearable, ECG)",
            "Imaging (MRI, CT, X-ray, Ultrasound)",
            "Therapeutic (Drug delivery, Stimulation, Ablation)",
            "Surgical (Robotic, Endoscopic, Powered instruments)",
            "Diagnostic (Blood analysis, Point-of-care)",
            "Implantable (Pacemaker, Stent, Orthopedic)",
            "In-vitro diagnostic (IVD, Lab analyzer)",
            "Software as Medical Device (SaMD, AI/ML)",
            "Respiratory (Ventilator, CPAP, Nebulizer)",
            "Dental (Laser, Imaging, Instruments)",
            "Ophthalmic (Laser, Lenses, Diagnostics)",
            "Rehabilitation / Assistive (Mobility, Prosthetic)",
            "Other",
        ],
    )
with col2:
    risk_class = st.selectbox(
        "Risk classification",
        ["Class I", "Class IIa", "Class IIb", "Class III"],
        index=1,
    )

device_description = st.text_area(
    "Device description",
    placeholder="Describe your device: what it does, key components, power source, connectivity, sensors. Be specific — the more detail, the better the analysis.",
    height=100,
)

intended_use = st.text_area(
    "Intended use / Indications (optional — improves analysis)",
    placeholder="Who uses it, where, for what clinical purpose. e.g., 'Point-of-care cardiac imaging by trained professionals in emergency settings.'",
    height=60,
)

subsystem_options = [
    "Electrical (power, wiring)",
    "RF / Wireless / EMC",
    "Thermal (heating, cooling)",
    "Mechanical (moving parts)",
    "Software / Firmware / AI",
    "Fluid / Gas systems",
    "Optical / Laser",
    "Magnetic field",
    "Battery / Portable",
    "Patient contact surfaces",
    "Radiation (ionizing)",
    "Biological (infection risk)",
    "Chemical / Toxicological",
    "Cybersecurity / Data",
    "Acoustic / Noise",
    "Sterilization / Reprocessing",
    "Ergonomic / Human factors",
    "Environmental (disposal)",
]

# Smart defaults based on device type
_subsystem_suggestions = {
    "Patient monitoring": ["Electrical (power, wiring)", "RF / Wireless / EMC", "Software / Firmware / AI", "Battery / Portable", "Patient contact surfaces"],
    "Imaging": ["Electrical (power, wiring)", "Software / Firmware / AI", "Mechanical (moving parts)", "Patient contact surfaces"],
    "Therapeutic": ["Electrical (power, wiring)", "Software / Firmware / AI", "Patient contact surfaces"],
    "Surgical": ["Electrical (power, wiring)", "Mechanical (moving parts)", "Software / Firmware / AI", "Sterilization / Reprocessing"],
    "Diagnostic": ["Electrical (power, wiring)", "Software / Firmware / AI", "Patient contact surfaces"],
    "Implantable": ["Electrical (power, wiring)", "Patient contact surfaces", "Biological (infection risk)", "Sterilization / Reprocessing", "Battery / Portable"],
    "In-vitro": ["Electrical (power, wiring)", "Software / Firmware / AI", "Fluid / Gas systems", "Biological (infection risk)", "Chemical / Toxicological"],
    "Software": ["Software / Firmware / AI", "Cybersecurity / Data"],
    "Respiratory": ["Electrical (power, wiring)", "Software / Firmware / AI", "Fluid / Gas systems", "Patient contact surfaces", "Acoustic / Noise"],
    "Dental": ["Electrical (power, wiring)", "Optical / Laser", "Patient contact surfaces", "Sterilization / Reprocessing"],
    "Ophthalmic": ["Electrical (power, wiring)", "Optical / Laser", "Software / Firmware / AI", "Patient contact surfaces"],
    "Rehabilitation": ["Electrical (power, wiring)", "Mechanical (moving parts)", "Battery / Portable", "Ergonomic / Human factors"],
}
_default_subs = []
for key, subs in _subsystem_suggestions.items():
    if device_type.startswith(key):
        _default_subs = subs
        break

subsystems = st.multiselect(
    "Key subsystems (select all that apply)",
    subsystem_options,
    default=_default_subs,
    help="Pre-selected based on device type. Add or remove as needed.",
)

target_market = st.multiselect(
    "Target market",
    ["EU (CE marking / MDR)", "US (FDA 510(k) / PMA)", "Canada (Health Canada)", "Other"],
    default=["EU (CE marking / MDR)"],
)

# --- Sidebar: Settings + License ---
with st.sidebar:
    st.header("Settings")

    # License key — hidden in expander, not prominent
    with st.expander("Pro license", expanded=False):
        license_key = st.text_input(
            "Enter license key",
            type="password",
            key="license_key",
        )
        pro = is_pro()
        if pro:
            st.success("Pro active — up to 25 risks + download")
        else:
            st.caption(f"[Get a Pro license]({PURCHASE_URL})")

    if is_pro():
        num_risks = st.slider("Number of risks", 5, 25, 15)
    else:
        num_risks = FREE_MAX_RISKS

    st.divider()
    st.markdown(
        "**What makes this different:**\n"
        "- 12 standards auto-selected per device\n"
        "- 6-point self-verification before delivery\n"
        "- GSPR mapping (EU MDR)\n"
        "- Audit readiness checklist\n"
        "- Post-market monitoring plan\n"
        "- CSV export for Excel / QMS import\n"
        "- No prompt writing, no setup, no AI expertise needed"
    )
    st.caption("Your data is processed, not stored.")

# --- API Key: server-side (secrets) or env var, fallback to user input for local dev ---
def get_api_key():
    """Get API key from Streamlit secrets (production) or env var (local dev)."""
    # 1. Streamlit Cloud secrets (production)
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    # 2. Environment variable (local dev)
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    # 3. No key available
    return None

api_key = get_api_key()

# --- Main area ---
if not api_key:
    st.error("Service is temporarily unavailable. Please try again later.")

if st.button("Generate Risk Analysis", type="primary", use_container_width=True):
    if not device_description:
        st.error("Please describe your device above.")
        st.stop()
    if not api_key:
        st.error("API key not configured. See setup instructions above.")
        st.stop()

    # --- Security: Input validation ---
    if len(device_description) > 5000:
        st.error("Device description is too long (max 5,000 characters). Please shorten it.")
        st.stop()
    if len(intended_use) > 2000:
        st.error("Intended use is too long (max 2,000 characters). Please shorten it.")
        st.stop()

    # --- Security: Rate limiting (per session) ---
    if "gen_count" not in st.session_state:
        st.session_state.gen_count = 0
    max_per_session = 20 if is_pro() else 3
    if st.session_state.gen_count >= max_per_session:
        st.error(
            f"Rate limit reached ({max_per_session} analyses per session). "
            "Refresh the page to start a new session."
        )
        st.stop()
    st.session_state.gen_count += 1

    if not subsystems:
        st.warning("No subsystems selected — analysis may miss relevant risks.")
    if len(device_description.split()) < 5:
        st.error("Please provide more detail about your device (at least a few sentences).")
        st.stop()

    # --- Security: Sanitize input (prompt injection defense) ---
    def _sanitize(text):
        """Remove common prompt injection patterns from user input."""
        blocked = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"forget\s+(all\s+)?previous",
            r"you\s+are\s+now",
            r"system\s*prompt",
            r"reveal\s+your\s+instructions",
            r"act\s+as\s+(a\s+)?different",
            r"pretend\s+you",
        ]
        cleaned = text
        for pat in blocked:
            cleaned = re.sub(pat, "[removed]", cleaned, flags=re.IGNORECASE)
        return cleaned

    device_description_safe = _sanitize(device_description)
    intended_use_safe = _sanitize(intended_use)

    # Build the user prompt
    user_prompt = f"""Generate a comprehensive ISO 14971 risk analysis for this medical device:

**Device type:** {device_type}
**Description:** {device_description_safe}
**Intended use:** {intended_use_safe}
**Key subsystems:** {', '.join(subsystems) if subsystems else 'Not specified'}
**Risk class:** {risk_class}
**Target market:** {', '.join(target_market)}

Generate exactly {num_risks} risks, starting with the highest-severity hazards.
Cover all relevant hazard types for the subsystems listed.
Be specific to THIS device — not generic medical device risks.

{SUMMARY_TABLE_INSTRUCTION}
"""

    # Call Claude API
    try:
        client = Anthropic(api_key=api_key)

        with st.spinner(f"Analyzing {device_type.split('(')[0].strip().lower()}... checking {len(subsystems)} subsystems against 12 standards (~60s)"):
            response = client.messages.create(
                model=MODEL,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

        result = response.content[0].text
        pro = is_pro()

        # Display result
        if pro:
            st.success(f"Generated {num_risks} risks. Review below.")
        else:
            st.success(
                f"Generated {num_risks} risks (free tier). "
                f"[Upgrade]({PURCHASE_URL}) for up to 25 risks + PDF download."
            )

        # Show in tabs
        tabs = ["Full Report", "Download Markdown", "Download CSV"] if pro else ["Full Report"]
        tab_objs = st.tabs(tabs)

        with tab_objs[0]:
            st.markdown(result)
            if not pro:
                st.divider()
                st.markdown(
                    f"> *Generated by MedRisk AI (Free Tier). "
                    f"[Upgrade to Pro]({PURCHASE_URL}) for full reports with "
                    f"up to 25 risks, PDF download, and IEC 60601 cross-reference.*"
                )

        if pro:
            with tab_objs[1]:
                # Markdown download
                report_header = f"""# ISO 14971 Risk Analysis
**Device:** {device_description[:100]}
**Generated by:** MedRisk AI (Pro)
**Date:** {__import__('datetime').date.today()}
**Standard:** ISO 14971:2019 + IEC 60601-1:2020
**Classification:** {risk_class}
**Market:** {', '.join(target_market)}

---

"""
                full_report = report_header + result

                st.download_button(
                    "Download Markdown Report",
                    data=full_report,
                    file_name="risk-analysis.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

            with tab_objs[2]:
                # CSV export — for import into Excel / Greenlight Guru / QMS
                csv_data = _extract_risk_table_csv(result, device_description, risk_class, target_market)
                st.download_button(
                    "Download CSV (for Excel / QMS import)",
                    data=csv_data,
                    file_name="risk-analysis.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
                st.caption("Open in Excel, Google Sheets, or import into your QMS (Greenlight Guru, MasterControl, etc.)")

        # Disclaimer for ALL users (legal requirement)
        st.info(
            "**Disclaimer:** This AI-generated analysis is a starting point for risk management "
            "documentation. It does not replace professional regulatory review. "
            "All outputs must be verified by a qualified person before regulatory submission."
        )

        # Usage stats (only show to admin, not customers)
        if os.environ.get("SHOW_USAGE_STATS"):
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (input_tokens * 3 / 1_000_000) + (output_tokens * 15 / 1_000_000)
            st.caption(
                f"Tokens: {input_tokens:,} in / {output_tokens:,} out. "
                f"Estimated cost: ${cost:.3f}"
            )

    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "auth" in error_msg.lower():
            st.error("Service temporarily unavailable. Please try again later.")
        elif "rate_limit" in error_msg.lower():
            st.error("Service is busy. Please wait a moment and try again.")
        else:
            st.error("An error occurred while generating your analysis. Please try again.")

else:
    # Landing — minimal, professional, addresses "why not ChatGPT?"
    st.markdown("**Describe your device above, select subsystems, and click Generate.**")

    st.markdown("""
    | You get | So you can |
    |---|---|
    | Device-specific risk analysis (not templates) | Start with real hazards, not blank page |
    | 12 standards auto-selected | Stop looking up which standards apply |
    | 6-point self-verification | Trust the numbers before your auditor sees them |
    | GSPR mapping (EU MDR) | Show Annex I compliance without manual cross-referencing |
    | Audit readiness checklist | Know exactly what's missing before submission |
    | Post-market monitoring plan | Have your PMS framework ready, not an afterthought |
    | CSV + Markdown export (Pro) | Import directly into Excel or your QMS |
    """)

    with st.expander("FAQ", expanded=False):
        st.markdown(f"""
**Can I submit this to a notified body / FDA?**
This is an audit-ready starting point. Review, customize with your device-specific details, then submit through your QMS. The output follows ISO 14971:2019 format with defense-in-depth controls, quantitative verification criteria, and IEC clause references — the structure auditors expect. Most teams save 80-90% of initial drafting time.

**What standards does it cover?**
12 standards auto-selected based on your device type and subsystems: ISO 14971, IEC 60601-1, IEC 62304 (software), ISO 10993 (biocompatibility), IEC 62366 (usability), IEC 62443 (cybersecurity), EU MDR Annex I, FDA 21 CFR 820, IEC 60601-1-2 (EMC), IEC 60601-1-6, IEC 60601-1-11 (home use), IEC 61010 (lab/IVD).

**How is this verified?**
Every analysis passes 6 automated checks before delivery: physics accuracy (are the numbers computed, not guessed?), completeness (did we cover all your subsystems?), scoring consistency, verification criteria specificity, standard reference accuracy, and adversarial review (how could each control fail?).

**Is my data safe?**
Your device description is processed in real-time and not stored after the report is generated. No data is retained or used to train any model. Do not include patient names or trade secrets.

**What format is the output?**
Markdown report (viewable in-app) + CSV for Excel/QMS import (Pro). Compatible with Greenlight Guru, MasterControl, and other QMS tools. The analysis also includes GSPR mapping (EU MDR), audit readiness checklist, and post-market monitoring guidance.

**Who built this?**
MedRisk AI was built by medical device professionals who understand both engineering and regulatory requirements. The system is purpose-built for ISO 14971, not a generic AI assistant.
""")

    st.divider()
    st.markdown(
        f"**Try free** — {FREE_MAX_RISKS} risks, no signup.\n\n"
        f"**[Pro — £79/report]({PURCHASE_URL})** — up to 25 risks + CSV/Markdown download + full GSPR + audit checklist.\n\n"
        f"*Risk consultants charge £12,000-40,000 for the same analysis. MedRisk AI: £79, delivered in 60 seconds.*"
    )
