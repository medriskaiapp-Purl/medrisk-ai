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
        "By clicking Accept, you agree to these terms."
    )
    if st.button("Accept and Continue", type="primary"):
        st.session_state.privacy_accepted = True
        st.rerun()
    st.stop()

# --- Header ---
st.title("MedRisk AI")
st.markdown("**AI-powered ISO 14971 risk analysis for medical devices**")
st.markdown("Generate audit-ready risk documentation in minutes, not months.")
st.divider()

# --- Sidebar: Device Input ---
with st.sidebar:
    st.header("Device Description")

    device_type = st.selectbox(
        "Device type",
        [
            "Imaging (MRI, CT, X-ray, Ultrasound)",
            "Therapeutic (Drug delivery, Stimulation, Ablation)",
            "Diagnostic (In-vitro, Blood analysis, Monitoring)",
            "Surgical (Robotic, Endoscopic, Powered instruments)",
            "Patient monitoring (Vital signs, Wearable)",
            "Implantable (Pacemaker, Stent, Prosthetic)",
            "In-vitro diagnostic (IVD)",
            "Other",
        ],
    )

    device_description = st.text_area(
        "Device description",
        placeholder="e.g., A portable ultrasound device for point-of-care cardiac imaging. Battery-powered, uses a phased array transducer at 2.5 MHz, wireless data transfer to tablet.",
        height=120,
    )

    intended_use = st.text_area(
        "Intended use / Indications",
        placeholder="e.g., Intended for cardiac imaging in emergency and primary care settings. Used by trained healthcare professionals for screening and follow-up.",
        height=80,
    )

    st.subheader("Key Subsystems")
    subsystems = []
    cols = st.columns(2)
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
    for i, sub in enumerate(subsystem_options):
        with cols[i % 2]:
            if st.checkbox(sub, key=f"sub_{i}"):
                subsystems.append(sub)

    risk_class = st.selectbox(
        "Risk classification",
        ["Class I", "Class IIa", "Class IIb", "Class III"],
        index=1,
    )

    target_market = st.multiselect(
        "Target market",
        ["EU (CE marking / MDR)", "US (FDA 510(k) / PMA)", "Canada (Health Canada)", "Other"],
        default=["EU (CE marking / MDR)"],
    )

    if is_pro():
        num_risks = st.slider("Number of risks to generate", 5, 25, 15)
    else:
        num_risks = FREE_MAX_RISKS
        st.markdown(f"**Risks:** {FREE_MAX_RISKS} (free tier). Upgrade for up to 25.")

    st.divider()

    # --- License Key ---
    st.subheader("License")
    license_key = st.text_input(
        "License key (leave empty for free tier)",
        type="password",
        key="license_key",
    )
    pro = is_pro()
    if pro:
        st.success("Pro license active")
    else:
        st.info(
            f"**Free tier:** {FREE_MAX_RISKS} risks, no PDF download.\n\n"
            f"[Upgrade to Pro]({PURCHASE_URL}) — $99/report or $499/year"
        )

    st.divider()
    st.caption("Powered by Claude AI. Your device data is not stored.")

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
    st.warning(
        "**Setup needed:** Set your Anthropic API key in "
        "`.streamlit/secrets.toml` (production) or `ANTHROPIC_API_KEY` env var (local dev).\n\n"
        "```toml\n# .streamlit/secrets.toml\nANTHROPIC_API_KEY = \"sk-ant-...\"\n```"
    )

if st.button("Generate Risk Analysis", type="primary", use_container_width=True):
    if not device_description:
        st.error("Please describe your device in the sidebar.")
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

        with st.spinner("Generating risk analysis... (this takes 30-60 seconds)"):
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
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

            st.info(
                "**Disclaimer:** This AI-generated analysis assists with risk management "
                "documentation. It does not replace professional regulatory review. "
                "All outputs should be verified by a qualified person before submission."
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
    # Landing content
    st.markdown("""
    ### How it works

    1. **Describe your device** in the sidebar (type, subsystems, intended use)
    2. **Click Generate** — AI produces ISO 14971-compliant risk analyses
    3. **Download** the report as Markdown or PDF

    ### What you get

    - Hazard identification specific to YOUR device
    - Risk scoring (P x S) with ISO 14971:2019 rubric
    - Control measures prioritized: design > protective > information
    - Verification criteria with quantitative pass/fail
    - IEC 60601-1:2020 clause cross-references
    - Residual risk justification auditors accept

    ### Pricing

    | | Free | Pro Report | Annual |
    |---|---|---|---|
    | **Price** | $0 | $99 | $499/year |
    | **Risks per analysis** | 5 | Up to 25 | Unlimited |
    | **PDF download** | — | Yes | Yes |
    | **IEC cross-reference** | — | Yes | Yes |
    | **Reports** | 1 per session | Per purchase | Unlimited |

    ### Why MedRisk AI?

    | Traditional | MedRisk AI |
    |------------|-----------|
    | Consultant: $15,000-50,000 | From $99 per report |
    | Timeline: 3-6 months | 10 minutes |
    | Generic templates | Device-specific analysis |
    | Checkbox compliance | Physics-based arguments |
    """)
