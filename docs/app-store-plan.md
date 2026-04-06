# App Store Plan (Phase 5 — After Web Validation)

Build this AFTER validating product-market fit on web. Don't invest 4-6 weeks before knowing if people want the product.

---

## Prerequisites

- [ ] Apple Developer account ($99/year) — use new email
- [ ] At least 5 paying web customers (validates demand)
- [ ] React Native or Swift development environment set up

## App Architecture

### 6 Screens

```
Screen 1: DEVICE INPUT
├── Device type picker (native)
├── Description text field
├── Subsystem toggle list
├── Risk class, target market
└── "Generate Analysis" button

Screen 2: GENERATING
├── Streaming progress indicator
├── Cancel button
└── Push notification when done (if backgrounded)

Screen 3: RISK REPORT
├── Native markdown rendering
├── Collapsible risk cards (tap to expand)
├── Summary table at bottom
└── Share button

Screen 4: RISK MATRIX (key differentiator — NOT a wrapper)
├── Interactive 5x5 heatmap (Probability x Severity)
├── Pre-control dots (red) + Post-control dots (green)
├── Tap any dot → shows risk detail
└── This is what makes it pass App Store review

Screen 5: SAVED ANALYSES
├── List of past analyses (local storage)
├── Offline viewing
├── Compare button (select 2 → side-by-side diff)
└── Delete / export

Screen 6: SETTINGS
├── Subscription status
├── PDF export (native Share Sheet → AirDrop, email, Files)
├── About / Privacy Policy
└── Restore purchases
```

### Native Features (required to pass App Store review)

Apple rejects "wrapper apps" — pure web views calling an API. Add these native features:

| Feature | Why it passes review |
|---------|---------------------|
| Risk matrix heatmap | Native iOS graphics (not web view) |
| Saved analyses | Offline functionality (Core Data / local storage) |
| PDF export via Share Sheet | Device-specific integration |
| ISO 14971 reference checklist | Works without internet |
| Push notifications | "Your analysis is ready" — device feature |
| Side-by-side comparison | Native UI, unique workflow |

### Tech Stack

**Option A: React Native (recommended for solo dev)**
- One codebase → iOS + Android
- JavaScript/TypeScript (easier to learn)
- Libraries: react-native-charts, react-native-pdf, react-native-share
- Claude API: native fetch() calls

**Option B: Swift (better for App Review, iOS only)**
- Apple's preferred language → smoother review
- SwiftUI for modern UI
- Charts framework built-in
- But: iOS only, no Android

### App Store Pricing

- Free download (includes 1 free analysis, 5 risks)
- In-App Purchase: $99 per full report
- Auto-Renewable Subscription: $499/year unlimited
- Apple commission: 15% (Small Business Program, <$1M revenue)

### ASO (App Store Optimization)

**Title:** "MedRisk AI - ISO 14971 Risk Analysis"
**Subtitle:** "Medical Device Risk Management"
**Keywords:** risk management, medical device, FDA compliance, ISO 14971, regulatory, QMS, IEC 60601, CE marking, risk analysis, audit

**Category:** Business (primary), Medical (secondary)

**Screenshots (6):**
1. Device input form (clean, professional)
2. Risk analysis report (detailed, impressive)
3. Risk matrix heatmap (the wow factor)
4. Side-by-side comparison
5. PDF export via share sheet
6. Pricing comparison (consultant vs MedRisk AI)

### Privacy Policy

Required by Apple. Must cover:
- What data is collected (device descriptions sent to Claude API)
- How data is processed (not stored, processed via Anthropic API)
- Third-party data sharing (Anthropic receives the device description)
- User consent (explicit before first analysis)
- Data deletion (no data stored = nothing to delete)

Host at: medrisk-ai.com/privacy (or a simple HTML page)

### Timeline

| Week | Task |
|------|------|
| 1 | Set up React Native project, basic navigation |
| 2 | Screen 1 (input) + Screen 2 (generating) + Claude API integration |
| 3 | Screen 3 (report) + Screen 5 (saved analyses) |
| 4 | Screen 4 (risk matrix heatmap) — the key differentiator |
| 5 | Screen 6 (settings) + In-App Purchase + PDF export |
| 6 | Testing, App Store submission, ASO |

### Submission Checklist

- [ ] App runs without crashes
- [ ] In-App Purchase works in sandbox
- [ ] Privacy policy URL set
- [ ] App description and screenshots ready
- [ ] Demo account or demo mode for Apple reviewer
- [ ] All screens work offline (saved analyses) or show graceful error
