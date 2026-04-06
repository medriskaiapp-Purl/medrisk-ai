# MedRisk AI — Launch Plan

Master plan. Execute step by step. Check off as you go.

---

## Phase 0: Identity Separation (30 min, do FIRST)

Everything else depends on this. MedRisk AI must have zero connection to your personal/work identity.

- [ ] Create new email: `medrisk.ai.team@gmail.com` (or similar)
- [ ] Create new GitHub account using that email (username: `medrisk-ai` or `medriskapp`)
- [ ] Check employment contract for side-activity / IP clauses (see `docs/legal-checklist.md`)

**After this phase:** You have a clean identity for the business.

---

## Phase 1: Deploy Web App (1-2 hours)

Goal: MedRisk AI is live on the internet, free tier works, anyone can try it.

| Step | What | How | Time |
|------|------|-----|------|
| 1.1 | Configure git identity | `cd ~/Projects/medrisk-ai && git config user.name "MedRisk AI" && git config user.email "YOUR_NEW_EMAIL"` | 1 min |
| 1.2 | Get Anthropic API key | anthropic.com → dashboard → API keys → create new key | 2 min |
| 1.3 | Test locally | `cd src && ANTHROPIC_API_KEY=sk-ant-... streamlit run app.py` | 5 min |
| 1.4 | First git commit | See `docs/deploy-guide.md` Step 1 | 5 min |
| 1.5 | Push to GitHub | Create repo on new GitHub account, push | 5 min |
| 1.6 | Deploy on Streamlit Cloud | share.streamlit.io → New app → connect repo → entry: `src/app.py` | 10 min |
| 1.7 | Add secrets on Streamlit Cloud | Settings → Secrets → `ANTHROPIC_API_KEY` | 2 min |
| 1.8 | Test live app | Open URL, run a free analysis, verify 5-risk limit works | 5 min |

| 1.9 | Add privacy notice to app | User sees what data goes to Claude API before first use | 15 min |

**After this phase:** App is live at `medrisk-ai.streamlit.app`. Free tier works. Privacy compliant.

---

## Phase 2: Payment Setup (1-2 hours)

Goal: People can pay $99/report or $499/year and get a license key.

| Step | What | How | Time |
|------|------|-----|------|
| 2.1 | Create Lemon Squeezy account | lemonsqueezy.com → sign up with new email | 5 min |
| 2.2 | Create "Pro Report" product | $99, one-time, digital delivery | 10 min |
| 2.3 | Create "Annual" product | $499/year, subscription | 10 min |
| 2.4 | Set up license key delivery | After purchase → email contains license key (see `docs/payment-setup.md`) | 15 min |
| 2.5 | Update app PURCHASE_URL | Set env var on Streamlit Cloud to your Lemon Squeezy checkout link | 2 min |
| 2.6 | Add license keys to secrets | On Streamlit Cloud: `LICENSE_KEYS = "key1,key2,key3"` | 2 min |
| 2.7 | Test full flow | Buy in test mode → get key → enter in app → verify Pro unlocks | 15 min |

**After this phase:** Complete purchase flow works. You can accept money.

---

## Phase 3: Landing Page (1 hour)

Goal: Professional marketing page at a custom URL, links to the app.

| Step | What | How | Time |
|------|------|-----|------|
| 3.1 | Update landing page links | Replace `YOUR_APP_URL` and `YOUR_LEMON_SQUEEZY_LINK_*` in `landing/index.html` | 10 min |
| 3.2 | Deploy landing page | Netlify: drag-drop `landing/` folder at app.netlify.com. Free, instant. | 5 min |
| 3.3 | (Optional) Buy domain | `medrisk-ai.com` or `medrisk.app` — Namecheap/Porkbun ~$10/year | 10 min |
| 3.4 | (Optional) Connect domain | Point DNS to Netlify (A record + CNAME) | 15 min |

**After this phase:** Professional landing page live. Funnel: Landing → Free trial → Purchase → Pro.

---

## Phase 4: Distribution — Zero Personal Brand (Week 1-2)

Goal: Get MedRisk AI in front of potential customers using platforms that don't need personal identity.

