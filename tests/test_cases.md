# MedRisk AI — Test Cases

Run each case, verify output quality. Check: physics verified? Scoring consistent? IEC clauses real? Verification criteria specific?

---

## Test 1: Pulse Oximeter (SIMPLE — start here)

- **Device type:** Patient monitoring (Vital signs, Wearable)
- **Description:** Fingertip pulse oximeter with SpO2 and heart rate display. Battery-powered, Bluetooth connectivity to mobile app. LED emitters at 660nm and 940nm.
- **Intended use:** Non-invasive monitoring of arterial oxygen saturation in adult patients. Home and clinical use by patients and healthcare professionals.
- **Subsystems:** Electrical, RF/Wireless, Software/Firmware, Battery/Portable, Optical/Laser, Patient contact surfaces
- **Risk class:** Class IIa
- **Market:** EU, US
- **Risks:** 5 (free tier test)
- **Expected:** Optical radiation, SpO2 accuracy, electrical leakage, battery safety, cybersecurity

---

## Test 2: Infusion Pump (COMPLEX — fluid + software)

- **Device type:** Therapeutic (Drug delivery, Stimulation, Ablation)
- **Description:** Portable volumetric infusion pump for IV drug delivery. Peristaltic mechanism, 0.1-999 mL/hr flow rate, 4.3" touchscreen, WiFi for EHR integration, rechargeable Li-ion battery.
- **Intended use:** Continuous and intermittent IV infusion of medications in hospital and home care settings. Operated by trained nurses and home care patients.
- **Subsystems:** Electrical, Mechanical, Software/Firmware, Fluid/Gas systems, Battery/Portable, Patient contact surfaces, RF/Wireless
- **Risk class:** Class IIb
- **Market:** EU, US
- **Risks:** 10 (pro tier test)
- **Expected:** Over-infusion, under-infusion, air embolism, occlusion, free flow, battery failure, software lockup, cybersecurity, biocompatibility, EMI

---

## Test 3: Digital Thermometer (SIMPLE — minimal subsystems)

- **Device type:** Diagnostic (In-vitro, Blood analysis, Monitoring)
- **Description:** Digital clinical thermometer with infrared tympanic sensor. Single-use probe covers. 2-second measurement, LCD display, fever alarm.
- **Intended use:** Temperature measurement in ear canal for fever screening. Home use by general population including children.
- **Subsystems:** Electrical, Battery/Portable, Patient contact surfaces
- **Risk class:** Class IIa
- **Market:** EU
- **Risks:** 5
- **Expected:** Measurement error, probe injury, battery leakage, cross-contamination, biocompatibility

---

## Test 4: Surgical Robot (COMPLEX — highest risk)

- **Device type:** Surgical (Robotic, Endoscopic, Powered instruments)
- **Description:** Robotic-assisted surgical system with 4 articulated arms, 3D HD vision system, master-slave control console. Electrosurgical capability, instrument exchange mechanism.
- **Intended use:** Minimally invasive surgery including general, urological, and gynecological procedures. Operated by trained surgeons in hospital OR.
- **Subsystems:** Electrical, Mechanical, Software/Firmware, Thermal, Optical/Laser
- **Risk class:** Class III
- **Market:** EU, US
- **Risks:** 15 (pro tier)
- **Expected:** Unintended instrument movement, electrosurgical burns, vision system failure, communication latency, instrument breakage, power failure, software crash, ergonomic (surgeon fatigue)

---

## Test 5: Wearable ECG Monitor (MID — wireless + contact)

- **Device type:** Patient monitoring (Vital signs, Wearable)
- **Description:** Continuous single-lead ECG patch worn on chest for 14 days. Adhesive, waterproof, Bluetooth Low Energy to smartphone app. AI-based arrhythmia detection algorithm.
- **Intended use:** Ambulatory cardiac monitoring for atrial fibrillation detection in adult patients. Prescribed by physicians, worn continuously.
- **Subsystems:** Electrical, RF/Wireless, Software/Firmware, Battery/Portable, Patient contact surfaces
- **Risk class:** Class IIa
- **Market:** US
- **Risks:** 10
- **Expected:** Skin irritation, false negative (missed AFib), false positive, data loss, battery failure, cybersecurity/PHI, adhesion failure, EMI, algorithm bias

---

## Test 6: MRI System (YOUR DOMAIN — complex imaging)

- **Device type:** Imaging (MRI, CT, X-ray, Ultrasound)
- **Description:** 1.5T superconducting MRI scanner with gradient system (45 mT/m, 200 T/m/s), 16-channel RF receive array, integrated patient table. Helium-cooled magnet.
- **Intended use:** Diagnostic imaging of brain, spine, musculoskeletal, abdominal, and breast. Hospital radiology departments, operated by trained radiographers.
- **Subsystems:** Electrical, Mechanical, Software/Firmware, Thermal, Magnetic field, RF/Wireless, Patient contact surfaces
- **Risk class:** Class IIa
- **Market:** EU, US
- **Risks:** 15
- **Expected:** Projectile (ferromagnetic), quench (helium), PNS (gradients), SAR (RF heating), acoustic noise, cryogen burns, claustrophobia, implant interaction, software/recon failure, table entrapment

---

## Test 7: IVD Blood Analyzer (LAB — no patient contact)

- **Device type:** In-vitro diagnostic (IVD)
- **Description:** Automated hematology analyzer for complete blood count (CBC). Processes 120 samples/hour, uses impedance and optical detection. Reagent cartridges, barcode sample tracking.
- **Intended use:** Quantitative analysis of blood cell counts in clinical laboratories. Operated by trained lab technicians.
- **Subsystems:** Electrical, Mechanical, Software/Firmware, Fluid/Gas systems, Optical/Laser
- **Risk class:** Class IIa
- **Market:** EU
- **Risks:** 10
- **Expected:** Wrong result (count error), sample carryover, reagent contamination, needle stick, biohazard (blood splash), laser safety, software misidentification, electrical safety

---

## Test 8: Implantable Pacemaker (HIGHEST RISK — Class III)

- **Device type:** Implantable (Pacemaker, Stent, Prosthetic)
- **Description:** Dual-chamber cardiac pacemaker with rate-responsive pacing. Titanium housing, silicone-insulated leads, lithium-iodine battery (8-year life). MRI conditional. Wireless telemetry for remote monitoring.
- **Subsystems:** Electrical, RF/Wireless, Software/Firmware, Battery/Portable, Patient contact surfaces, Magnetic field
- **Risk class:** Class III
- **Market:** EU, US
- **Risks:** 15
- **Expected:** Lead dislodgement, battery depletion, oversensing/undersensing, pacing failure, EMI vulnerability, MRI interaction, infection, lead fracture, software malfunction, cybersecurity, end-of-life behavior

---

## Verification Checklist (for each test)

After each test, check:

- [ ] **No hallucinated numbers** — every quantitative claim has a computation or standard reference
- [ ] **Scoring consistent** — similar hazards scored similarly across risks
- [ ] **P2 rules followed** — information alone didn't reduce P, S2=S1 unless harm nature changes
- [ ] **At least 1 risk is A*** — if all are A, scoring is too optimistic
- [ ] **IEC clauses plausible** — clause 8=electrical, 9=mechanical, 11=thermal, 14=software, 15=construction
- [ ] **Verification criteria specific** — named instruments, quantitative pass/fail, a test engineer could execute
- [ ] **Completeness** — all checked subsystems have at least one associated risk
- [ ] **No generic risks** — each risk is specific to THIS device, not copy-paste boilerplate
