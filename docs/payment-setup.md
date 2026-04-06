# Payment Setup — Lemon Squeezy

## Why Lemon Squeezy (not Stripe directly)

- Handles global tax compliance automatically (VAT, GST, sales tax)
- Simpler setup than Stripe for solo founder
- Built-in checkout pages (no code needed)
- License key delivery built-in
- 5% + $0.50 per transaction (vs Stripe 2.9% + $0.30 but you handle tax yourself)

---

## Step 1: Create Account (5 min)

1. Go to lemonsqueezy.com
2. Sign up with your new email (medrisk.ai.team@gmail.com)
3. Complete store setup:
   - Store name: MedRisk AI
   - Store URL: medrisk-ai.lemonsqueezy.com
   - Currency: USD
4. Add bank account or PayPal for payouts

## Step 2: Create "Pro Report" Product (10 min)

1. Products → New Product
2. Name: "MedRisk AI — Pro Report"
3. Description: "Full ISO 14971 risk analysis with up to 25 risks, PDF download, and IEC 60601 cross-reference table. One license key, use anytime."
4. Price: $99.00 (one-time)
5. Product type: Digital download
6. Tax category: "Software as a Service" or "Digital goods"

**License key setup:**
1. In product settings → "License keys" → Enable
2. Activation limit: 1 (one key = one user)
3. Key format: leave default (random alphanumeric)
4. After purchase, customer automatically receives license key in receipt email

## Step 3: Create "Annual" Product (10 min)

1. Products → New Product
2. Name: "MedRisk AI — Annual (Unlimited Reports)"
3. Description: "Unlimited ISO 14971 risk analyses for 12 months. Up to 25 risks per analysis, PDF download, IEC 60601 mapping."
4. Price: $499.00/year (recurring subscription)
5. License key: Enable, same as above

## Step 4: Get Checkout Links

After creating products:
1. Go to Products → select product → Share
2. Copy the checkout link for each:
   - Pro Report: `https://medrisk-ai.lemonsqueezy.com/buy/xxxxx`
   - Annual: `https://medrisk-ai.lemonsqueezy.com/buy/yyyyy`

## Step 5: Update Your App

On Streamlit Cloud → Settings → Secrets, add:

```toml
PURCHASE_URL = "https://medrisk-ai.lemonsqueezy.com/buy/xxxxx"
```

In `landing/index.html`, replace:
- `YOUR_LEMON_SQUEEZY_LINK_REPORT` → your Pro Report checkout link
- `YOUR_LEMON_SQUEEZY_LINK_ANNUAL` → your Annual checkout link
- `YOUR_APP_URL` → your Streamlit Cloud app URL

## Step 6: Managing License Keys

When someone buys:
1. Lemon Squeezy auto-generates a license key
2. Customer receives it in their receipt email
3. You see the key in Lemon Squeezy dashboard → Orders

To activate in your app:
1. Go to Streamlit Cloud → Settings → Secrets
2. Add the new key to LICENSE_KEYS:

```toml
LICENSE_KEYS = "DEMO-PRO-2026,abc123-def456,xyz789-uvw012"
```

3. Save. App reboots. Customer's key now works.

**Note:** This is manual for now. Once you have 20+ customers, automate with Lemon Squeezy webhooks. For the first customers, manual is fine and takes 30 seconds.

## Step 7: Test (15 min)

1. Enable test mode in Lemon Squeezy
2. Make a test purchase
3. Check: receipt email received? License key included?
4. Enter license key in app → Pro features unlock?
5. Disable test mode when ready to go live

---

## Money-Back Guarantee

Add to Lemon Squeezy product description:
"30-day money-back guarantee. If you're not satisfied with the quality, email medrisk.ai.team@gmail.com for a full refund."

Process refunds through Lemon Squeezy dashboard → Orders → Refund.
