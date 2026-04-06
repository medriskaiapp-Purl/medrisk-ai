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
    st.warning(
        "**Privacy Notice**\n\n"
        "MedRisk AI sends your device description to the Claude AI API (Anthropic) for analysis. "
        "Your data is processed but **not stored** by Anthropic or MedRisk AI after the response is generated.\n\n"
        "- Do NOT include patient names, personal data, or confidential trade secrets in your device description\n"
        "- Device descriptions are used solely to generate your risk analysis\n"
        "- No data is shared with third parties beyond the AI processing\n\n"
        "By clicking Accept, you agree to these terms.\n\n"
        "Questions? Contact medrisk.ai.app@gmail.com"
    )
    if st.button("Accept and Continue", type="primary"):
        st.session_state.privacy_accepted = True
        st.rerun()
    st.stop()

# --- Header ---
st.title("MedRisk AI")
st.caption("Your first ISO 14971 risk analysis in 10 minutes. Review, customize, import into your QMS.")

# --- Sample Output (trust before trial) ---
with st.expander("See a sample analysis (Pulse Oximeter)", expanded=False):
    st.markdown("""**Risk 2: SpO2 Measurement Error — Missed Hypoxemia**

**Risk ID:** RISK_02 | **Hazard:** Software/Diagnostic | **Subsystem:** Signal processing (PPG)

**Hazardous situation:** Device displays falsely normal SpO2 (97%) when patient is hypoxemic (actual <90%). Clinician does not intervene.

**Pre-control:** P1=3, S1=5 (RPN=15, U — MUST reduce)

**Controls:**
- 2a. Signal Quality Index (Safety by design): PI <0.3% or SQI <60% → SpO2 blanked ("---")
- 2b. Clinical validation (Safety by design): ISO 80601-2-61, n≥200, Arms ≤ 3%, Fitzpatrick V-VI
- 2c. Motion artifact rejection (Protective): Accelerometer + adaptive filter, >30s → blanked

**Verification:** Clinical accuracy Arms ≤ 3.0% | SQI blanking <5s | Dark pigmentation bias ≤ 1.0%

**Residual:** P2=2, S2=5 (RPN=10, A* — benefit-risk justified) | **Ref:** ISO 80601-2-61, IEC 62304
""")

st.divider()

# --- Main Area: Device Input Form ---
st.subheader("Describe your device")

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
        "**What's inside each analysis:**\n"
        "- 12 standards auto-selected\n"
        "- 18 hazard categories checked\n"
        "- 6-point self-verification\n"
        "- Physics-based, not generic"
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
    #### Why MedRisk AI, not ChatGPT?

    | | ChatGPT / Claude | MedRisk AI |
    |---|---|---|
    | **Verification** | None — states numbers without checking | 6-point self-verification (physics, scoring, completeness) |
    | **Standards** | Whichever you ask for | 12 standards auto-selected based on your device |
    | **Scoring rules** | Often scores everything "acceptable" | Enforces ISO 14971 post-control rules (P2, S2 justification) |
    | **Output format** | Different every time | Consistent, auditor-ready, QMS-importable |
    | **Export** | Copy-paste text | CSV for Excel / Greenlight Guru + Markdown |
    | **Prompt needed** | You write 30 min of instructions | 2 clicks |
    """)

    with st.expander("What's in each analysis", expanded=False):
        st.markdown("""
        - Device-specific hazard identification (not templates)
        - P x S scoring with post-control justification
        - Defense-in-depth controls: design > protective > information
        - Quantitative verification criteria (instruments + pass/fail values)
        - Multi-standard references (IEC 60601, 62304, 62366, ISO 10993, and 8 more)
        - 6-point self-verification before delivery
        """)

    with st.expander("FAQ", expanded=False):
        st.markdown(f"""
**Can I submit this to a notified body / FDA?**
This is a starting point, not a final submission. Review and customize the output, add your device-specific details, then submit through your normal QMS process. Most users save 80-90% of the initial drafting time.

**What standards does it cover?**
12 standards auto-selected based on your device: ISO 14971, IEC 60601-1, IEC 62304 (software), ISO 10993 (biocompatibility), IEC 62366 (usability), IEC 62443 (cybersecurity), EU MDR Annex I, FDA 21 CFR 820, and more.

**How is this different from ChatGPT?**
MedRisk AI runs 6 self-verification checks (physics, completeness, scoring consistency, verification criteria, standard references, adversarial review) before delivering results. ChatGPT gives you unverified output. See the comparison table above.

**Is my data safe?**
Your device description is sent to the Claude AI API for processing and is not stored afterward. We recommend not including patient names or trade secrets in your description.

**What format is the output?**
Markdown report (viewable in-app) + CSV for Excel/QMS import. Compatible with Greenlight Guru, MasterControl, and other QMS tools.
""")

    st.caption(f"Free: {FREE_MAX_RISKS} risks. [Pro]({PURCHASE_URL}) — up to 25 risks + download.")
