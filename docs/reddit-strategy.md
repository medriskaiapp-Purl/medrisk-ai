# Reddit + Indie Hackers Strategy

## Principle: Help First, Promote Never

Reddit bans self-promotion. The strategy: be genuinely helpful, mention the tool naturally.

---

## Target Subreddits

| Subreddit | Size | Strategy |
|-----------|------|----------|
| r/medicaldevices | Niche, active | Answer questions about risk management, ISO 14971 |
| r/regulatoryaffairs | Niche | Help with FDA/EU MDR compliance questions |
| r/biotech | Large | Relevant for device/diagnostic startups |
| r/QualityManagement | Small | ISO 13485, CAPA, QMS discussions |
| r/SaaS | Large | Share as "I built a tool" story |
| r/startups | Large | Share journey, get feedback |
| r/EntrepreneurRideAlong | Medium | Build-in-public format |

## Sample Posts

### Post 1: Value-first (r/medicaldevices or r/regulatoryaffairs)

**Title:** "I made a free tool that generates ISO 14971 risk analyses — looking for feedback"

```
I've been working on an AI tool that generates ISO 14971:2019-compliant
risk analyses for medical devices. You describe your device, and it
produces a full analysis with:

- Hazard identification specific to your device type
- P x S scoring with pre/post-control
- Defense-in-depth controls (design + protective + information)
- IEC 60601 clause cross-references
- Verification criteria with specific instruments and pass/fail values

Here's a sample output for a pulse oximeter (10 risks):
[link to sample PDF or markdown]

The free version generates 5 risks. I'm looking for feedback from
people who actually do risk management — is this useful as a starting
point? What would make it better?

Try it here: [link]
```

### Post 2: Build story (r/SaaS or r/startups)

**Title:** "I built an AI tool for medical device risk management — $0 to launch"

```
Quick background: medical device companies spend $15-50K on consultants
for ISO 14971 risk analysis. Small startups either skip it or do it
poorly. I built MedRisk AI to generate audit-ready risk documentation
in 10 minutes.

Tech stack: Streamlit + Claude API. Total cost to build: $0 (free
tier of everything). Time to build: 1 weekend.

What makes it different from generic AI:
- Physics-based arguments (not checkbox compliance)
- Specific IEC 60601 clause mapping
- Quantitative verification criteria
- Defense-in-depth enforcement for serious risks

Revenue model: Free tier (5 risks) → $99/report (25 risks + PDF) → $499/year

Currently at $0 revenue, 0 customers. Would love feedback on:
1. Is the pricing right?
2. Would you trust AI for regulatory documentation?
3. How would you find this tool if you needed it?
```

## Rules

- NEVER post the same link in multiple subreddits on the same day
- Wait at least 1 week between promotional posts
- Spend more time ANSWERING other people's questions than posting about your tool
- Upvote ratio matters — if a post gets downvoted, delete and rethink
- Some subreddits have "Show HN" style threads — use those

---

## Indie Hackers

Indie Hackers (indiehackers.com) is friendlier to self-promotion.

**What to post:**
1. "I'm building MedRisk AI — an ISO 14971 risk analysis tool" (milestone post)
2. Revenue updates: "$0 → first customer → $X MRR" (the community loves these)
3. Ask for feedback on pricing, positioning, features

**Build-in-public format works best:**
- Share wins AND losses
- Ask genuine questions
- Engage with other builders' posts
