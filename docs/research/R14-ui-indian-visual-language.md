# Research E: The Indian visual language for "Kaam ka Parcha"

Date: 2026-10-05. Scope: what Indian small-business owners and ordinary consumers already trust, turned into tokens and components for `/workshop`, `/customer/{id}` and `/verify`.

**How each claim was checked (applies to the whole report):**
- **[V-css]**: I pulled the value from the brand's live website CSS or JS with curl and a Python regex. Scripts and raw files are in the scratchpad (`sitecss.py`, `sites/`).
- **[V-font]**: I opened the font file from the `google/fonts` GitHub repo with fontTools and checked it directly (`fontcheck.py`, `fonts/`).
- **[V-shot]**: I looked at the brand's Google Play screenshots myself (`shots/`, `sheets/`).
- **[V-contrast]**: I computed the WCAG 2.x contrast ratio with a script.
- **[Src]**: Taken from a cited third-party web page. I did not check it against the product.
- **[UNVERIFIED]**: My own observation or common knowledge, with no primary source in this session.

**Limits of this research:**
- Medium, Brandfetch, Mobbin, Scribd and Amazon.in returned 403 or 503 (some blocked by a corporate proxy). Several designer case studies on Medium could only be read through search snippets.
- The web-search budget ran out partway through. Swiggy, Zepto, Ola and Meesho rely on secondary sources.

---

## 0. TL;DR

1. The apps this audience trusts all share one grammar:
   - a **light background**;
   - one **saturated brand colour** in the header or primary CTA;
   - **amounts in very large bold figures with ₹**;
   - **red/green credit-debit semantics**;
   - a **sticky bottom CTA, often split in two**;
   - **WhatsApp as the share channel**;
   - **illustrated "people like me" characters** (kurta, moustache, shop shelves);
   - a **language picker in which each script is shown in its own script**.

   None of them uses a dark developer-dashboard look.
2. The physical artefacts mechanics already use carry an equally strong visual vocabulary. Kaam ka Parcha can reuse it almost literally:
   - the carbon-copy **bill book**: white original, pink or yellow duplicate, a **red 6-digit serial number**, a perforated edge, ruled "Sl. No. / Particulars / Qty / Rate / Amount" columns, and a signature line;
   - the **violet** rubber-stamp seal.
3. Recommended direction: **"Digital Parcha" (Direction A)**. Each job card is a paper bill-book slip on a warm light "workshop counter" background:
   - ballpoint ink-blue for content;
   - a red serial number;
   - a violet rubber-stamp **"पक्का / SEALED"** stamp that lands at sealing time;
   - green reserved for "confirmed/verified";
   - haldi yellow for highlights only.

   Fonts: **Mukta** for UI and amounts (it has `tnum`, ₹ and Devanagari; checked), plus **Kalam** for handwriting-style mechanic notes.
4. Typography trap [V-font]: **Poppins and Hind have proportional digits and no `tnum` feature**, so ₹ columns will not line up. Mukta, Baloo 2, Anek Devanagari, Inter and Noto Sans do have `tnum`. Noto Sans, Noto Sans Devanagari and IBM Plex Sans Devanagari already have tabular digits by default.

---

## 1. What Indian apps actually look like (brand by brand)

### 1.1 Khatabook (digital *bahi-khata*)
- **App** [V-shot] (Play screenshots, package `com.vaibhavkalpe.android.khatabook`):
  - Header: saturated **royal blue** (sampled by eye, about `#0D47A1`/`#1A47A0`, [UNVERIFIED hex]).
  - Content: white cards on a light grey ground.
  - Ledger rows have a pale pink "YOU GAVE" column and a white "YOU GOT" column. Amounts are **red for "you gave"** and **green for "you got"**.
  - **Sticky split CTA at the bottom: red "YOU GAVE ₹" and green "YOU GOT ₹", side by side.**
  - Date chips ("22 Feb 24 • Today"), and running balances in small grey text ("Bal. ₹ 862").
  - A summary card with three big figures (You will get ₹4,33,567 / You will give ₹4,200 / Online Collections).
  - Reminders are shared to WhatsApp as a card with a mandala/rangoli corner ornament ("Payment reminder for ₹625 … Sent by Sattu Parathe Wala").
  - Indian digit grouping is used throughout (₹4,33,567).
- **Marketing**: pink-to-white gradient backgrounds, bold red headline type, and flat illustrated shopkeepers (kurta, moustache, cash in hand, hanging chips packets).
- **Website theme** [V-css] (Next.js/MUI bundle on khatabook.com):

  | Token | Hex |
  |---|---|
  | primary | `#C82128` |
  | primary light | `#FCF4F4` |
  | secondary | `#FEC855` |
  | navy | `#20386E` |
  | blues | `#375A8D` / `#355C90` |
  | ink | `#0E1725` |
  | brand rose | `#C67764` |

  Fonts: **Source Sans Pro, Noto Sans, Poppins**, and Grand Hotel as a script accent.
- Brandfetch lists Contessa `#C67764`, Wisp Pink `#FDF2F3` and Ebony `#0D1726` [Src].
- The design team is "Khatabook.Design – crafting experiences for the next billion users". Its Dribbble shows an "Illustration system" and an "Our Small business owners" character set [Src].
- **Borrow:** the red/green split sticky CTA, the ledger row tinting, the 3-figure summary strip, and the WhatsApp reminder card with an ornament.

