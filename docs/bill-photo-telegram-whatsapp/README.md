# Automated workflow: Bill photo on Telegram → calculations → WhatsApp

> **Deployed:** this workflow has been created in the n8n instance as
> **"Bill Photo → Calculations → WhatsApp"** (workflow ID `kqFjqmPinNbD8LHp`,
> https://kappulearnn8n.app.n8n.cloud/workflow/kqFjqmPinNbD8LHp).
> The JSON in this folder is a reference copy for re-import/recovery.

## What it does
1. **Trigger** — you (or anyone allowed to use the bot) send a **photo of a bill** to a Telegram bot.
2. n8n downloads the photo and an **AI vision model reads the bill** — merchant, date, invoice number, every line item, discounts, GST/other taxes, charges, and the printed grand total.
3. A **Code node performs the calculations**:
   - recomputes each line item (`quantity × unit price`) when the amount isn't printed,
   - sums items, subtracts discounts, adds each tax line (CGST/SGST/IGST etc.) and other charges,
   - computes the total tax as a % of the items total,
   - **cross-checks the computed grand total against the printed grand total** and flags any mismatch bigger than ₹1 (round-off tolerance),
   - **bifurcates the bill amount** between the four parties: **Kalpana 20%, Batra ji 25%, Jitender 25%, Joshi ji 30%** (rounding paise are absorbed by the largest share so the four shares always add up to exactly the bill total).
4. The formatted summary is **sent to a WhatsApp number** via the WhatsApp Business Cloud API.
5. The Telegram bot replies with the same summary as confirmation. If you send text (no image), the bot asks for a bill photo instead of failing.

```
Telegram Trigger ─► Has Bill Photo? ─► Get Bill Photo ─► Extract Bill Data (AI Vision)
                          │                                        │
                          ▼ (no photo)                             ▼
                    Ask For Photo                        Calculate Bill Totals
                                                                   │
                                                                   ▼
                                              Send to WhatsApp ─► Confirm on Telegram
```

## Import
1. In n8n: **Workflows → Add workflow → ⋯ → Import from file** and pick
   [`Bill_Photo_to_WhatsApp.workflow.json`](Bill_Photo_to_WhatsApp.workflow.json).
2. Attach credentials to the four nodes below, set the WhatsApp recipient, then **Activate**.

## Credentials & configuration

### 1. Telegram (nodes: *Telegram Trigger*, *Get Bill Photo*, *Ask For Photo*, *Confirm on Telegram*)
- Create a bot with **@BotFather** (`/newbot`) and copy the token — or reuse the existing
  bot token from the *Food Agent - Photo Flow* workflow if you want the same bot to handle bills too
  (note: only one active n8n Telegram Trigger can hold a bot's webhook at a time, so a **separate bot
  for bills is the safer choice**).
- In n8n create a **Telegram API** credential with that token and select it on all four Telegram nodes.

### 2. OpenAI (node: *Extract Bill Data (AI Vision)*)
- Uses the same **OpenAI API** credential type as the existing food-photo workflow; model is `gpt-4o`
  (vision). Select your OpenAI credential on the node.

### 3. WhatsApp Business Cloud (node: *Send to WhatsApp*)
1. Go to [developers.facebook.com](https://developers.facebook.com) → create an app → add the **WhatsApp** product.
2. From **WhatsApp → API Setup** copy:
   - the **Phone number ID** → paste into the node's *Phone Number ID* field
     (replace `YOUR_WHATSAPP_PHONE_NUMBER_ID`),
   - a **permanent access token** (create a System User in Business Settings and generate a token with
     `whatsapp_business_messaging` permission — the default token from API Setup expires in 24 h).
3. In n8n create a **WhatsApp API** credential with that token and select it on the node.
4. Set **Recipient Phone Number** to the destination number in international format without `+`
   (e.g. `9198XXXXXXXX`), replacing the `91XXXXXXXXXX` placeholder.

> **⚠️ WhatsApp 24-hour rule:** the Cloud API only delivers *free-form* text to a number that has
> messaged your WhatsApp business number within the last 24 hours. For this personal-automation use
> case the simple fix is: from the recipient's WhatsApp, send any message (e.g. "hi") to your business
> number once a day / whenever delivery stops. For fully unattended delivery, create a pre-approved
> **message template** in Meta Business Manager and switch the node's *Message Type* to Template.
> (Alternative: swap the node for **Twilio → WhatsApp**, which has the same session rule but an easier
> sandbox for testing.)

## The message that lands on WhatsApp

```
🧾 Bill Summary — Hotel Sagar
📅 09/07/2026  |  No: INV-4821

Items (3):
1. Paneer Butter Masala — 2 × ₹280.00 = ₹560.00
2. Butter Naan — 6 × ₹45.00 = ₹270.00
3. Fresh Lime Soda — 3 × ₹90.00 = ₹270.00

Items total: ₹1,100.00
Discount: -₹50.00
CGST @ 2.5%: ₹26.25
SGST @ 2.5%: ₹26.25
Total tax: ₹52.50 (4.77% of items)
Round off: ₹0.50

Grand total (printed): ₹1,103.00
Grand total (computed): ₹1,103.00
✅ Totals check out.

Bifurcation of ₹1,103.00:
Kalpana (20%): ₹220.60
Batra ji (25%): ₹275.75
Jitender (25%): ₹275.75
Joshi ji (30%): ₹330.90
```

If the printed total doesn't equal the computed one (beyond ₹1 round-off) the last line becomes:
`⚠️ MISMATCH of ₹X — printed total is HIGHER/LOWER than the computed one. Please verify the bill.`

## Customising the calculations
All arithmetic lives in the **Calculate Bill Totals** Code node:
- **Bifurcation shares** — edit the `SPLIT` array (names and `pct` values; percentages should total 100):
  ```js
  const SPLIT = [
    { name: 'Kalpana', pct: 20 },
    { name: 'Batra ji', pct: 25 },
    { name: 'Jitender', pct: 25 },
    { name: 'Joshi ji', pct: 30 },
  ];
  ```
  The split is applied to the printed grand total (falling back to the computed total if the printed
  one is unreadable), and any rounding paise are added to the last entry so shares sum exactly.
- **Round-off tolerance** — change `Math.abs(diff) <= 1`.
- **Extra derived figures** (e.g. per-person split, tip %, category tagging) — compute them in
  section 3 of the code and append lines to the message in section 4.
- **Currency** — amounts default to `₹` (Indian digit grouping); any non-INR currency detected on the
  bill is shown with its ISO code instead.

## Notes
- The bot accepts bills sent as a **photo** or as an **image file attachment** (it picks the
  highest-resolution version of Telegram photos).
- The AI is instructed to return strict JSON; the Code node still tolerates code-fenced or slightly
  wrapped output and fails loudly (visible in n8n executions) if the image is unreadable.
- The Telegram confirmation is sent **after** the WhatsApp send succeeds, so a confirmation on
  Telegram means the message really went out.