### 4A. Product Hunt Launch (TOP PRIORITY)
- [ ] Create maker account on producthunt.com using new email
- [ ] Prepare launch materials (see `docs/product-hunt-launch.md`)
- [ ] Schedule launch for Tuesday-Thursday
- [ ] Goal: 100+ upvotes, top 10 of the day

### 4B. Reddit + Indie Hackers
- [ ] Create anonymous Reddit account
- [ ] Post in r/medicaldevices, r/regulatoryaffairs (see `docs/reddit-strategy.md`)
- [ ] Create Indie Hackers profile, post build story

### 4C. Gumroad Listing
- [ ] Create Gumroad account with new email
- [ ] List MedRisk AI Pro Report ($99) with screenshots + sample output
- [ ] Gumroad has marketplace search — some organic discovery

### ~~4D. AppSumo~~ — REMOVED (see audit)
AppSumo keeps 70% of revenue, requires lifetime support on $18/customer, and 40% of LTD products fail within 3 years. Trap for solo founders. Do NOT pursue.

**After this phase:** MedRisk AI is visible on 3+ platforms. No personal brand exposed.

---

## Phase 5: App Store (Week 3-8, optional)

Goal: Native iOS app for App Store discovery + credibility.

- [ ] Set up Apple Developer account ($99/year) with new email
- [ ] Build React Native app (see `docs/app-store-plan.md` for 6-screen design)
- [ ] Submit to App Store with ASO keywords
- [ ] Pricing: Free download + $99 IAP + $499/year subscription

**After this phase:** "Available on the App Store" badge. Additional discovery channel.

---

## Phase 6: Build Moat — Before Window Closes (Month 2-6)

The prompt alone is NOT defensible. Must build features ChatGPT/Claude can't replicate.

### 6A. Device Template Library (Month 2-3)
- [ ] Pre-build risk templates for 20+ common device types
- [ ] Each template: pre-filled hazards, typical controls, relevant IEC clauses
- [ ] User selects device type → analysis starts with known risks as baseline
- [ ] WHY THIS MATTERS: saves user from describing common hazards, ChatGPT can't offer this

### 6B. Risk Database (Month 3-4)
- [ ] Store anonymized risks from customer analyses (with consent)
- [ ] Cross-reference: "Devices similar to yours typically have these risks"
- [ ] WHY THIS MATTERS: gets smarter with every customer. Proprietary data moat.

### 6C. Export Integration (Month 4-6)
- [ ] Export to Greenlight Guru CSV format
- [ ] Export to Excel (universal format for risk matrices)
- [ ] WHY THIS MATTERS: switching cost. Once in their QMS, they stay.

### 6D. Audit Simulation (Month 4-6)
- [ ] "What would an auditor ask about this risk?" mode
- [ ] Generates likely auditor questions + suggested responses
- [ ] WHY THIS MATTERS: unique feature no competitor has

**After this phase:** Product has real differentiation. Not just a prompt wrapper.

---

## Phase 7: SEO + Content (Month 2+, ongoing)

Goal: Long-term organic traffic from Google.

- [ ] Set up blog on landing page domain (or Medium under brand name)
- [ ] Write 1 post/week: "How to do ISO 14971 risk analysis", "IEC 60601 compliance guide"
- [ ] Each post links to free trial
- [ ] SEO compounds over 3-12 months

---

## Key Metrics to Track

| Metric | Tool | Target (Month 1) |
|--------|------|-------------------|
| Free analyses run | Streamlit Cloud logs | 100+ |
| License keys sold | Lemon Squeezy dashboard | 5+ |
| Revenue | Lemon Squeezy | $500+ |
| Product Hunt upvotes | producthunt.com | 100+ |
| App Store installs | App Store Connect | 50+ (if Phase 5 done) |

---

## Decision Gate: Week 8

After 8 weeks, evaluate:
- **Revenue > $500?** → Double down. Add features, more content, consider App Store.
- **Users but no revenue?** → Pricing problem. Try $49/report or different positioning.
- **No users at all?** → Distribution problem. Try cold email, different platforms.
- **Negative feedback on quality?** → Product problem. Improve system prompt.