### 1.2 OkCredit
- **App** [V-shot]:
  - Green brand. Pale grey-green cards and amounts in red.
  - Avatar photos carry a small green verified-tick badge.
  - A "Remind Defaulters" pink alert strip.
  - Pill FAB "+ Add Customer" and a bottom nav.
  - **Language picker**: a 2-column grid of pastel tiles. Each tile names the language **in its own script** (हिंदी, ગુજરાતી, தமிழ், বাংলা) with a small English label underneath, and each script gets a different pastel. "Hinglish – Hindi in English" is offered as a separate option.
  - The WhatsApp reminder card says "**OkCredit Verified**" with a check icon and "Due as on: 27 Feb".
- **Website tokens** [V-css]:

  | Token | Hex |
  |---|---|
  | `--green` | `#0E7A41` |
  | `--green-dark` | `#0A5C31` |
  | `--green-bright` | `#16A85C` |
  | `--green-tint` | `#E3F4EA` |
  | `--red` | `#C0392B` |
  | dark greens | `#1D3B36`, `#17332B` |
  | amber | `#B47A0B` / `#F5A623` |

  Font: **Plus Jakarta Sans** (Noto Sans for Indic).
- **Borrow:** the language tile grid, the "Verified" badge on shared cards, and the green-tint surfaces.

### 1.3 Vyapar (GST billing for SMBs)
- Brand **crimson `#ED1A3B`** [V-css; also Src], with `#F79F1F` mango in the logo [Src] and navy `#314259` [Src]. Website font: **Poppins** [V-css].
- `#ED1A3B` on white is only 4.36:1 [V-contrast]: it fails AA for body text and passes only for large text and UI elements.
- The app is invoice-centric. Printed-invoice themes are a selling point, and Khatabook copies this with "Premium / Thermal / Basic" invoice themes [V-shot].
- **Borrow:** treat the PDF as a first-class "theme". Offer a *thermal-receipt* look and a *bill-book* look.

### 1.4 PhonePe (consumer) and PhonePe Business
- **Consumer** [V-css]: brand purple `#5F259F` (named "Daisy Bush") [Src]. Website variants are `#361968`, `#5E2B9D`, `#6739B7`, `#492187`. Text primary `#05020A`, secondary button cyan `#07C3DE`. Fonts on the site: Inter Tight and Bebas Neue. Third-party sources say the app uses Inter [Src, UNVERIFIED for the app].
- **Brand identity** by Codesign (Mohor Ray) [Src]:
  - The purple was shifted to a "warmer, richer shade" so it would not look faded in Indian conditions.
  - The **Devanagari "पे"** descender is built into every icon.
  - Illustrations are modular and gender-neutral.
  - A **sonic logo** was re-engineered to cut through ambient noise and signals a successful payment.
- **Success screen** [V-shot]:
  - A big green filled circle with a white tick, then "…fetched successfully", then the bank logo line, then a **large amount (₹2000)**.
  - A single text CTA "DONE" sits at the bottom.
  - The screen is white and minimal.
- **PhonePe Business** [V-css + V-shot]:
  - The merchant app is **green, not purple**: `--primary:#007C08`, `--primaryDark:#043F32`, `--primaryLight:#EAF6EB`, `--brand:#5F259F`.
  - Website fonts: **Archivo + Manrope**.
  - The app has a green header, "Today's Collection ₹20,564" in big green figures, a "Settled" green pill on each transaction row, tabs and a bottom nav.
  - The SmartSpeaker soundbox is advertised with Amitabh Bachchan ("#MeriDukaanKaSuperstar").
- Takeaway: **merchants equate green with "money arrived/settled"**, even inside a purple brand.

### 1.5 Paytm
- Brand blues **`#002970` navy and `#00BAF2` cyan**, website font **Inter** [V-css].
- A design-system case study (Yellowslice) lists Mulish, `#243C7A`, `#3FA5E0`, `#00BAF1` and others [Src].
- The CDO (Rahul Saini) on the PODS design system: "the user wants to accomplish their task in the shortest possible time and with the least amount of friction" [Src].
- An analysis of the success page found that a **pink-tinted rating block on the success page made users think something had gone wrong** [Src]. **Never put red or pink near a success state.**
- **Paytm Soundbox** [Src]:
  - It reads each payment amount aloud in 8–11 languages.
  - More than 6.8 million devices are deployed.
  - It exists because "India has historically been a low-trust society … people seek multiple confirmations".
  - BharatPe's version is "Paisa Bolega".
- Shopkeepers are told not to trust a customer's success screenshot and to confirm by soundbox or bank SMS [Src].
- **This is the cultural precedent for Kaam ka Parcha's voice read-back.**

### 1.6 Google Pay India (Tez → GPay)
- Built for 1 GB RAM phones and new internet users, in 8 languages, and some users navigate by audio alone [Src: Increment].
- **Payments are grouped as a chat thread per person or merchant**, because "payments are not just payments but an interaction between individuals" [Src].
- Website [V-css]: Google Sans and Roboto, M3 blue `#0B57D0`, ink `#1F1F1F`, `#444746`, surface `#F0F4F9`.
- Success = a blue check with a wave animation (Wallet) [Src].
- The Tez-era scratch cards turned rewards into a ritual [Src].
- **Borrow:** a chat-thread metaphor for the customer page (mechanic → owner messages, owner's "haan theek hai" reply as a bubble).

### 1.7 BharatPe
- Website [V-css]: Poppins + Lato, blues `#004085`/`#2B7BFF`, green `#0A6E3A`/`#2DD882`.
- Brandfetch lists Surfie Green `#10707F`, Mandy `#E4606D`, Carnation `#F37160` and Roboto [Src, UNVERIFIED].
- Known for the "Paisa Bolega" audio confirmation [Src].

### 1.8 Meesho
- Landor rebrand [Src]. Colours are named in Hindi: **"Jamuni" (purple)** for aspiration and **"Aam" (mango)** for warmth.
- Fonts: **Nunito Rounded** for display and **Mier** for body. The visual system is designed for low-resolution devices.
- The Mesh design system reduced the palette to 24 shades with higher contrast, and the rebuild raised conversion by 14% [Src].
- **Borrow:** name tokens in Hindi (`--haldi`, `--sindoor`, `--neela`). The team and users will remember them.

### 1.9 Swiggy and Zomato (order tracking)
- **Swiggy**: orange `#FC8019`, a custom Futura logotype, and Basis Grotesque in the product [Src]. The site could not be fetched.
- **Zomato**: red `#E23744` [Src]. On the website the in-product red is `#EF4F5F` and the ink is `#1C1C1C`; fonts are **Okra** (their customised Metropolis), Our Lexend and Wasabi [V-css].
- Order-tracking pattern [UNVERIFIED, common knowledge]:
  - a **vertical stepper / timeline** (Order placed → Preparing → Out for delivery → Delivered);
  - the current step pulses;
  - an ETA appears in a big number at the top;
  - the delivery partner's card has a call button.
- **Borrow:** the stepper for job-card status (Bola → Parcha bana → Call pe padha → Haan → पक्का).

### 1.10 Rapido and Ola
- **Rapido** [V-css]: yellow `#FFCA20` and `#F9C935`, black `#000`, ink `#1A202A`, pale yellow tints `#F8EFBC`/`#FBF7DD`, fonts **Poppins + Noto Sans**.
  - Black on `#FFCA20` = 13.7:1 [V-contrast].
  - Yellow helmets act as "moving billboards" [Src].
  - Rapido has a token-based design system in Jetpack Compose [Src].
- **Ola**: black and lime `#D6DF22` logo [Src, UNVERIFIED for the current identity].
- Both are the reference for a **high-visibility, outdoor, two-wheeler-world** look.

### 1.11 Zepto
- Purple brand. Brandfetch-style sources list Electric Violet `#950EDB` [Src, UNVERIFIED: that source may mix it up with ZeptoExpress Malaysia]. The site returned 202 with an empty body.

### 1.12 Urban Company, including the partner (technician) app
- Website [V-css]:
  - near-monochrome: ink `#212121`/`#0F0F0F`, grey `#545454`, surfaces `#F5F5F5`;
  - accent red `#DD0017`, purple `#6E42E5`, blue `#304FFE`;
  - proprietary fonts `os_regular / os_semi_bold / os_bold` (identity unknown).
- The **Align** design system covers both the customer and partner apps, with LTR and RTL variants of every component [Src].
- The first flow they standardised was "**partner receives their payments**", after finding **40 different primary buttons** in the partner app [Src: Obvious].
- Partner app screenshots [V-shot, not in detail]: white UI, black primary buttons, large earnings figures.
- **Borrow:** monochrome plus one accent works for skilled-trade partners. One primary button style only.

### 1.13 GoMechanic (the closest category)
- Website [V-css]: brand red **`#E73C33`**/`#E03E2F`, navy `#071C2C`/`#083250`, ink `#282828`/`#4A4A4A`, surface `#F6F6F6`, green `#3A9B14`, font **Gilroy**.
- An older palette quotes red `#EB162C` [Src].
- The logo is a wrench in negative space that doubles as car headlights [Src: NH1 Design].
- The Play listing returned 404. The app may be delisted or renamed [UNVERIFIED].
- The visual is generic "auto service": red, navy and white with photos of cars.
- **Do not copy it.** It reads "aggregator", not "my local mistri".

### 1.14 WhatsApp (the channel the customer arrives from)
- Brand `#25D366`, teal `#075E54`, `#128C7E` [Src; the canonical source is Meta's brand centre].
- Current light chat [Src: codefronts recreation, consistent with V-shot]:

  | Element | Value |
  |---|---|
  | wallpaper | `#EFE7DE`/`#EFEAE2` doodles |
  | outgoing bubble | `#D9FDD3` |
  | incoming bubble | `#FFFFFF` |
  | text | `#111B21` |
  | timestamp | `#667781` |
  | read ticks | `#53BDEB` |
  | bubble radius | ~7–9px, with a tail |
  | bubble shadow | `0 1px 0.5px rgba(11,20,26,.13)` |

  The old outgoing bubble was `#DCF8C6`.
- Dark mode: bg `#111B21`, outgoing `#005C4B`.
- `#25D366` on white is only **1.98:1** [V-contrast]. Never use it for text. Use `#008069` (4.89:1) for WhatsApp-green text and icons.
- Voice-note UI [UNVERIFIED, from use]:
  - a round play button, a dotted/bar waveform, the duration in grey, and the sender's avatar with a mic badge;
  - the mic turns blue once the note has been played;
  - press-and-hold a big green round mic, slide to cancel, swipe up to lock.
- **Borrow:**
  - the voice-note bubble for the mechanic's recording and the call transcript;
  - the green round hold-to-talk mic;
  - single, double and blue ticks as a "sent / delivered / owner heard" metaphor.

### 1.15 Government trust UI (UX4G, DigiLocker, Aadhaar)
- **UX4G** (MeitY/NeGD, the official GoI design system) [Src, fetched from ux4g.gov.in]:
  - **Noto Sans** at 400/500/600/700 for Hindi and English; body text at least 16px; **Devanagari line-height raised to 1.8**.
  - Palette "rooted in national identity":
    - Brand Purple 600 `#4A2BC2` (8.69:1 on white [V-contrast]; UX4G itself states 16.75:1, which is wrong);
    - Saffron 400/500 `#E89C30`/`#C47D00`;
    - semantic green, red, orange and cyan scales;
    - neutrals `#FAFAFA` to `#171717`.
- **DigiLocker**: issued documents carry a "**Signature valid ✓**" green-tick badge. The "Verified" badge was redesigned for recognisability [Src].
- **Aadhaar Secure QR**:
  - The data is *digitally signed, not encrypted*.
  - The scanner app shows the masked demographic data plus the photo, to be compared with the card.
  - Failure says "QR Code not verified" [Src].
- **Borrow for `/verify`:**
  - the same mental model: scan, then **"Parcha asli hai ✓ / Signature valid"**, then show the sealed contents to compare with the paper;
  - an explicit red failure state ("Yeh parcha match nahi hua").

---

## 2. The physical artefacts: bill book, estimate book, job card

| Feature | What it looks like | Source |
|---|---|---|
| Copies | **Duplicate**: white original (to customer) and **pink or yellow** copy that stays in the book. **Triplicate**: white, pink, yellow. Colour order by convention: white → pink → yellow → green → blue | [Src: Shekhawati Printers, Shivani Enterprises, IndiaMART] |
| Paper | Original 60–90 gsm white bond or maplitho, duplicates 55–70 gsm tinted. **NCR carbonless** ("no carbon required") or loose carbon sheets | [Src] |
| Serial no. | **Mechanical "crash" numbering, 6 digits, in red ink**, e.g. `000101`–`000150`, printed in the top-right corner, often in a typewriter-like numbering-machine face | [Src] |
| Book | 50 sets per book (33 for triplicate). Hard strawboard cover with a cloth spine, plus a cardboard writing shield. **Micro-perforated** tear-off on the original; the record copy stays bound. Left or top binding. Common sizes A5, 1/4 Demy, and pocket 1/6 foolscap (≈11×14.5 cm) | [Src] |
| Layout | Header: shop name (big, often in a Devanagari display face), address, phone, sometimes "GSTIN". Rows: `Sl. No. / Particulars / Qty / Rate / Amount` (some books split Amount into `Rs.` and `P.`). Footer: Total, "E.&O.E.", "Thank you, visit again", **signature line ("For <Shop name>" … "Authorised Signatory")**. Revenue-stamp box for cash receipts over ₹500 | [Src: Vyapar cash-memo page, Khatabook blog, billonline] |
| Bilingual | Hindi-English bill books are sold widely ("Hindi-English format bill book") | [Src] |
| Garage job card | Fields: Regn. No., Make/Model, colour, **Odometer (km)**, fuel level (often a fuel-gauge drawing), Date/Time in and out, customer name and mobile, "Customer complaints / Demanded repairs", labour and spares lists with amounts, mechanic assigned, estimate total, customer signature authorising the work | [Src: scribd and pdfcoffee titles; the bodies were blocked; field list is UNVERIFIED in detail] |
| Rubber stamp | Indian stamp-pad ink is **violet by default** (Camlin sells violet, red and black; Soni Officemate's 500 ml is violet). Blue is also common. **Red** is used for "PAID", "CANCELLED", "DUPLICATE" and urgent marks. Firms keep a 3-piece set: **round firm seal** (name around the rim), **Proprietor** stamp, **Authorised Signatory** stamp. Prints are always imperfect: patchy ink, a slight rotation, a double rim line | [Src: Camlin, Flipkart, rubberstampwala] + [UNVERIFIED: print look] |
| Handwriting | Item lines written by hand in ballpoint blue (Reynolds/Cello culture), totals underlined twice, corrections struck through and initialled | [UNVERIFIED, common knowledge] |

**What to reuse digitally:**
1. **Paper slip card**: an off-white card with faint ruled rows, a column rule before Amount, and a **perforated top edge** (CSS radial-gradient "holes" or a dashed line with semicircle notches).
2. **Red serial number** top-right: `№ 000127` in a mono or typewriter-ish face. It is tabular and never reused, so it is a cheap trust cue.
3. **Copy label**: "ORIGINAL / मूल प्रति" on the customer view, and a pink **"DUPLICATE – workshop copy"** tint on the mechanic view. This mirrors who keeps which copy.
4. **"पक्का / SEALED" rubber-stamp animation**:
   - violet ink, a double rim, the shop name around the circle, date in the centre;
   - lands rotated about -8°, with scale 1.6→1 and a 120ms squash, then a slight ink "bleed" (SVG `feTurbulence` + `feDisplacementMap` mask for texture);
   - optional thump sound and haptic (`navigator.vibrate(30)`).
5. **Signature line**: "For <Garage name> ______ Mistri" and "Gaadi maalik ki manzoori: haan theek hai ✓ (call 14:32)". The voice "haan" *is* the signature.
6. **Double underline under the total** and the amount in words ("Rupaye do hazaar chaar sau pachaas maatra"). Indian cheques and bills write the amount in words, and it works as a tamper cue.

---

## 3. Indian trust cues and colour meanings

- **The UPI success grammar** (PhonePe, GPay, Paytm, fake-app scam studies) [Src + V-shot]:
  - big **green tick** in a filled circle;
  - "Payment Successful" / "Paid to <name>";
  - **amount in the largest type on screen**;
  - counter-party, then timestamp, then transaction/UTR ID;
  - payment-app logo;
  - sound and vibration.

  Scam studies show that **shopkeepers know screenshots can be faked**, so the real trust comes from *an independent channel*: soundbox voice, bank SMS. Kaam ka Parcha should show *who confirmed and how*, for example "Owner ne call pe 'haan theek hai' bola – 14:32, 0:41 recording", and offer a QR to `/verify`.
- **Verified badges**: the DigiLocker "Signature valid ✓" and OkCredit "Verified" patterns are green ticks *with text*. Never use colour alone; this is also a UX4G rule.
- **Seal and stamp**: rubber stamps carry legitimacy in Indian offices. Nothing is "official" until stamped. Violet ink reads "official office stamp"; red reads "PAID / CANCELLED".
- **Hologram cues** [UNVERIFIED]: on PAN, Aadhaar PVC and RC cards, and on product security labels, a rainbow foil shimmer signals "original". Use it sparingly, for example as a thin animated iridescent border on the sealed card's QR and only on `/verify`.
- **Colour meanings in this audience** [mostly UNVERIFIED cultural knowledge; partly supported by app behaviour]:

  | Colour | Meaning |
  |---|---|
  | Green | Money in, settled, success, "OK". Universal in Khatabook, OkCredit and PhonePe Business [V-shot] |
  | Red | Money out, *udhaar* (you gave), due, error. On paper, also serial numbers and the "PAID" stamp. In culture, *sindoor/kumkum* = auspicious (shubh) |
  | Saffron / haldi yellow | Auspicious beginnings and festivals; also caution/high-viz in workshops. Fine for highlights, but never for text on white (1.79:1 [V-contrast]) |
  | Violet / purple | Rubber-stamp ink, PhonePe/UPI-era fintech, and the UX4G government brand. Strong "official" association |
  | Blue | Ballpoint ink, banks (SBI, Paytm), Khatabook header. "Written / record" |

  Avoid pink or red near success (Paytm finding) [Src].

---

## 4. Typography for Hindi + English

### 4.1 Checked font facts (fontTools on google/fonts files) [V-font]

| Font | ₹ U+20B9 | Devanagari | `tnum` | Digits tabular by default? | Notes |
|---|---|---|---|---|---|
| **Mukta** (Ek Type) | yes | yes | **yes** | no (use `tnum`) | 7 weights. Used by Dainik Jagran and Lokmat online [Src]. Mono-linear, calm UI face |
| **Baloo 2** | yes | yes | **yes** | no | Variable weight 400–800. Friendly, rounded, "next billion" display |
| **Anek Devanagari** | yes | yes | **yes** | no | Variable width 75–125 and weight 100–800. Condensed widths suit amounts and tables |
| **Noto Sans** / **Noto Sans Devanagari** | yes | yes | yes / – | **yes** | UX4G standard. Very neutral |
| **IBM Plex Sans Devanagari** | yes | yes | – | **yes** | Technical feel |
| **Inter** | yes | **no** | yes | no | Latin only. Pair with a Devanagari face |
| **Poppins** (ITF) | yes | yes | **no** | **no (9 different digit widths)** | Very common in Indian products (Vyapar, Rapido, BharatPe sites [V-css]), but amounts will not align in columns |
| **Hind** (ITF) | yes | yes | **no** | **no** | Designed for UI; Devanagari is 94% of Latin cap height [Src] |
| **Kalam** (ITF) | yes | yes | no | no | Handwriting style. Good for "mechanic's note"; not for amount columns |
| **Tiro Devanagari Hindi** | yes | yes | – (`pnum` only) | no | Bookish serif. Good for a "printed header" of the bill book |
| Rozha One / Yatra One | yes | yes | no | no | Signboard and poster display faces (shop-name header) |
| Teko / Rajdhani / Khand (ITF) | yes | yes | no | no | Condensed, industrial, number-plate feel. Good for registration numbers |
| JetBrains Mono / Roboto Mono | **no** | no | – | yes | **No ₹ glyph**. Don't use for amounts |
| Courier Prime / Special Elite | **no** | no | – | – | Typewriter style, but no ₹ |

Caveats:
- `tnum` support was checked in the full repo fonts. I did **not** check whether the Google Fonts CSS API keeps `tnum` in the subsetted woff2 [UNVERIFIED]. Test with `font-variant-numeric: tabular-nums` on a column of ₹ values. If it fails, self-host the TTF from `google/fonts`.
- The x-height/upm ratios measured are Mukta 0.468, Hind 0.505, Poppins 0.548 and Noto Sans 0.536 [V-font]. Mukta looks smaller at the same px size, so set Mukta body text at 17px, not 16px.

### 4.2 What Indian products use
- Website-level fonts are [V-css]; the apps themselves may use other faces:

  | Product | Fonts |
  |---|---|
  | Khatabook | Source Sans Pro + Noto Sans + Poppins |
  | OkCredit | Plus Jakarta Sans + Noto Sans |
  | Vyapar | Poppins |
  | PhonePe | Inter Tight + Bebas Neue |
  | PhonePe Business | Archivo + Manrope |
  | Paytm | Inter |
  | Rapido | Poppins + Noto Sans |
  | GoMechanic | Gilroy |
  | Zomato | Okra |
  | Google Pay | Google Sans |
  | Meesho | Mier + Nunito Rounded [Src] |

- Pattern: **a geometric/grotesque Latin face, with Noto as the Indic fallback**. Few products pick a face designed for both scripts together. Mukta or Baloo 2 is a differentiator, and Devanagari and Latin share the same rhythm.

### 4.3 Number formatting
- Use `Intl.NumberFormat('en-IN', {style:'currency', currency:'INR', maximumFractionDigits:0})`. It gives **₹1,23,450** (lakh grouping) [standard ECMA-402 behaviour; UNVERIFIED in this session].
- For Hindi UI use `hi-IN`, which keeps Latin digits by default. **Use Latin digits even in Hindi UI.** Every app screenshot reviewed uses Latin digits with Devanagari text [V-shot]. Devanagari digits (०१२) are available in all the Devanagari fonts checked [V-font], but they are read more slowly.
- Write ₹ directly before the number with no space, or with a thin space (`₹ 4,603` as Khatabook does).
- Line-height: 1.5 for Latin and **1.7–1.8 when Devanagari is present** (UX4G).

---

## 5. Three candidate visual directions

### Direction A: "Digital Parcha" (bill-book slip) — **RECOMMENDED**
Concept: every job card is a torn-off slip from a bill book, lying on a warm workshop counter. The mechanic sees the pink **duplicate**; the owner sees the white **original**. Sealing stamps it.

**Palette** (contrast [V-contrast], all on paper `#FFFDF6` unless noted):

| Token | Hex | Use | Contrast |
|---|---|---|---|
| `--counter` (page bg) | `#F3EEE3` | warm kraft-grey "counter" | – |
| `--paper` | `#FFFDF6` | card surface, original copy | – |
| `--paper-pink` | `#FCE4EC` | duplicate (workshop) copy tint | ink on it 12.96 AAA |
| `--paper-yellow` | `#FFF3C4` | triplicate / highlight row | ink on it 14.01 AAA |
| `--ink` | `#1B2433` | body text | 15.32 AAA (13.48 on counter) |
| `--ink-muted` | `#5B6472` | labels, meta | 5.88 AA (5.17 on counter) |
| `--neela` (ballpoint blue) | `#1F3A8A` | handwritten items, links, primary button | 10.16 AAA; white on it 10.34 |
| `--sindoor` (stamp/serial red) | `#B3261E` | money due, errors, serial number | 6.42 AA; white on it 6.54 |
| `--serial` | `#C0262D` | serial `№ 000127` | 5.80 AA |
| `--jamuni` (stamp violet) | `#5B2E91` | **पक्का / SEALED stamp**, seal icon | 9.19 AAA |
| `--hara` (seal green) | `#0E7A41` | confirmed, verified, "haan" | 5.32 AA; white on it 5.41 |
| `--haldi` | `#F2B705` | highlight fills, active-step dot, mic glow. **Never text on paper** (1.79) | ink on haldi 8.58 AAA |
| `--rule` | `#D9CFBC` | ruled lines (decorative, 1.52, intended) | – |
| `--wa-green` | `#008069` | WhatsApp CTA icon and text (`#25D366` only as a fill behind dark text) | 4.89 AA |

**Fonts:**
- `--font-ui`: `"Mukta", "Noto Sans Devanagari", system-ui, sans-serif`. Weights 400/500/700/800. Body 17px, line-height 1.6 (1.75 for Hindi-heavy blocks).
- `--font-amount`: Mukta 800 with `font-variant-numeric: tabular-nums`. The total is 40–48px, rows 18px.
- `--font-hand`: `"Kalam", "Mukta", cursive`, weight 400/700. Only for the "mechanic's note" line and the signature.
- `--font-display` (shop-name header, stamp text): `"Baloo 2"` 800. The stamp text uses letter-spacing .08em.
- `--font-serial`: `"Anek Devanagari"` at condensed width (wdth 75), 700, `tabular-nums`. Alternative: Teko for registration numbers. Mono faces lack ₹ [V-font].
- Google Fonts URL: `family=Mukta:wght@400;500;700;800&family=Baloo+2:wght@700;800&family=Kalam:wght@400;700&family=Anek+Devanagari:wdth,wght@75,700`.

**Radii:** card `6px` (paper, nearly square), inner rows `0`, buttons `12px`, chips and pills `999px`, bottom sheet `20px 20px 0 0`, stamp: circle with double ring.

**Shadows:**
- paper: `0 1px 0 rgba(27,36,51,.06), 0 8px 18px -8px rgba(27,36,51,.22)`;
- lifted/active card: `0 14px 28px -10px rgba(27,36,51,.28)`;
- sticky bar: `0 -6px 16px rgba(27,36,51,.10)`.

**Texture:**
- ruled rows: `repeating-linear-gradient(transparent 0 35px, var(--rule) 35px 36px)`;
- perforation: a `radial-gradient(circle at 6px 0, transparent 4px, var(--paper) 4.5px)` strip across the top;
- optional faint paper grain via a 2–3% SVG noise.

**Why this wins:**
- It looks like what both users already handle every day, so it fits "resemble the target audience" literally.
- It turns the abstract "SEALED" into a culturally obvious act (stamping).
- It works on a light, sunlight-friendly ground.
- It is cheap to build: one CSS file and SVG.

### Direction B: "Khatabook-clean" (fintech ledger)
- Light grey `#F4F6FA` bg, white cards, a royal-blue header `#0D47A1` (8.63:1 with white), red `#C62828` / green `#1B7F3B` (5.62 / 5.07 AA).
- Fonts: Noto Sans + Noto Sans Devanagari (UX4G-aligned, tabular by default).
- Radius 12px cards, 8px buttons. Shadow `0 1px 3px rgba(16,24,40,.08)`.
- Components: blue app bar, summary strip, red/green split sticky CTA, list rows with avatars.
- Pros: instantly "an app like Khatabook/OkCredit". Cons: generic. It does not express "parcha" or "sealed", and it looks like a ledger rather than a job slip.

### Direction C: "Workshop high-viz" (Rapido / safety signage)
- Pale yellow `#FFF6CC` bg or white, safety yellow `#FFC400` blocks with black `#111111` text (11.82 AAA), black bars (white on black 18.88), hazard orange `#C2410C` (5.18 AA), green `#15803D`.
- Fonts: Anek Devanagari (condensed) + Mukta. Radius 4px, thick 2px borders, black-and-yellow diagonal-stripe dividers.
- Pros: great in direct sun, very legible, feels like workshop signage. Cons: shouty for the vehicle owner. It suits the `/workshop` screen better than `/customer`. Yellow-black also reads "warning".
- **Hybrid option:** use C's high-viz yellow mic button and step indicator inside A's mechanic screen.

**Recommendation: A, with two hybrids:** Direction C's haldi high-viz mic and record button on `/workshop`, and Direction B's red/green semantics for amounts due and paid.

---

## 6. Component list (Direction A), with where each idea comes from

1. **Bill-book slip card**: paper, perforated top, ruled rows, `Sl. / Kaam (Particulars) / Qty / Rate / ₹` columns, double-underlined total, amount in words. *Origin: physical bill book.*
2. **Red serial number** `№ 000127` plus the date, top-right. *Origin: crash-numbered books.*
3. **Copy ribbon** "ORIGINAL – मालिक की प्रति" on white, "DUPLICATE – वर्कशॉप प्रति" on the pink tint. *Origin: carbon copies.*
4. **पक्का / SEALED rubber-stamp animation**: violet round seal, shop name on the rim, date and time in the centre, about -8° rotation, an ink-texture mask, thump sound and haptic. *Origin: rubber stamp + UPI sonic and haptic success.*
5. **Big-amount hero**: ₹ total in Mukta 800, 44px, tabular, lakh grouping, with "Kul anumaan / Estimate total" above. *Origin: UPI success, Khatabook summary.*
6. **Confirmation receipt block** (owner side): green tick in a filled circle, "Aapne call pe 'haan theek hai' kaha", time, call duration, a play button for the recording, and a transaction-style ID. *Origin: UPI "Paid to" plus soundbox voice confirmation.*
7. **Voice-note bubble**: round play button, waveform, duration, blue mic once heard; used for the mechanic's Hinglish recording and the call. *Origin: WhatsApp.*
8. **Hold-to-talk mic FAB**: 72px circle, haldi glow ring while recording, "slide to cancel". *Origin: WhatsApp + high-viz.*
9. **Sticky split CTA bar**:
   - owner: green "Haan, theek hai ✓" and outlined red "Badlaav chahiye ✎";
   - mechanic: blue "Call karke padho" and "WhatsApp bhejo".

   *Origin: Khatabook YOU GAVE / YOU GOT.*
10. **Status stepper**: Bola → Parcha → Call → Haan → पक्का, with the active step as a pulsing haldi dot. *Origin: Swiggy/Zomato tracking.*
11. **Chat-thread view of the job**: mechanic messages left, owner replies as `#D9FDD3`-style bubbles on the right. *Origin: GPay/Tez threads, WhatsApp.*
12. **WhatsApp share card**: preview of the slip, "Kaam ka Parcha Verified ✓" badge, link. *Origin: OkCredit/Khatabook reminders.*
13. **`/verify` result screen**: big green "Asli parcha ✓ – Signature valid" or red "Match nahi hua ✕", then the sealed slip to compare, plus the scan time; optional thin iridescent "hologram" border on success. *Origin: DigiLocker, Aadhaar QR, hologram labels.*
14. **Language toggle**: "हिं / En / Hinglish" pills, each written in its own script. *Origin: OkCredit language grid.*
15. **Vehicle plate chip**: `MH 12 AB 1234` in condensed Anek/Teko with a black border on white (a yellow plate for commercial vehicles). *Origin: Indian number plates.*
16. **Bottom sheet for corrections**: 20px top radius, grab handle, item rows with stepper ± and a ₹ field.

Ten to borrow first: 1, 2, 4, 5, 6, 7, 9, 10, 12, 13.

---

## 7. Sources
- PhonePe identity (Codesign): https://thehardcopy.co/phonepes-brand-identity-case-study/ ; PhonePe design-system story: https://tech.phonepe.com/the-tale-before-the-design-system/ ; PhonePe DESIGN.md (third-party): https://explainx.ai/designs/whyashthakker-design-md-templates-skills/phonepe/design-md
- Tez/GPay: https://increment.com/frontend/case-study-mobile-payments-in-india/ ; https://yourstory.com/2018/01/google-tez-interview ; https://en.wikipedia.org/wiki/Tez_(software)
- Khatabook: https://dribbble.com/khatabook ; https://brandfetch.com/khatabook.com ; https://khatabook.com/blog/khatabook-app-features/ ; khatabook.com bundle (V-css)
- OkCredit: okcredit.com CSS (V-css) ; https://yourstory.com/2021/03/product-roadmap-fintech-startup-okcredit-800-million-transactions
- Vyapar: https://brandfetch.com/vyaparapp.in ; https://commons.wikimedia.org/wiki/File:Vyapar_App_Logo.svg ; https://vyaparapp.in/bill-book-format/cash-memo
- Paytm: https://www.yellowslice.in/project/paytm ; https://thehardcopy.co/under-paytms-design-hood/ ; https://wittywit.com/paytm.html ; https://thehardcopy.co/paytm-uses-voice-to-reassure-small-businesses/ ; https://paytm.com/blog/payments/transformative-power-of-paytm-qr-and-soundbox-how-our-innovative-technology-is-helping-small-vendors-transition-to-mobile-payments/
- UPI screenshot scam / shopkeeper verification: https://scamshieldai.in/blog/case-study-fake-upi-payment-screenshot-scam
- Meesho: https://www.creativegaga.com/branding/rebranding/meeshos-makeover-from-humble-beginnings-to-vibrant-bazaar ; https://medium.com/meesho-tech/mesh-design-system-a-way-forward-for-design-at-meesho-873585b24956
- Swiggy: https://oppositehq.com/portfolio/swiggy-brand-identity-design/ ; https://www.brandcolorcode.com/swiggy ; Zomato: https://www.zomato.com/content_guidelines.pdf (timed out) ; https://www.brandcolorcode.com/zomato
- Rapido: https://medium.com/rapido-labs/building-rapidos-design-system-54a0e94bf5dc ; rapido.bike CSS (V-css)
- Urban Company: https://obviousinhindsight.substack.com/p/urban-company-design-system ; https://medium.com/uc-design/introducing-align-urban-companys-unified-design-system-f642bd149890 ; https://medium.com/uc-design/scaling-urban-companys-partner-app-to-handle-international-challenges-889a2973c15d
- GoMechanic: https://nh1design.com/project/gomechanic ; https://www.behance.net/gallery/61088047/GOMechanic-CR-App-Design-(UIUX) ; gomechanic.in CSS (V-css)
- Zepto: https://brandfetch.com/zeptonow.com (UNVERIFIED) ; BharatPe: https://brandfetch.com/bharatpe.com
- WhatsApp: https://codefronts.com/snippets/css-chat-bubbles/whatsapp-web-chat-bubble-css/ ; https://themeandcolor.com/blog/whatsapp-dark-mode-colors ; https://www.brandcolorcode.com/whatsapp ; https://www.androidpolice.com/whatsapp-plans-big-ui-redesign-what-it-looks-like/
- UX4G: https://www.ux4g.gov.in/foundations/color ; https://www.ux4g.gov.in/foundations/typography
- DigiLocker / Aadhaar: https://negd.gov.in/blog/digilocker-the-digital-briefcase-for-indias-authentic-e-documents/ ; https://pdfsigncheck.com/digilocker-pdf-signature-verification ; https://x.com/UIDAI/status/1948231707414442152 ; https://www.bankbazaar.com/aadhar-card/aadhaar-qr-code-scanner.html
- Bill books: https://shekhawatiprinters.in/printing-guides/ncr-bill-book-printing-guide ; https://www.shivanienterprises.com/blog/bill-book-printing/ ; https://dir.indiamart.com/impcat/bill-book-printing-services.html ; https://www.amazon.in/estimate-bill-book/s?k=estimate+bill+book ; https://www.amazon.in/Small-Writing-Original-Duplicate-Offices/dp/B0DVH6LFH3 ; https://www.billonline.in/blog/kirana-bill-format ; https://khatabook.com/blog/all-about-cash-memo/
- Job cards: https://www.scribd.com/document/735942763/JOB-CARD ; https://pdfcoffee.com/sample-auto-workshop-job-card-pdf-free.html
- Stamps: https://www.kokuyocamlin.com/camlin/office-supplies/stamp-pads-and-inks/rubber-stamp-inks ; https://www.flipkart.com/soni-officemate-stamp-pad-ink-500ml-violet-colour-pack-1-ink/p/itm00faa79af37c8 ; https://rubberstampwala.in/products/proprietorship-rubber-stamps
- Type: https://design.google/library/new-wave-indian-type-design ; https://github.com/EkType/Mukta ; https://github.com/itfoundry/hind ; https://github.com/itfoundry/Poppins/issues/42 ; https://tdc.org/winner/poppins-devanagari-branding/ ; https://github.com/google/fonts (files inspected)
- Play Store listings (screenshots inspected): Khatabook `com.vaibhavkalpe.android.khatabook`, OkCredit `in.okcredit.merchant`, Vyapar `in.android.vyapar`, PhonePe `com.phonepe.app`, PhonePe Business `com.phonepe.app.business`, Paytm `net.one97.paytm`, GPay `com.google.android.apps.nbu.paisa.user`, BharatPe `com.bharatpe.app`, UC Partner `com.urbanclap.provider`, WhatsApp `com.whatsapp`
