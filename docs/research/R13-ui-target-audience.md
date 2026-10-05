# Research D: Target audience for the Kaam ka Parcha UI

*Who the UI is for, what they're used to, and the design requirements that follow*

Prepared for: Kaam ka Parcha (काम का पर्चा), Gnani AI Great Indian AI Internship Challenge
Date: 2026-10-05
Scope: (1) ethnography of Indian garage mechanics, (2) "Bharat" / next-billion-user design guidelines, (3) what customers expect from an estimate, (4) Hindi/Hinglish UI copy.

## Confidence tags used throughout

| Tag | Meaning |
|---|---|
| **[V]** | Verified. I fetched and read the primary or official source (full text or the relevant section). |
| **[S]** | Secondary. Taken from a search-result snippet, an aggregator, or a vendor or marketing page. Probably right, but I did not confirm it against the original source. |
| **[U]** | Unverified, or my own inference. Treat it as a hypothesis to test in the field. |

A methodological caveat: I found **no peer-reviewed ethnography that studies Indian roadside garage mechanics specifically**. The mechanic persona below is put together from four kinds of source: labour-survey data for the motor-vehicle-repair industry (NIC 4520), HCI studies of "emergent" low-literacy smartphone users in North India, market and vendor sources on garages, and Indian consumer-dispute guidance. Section 7 lists what to check in the field.

---

## 1. Executive summary

- **The mechanic is typically educated to middle school, has no technical education, and learned the trade informally.** PLFS 2022-23 data on "maintenance and repair of motor vehicles" (NIC 4520) shows most workers were educated up to middle school, 93% had no technical education, and 60% had only non-formal vocational training. [V] ([NCAER Policy Brief, Oct 2025](https://ncaer.org/wp-content/uploads/2025/10/NCAER-Policy-Brief-Oct-2025.pdf))
- **Low-literacy Hindi-belt smartphone users already lean on voice.** In a 2021 study of 30 emergent users across Delhi, UP, Bihar, Rajasthan, Chhattisgarh and other states:
  - 28 of 30 preferred voice search.
  - 20 of 30 sent WhatsApp voice notes.
  - They spoke code-mixed Hindi and English.
  - Literate users checked the transcribed text before acting on it.
  - They typed instead of speaking when it was noisy.
  [V] ([Gupta, Mehta, Punj & Medhi Thies, COMPASS '22](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/05/compass22-34-taps.pdf))
- **Text interfaces fail this group, and a live operator works best.** Text UIs were "unusable" for first-time low-literacy users and error-prone for novice literate users. A live operator was up to 10 times more accurate. [S] ([Medhi et al., ACM TOCHI 2011](https://dl.acm.org/doi/10.1145/1959022.1959024)). This supports the "simulated phone call" idea for customers.
- **Numerals are the one piece of text that even non-literate users read.** In Medhi's Bangalore fieldwork, non-literate users "could easily recognize numerals", so numerals "can remain in the UI". [V] ([Medhi, Sagar & Toyama, ITID 2007](https://ocw.mit.edu/courses/mas-965-nextlab-i-designing-mobile-technologies-for-the-next-billion-users-fall-2008/8ccecb3eacd514b7ea0255f5158de907_MITMAS_965F08_medhi2007.pdf)). Make the ₹ amounts the visual hero of the screen.
- **India already trusts spoken confirmation.** Paytm, PhonePe and Google Pay soundboxes and in-app voice alerts announce "₹X received" aloud in Hindi. They exist because a screen on the customer's phone can be faked, and because shopkeepers are busy and their shops are noisy.
  - [V] [PhonePe press release, Dec 2020](https://www.phonepe.com/press/phonepe-launches-vernacular-voice-notifications-on-its-business-app/)
  - [V] [TechCrunch, Jan 2023](https://techcrunch.com/2023/01/17/google-pay-soundbox-india/)
  - [S] [Fake-screenshot guidance](https://www.indianpaycalculator.in/govt-news/fake-upi-payment-screenshot-scam-shopkeepers-verify-2026)
- **Customers have been primed for line-by-line approval through an SMS link.** Maruti's 2018 online job-card approval works like this:
  - An SMS link opens the job card.
  - Each extra part is listed with description, quantity and price, and can be approved or rejected individually.
  - The service centre can attach photos.
  - A revised estimate follows, then a confirmation call from the service advisor.
  [V] ([Rushlane](https://www.rushlane.com/maruti-customer-service-launch-new-system-12287133.html))
- **Hindi copy must be everyday Hindi, not shuddh (formal) Hindi.**
  - Duolingo found its Hindi UI "too hard for even native Hindi speakers" and switched some words to English. [V] ([Duolingo](https://blog.duolingo.com/language-learning-for-the-next-billion-duolingo-in-india/))
  - Meesho replaced literal translations with familiar words, because "users scan words, and only read words which they are familiar with". [V] ([Meesho Design](https://medium.com/meesho-tech/my-first-6-months-as-a-product-designer-at-meesho-90b7144c955b))
- **The phone is Android, roughly 360×800 CSS px, made by vivo, Oppo, Xiaomi, Samsung or realme, and used on a frequently slow or rationed connection.**
  - Android has 93.9% share in India; 360×800 is the top resolution at 15.3%. [V] (Statcounter, Sept 2026: [OS](https://gs.statcounter.com/os-market-share/mobile/india), [resolution](https://gs.statcounter.com/screen-resolution-stats/mobile/india), [vendor](https://gs.statcounter.com/vendor-market-share/mobile/india))
  - Users ration data and report voice search failing on slow internet. [V] ([COMPASS '22](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/05/compass22-34-taps.pdf))

---

## 2. Persona A: the mechanic or workshop owner ("Mistri ji")

### 2.1 The trade

- **Scale and informality.** One source describes India's independent service ecosystem as "nearly 200,000 garages". [S] ([autofintechs](https://autofintechs.com/automotive-aftermarket-garages-in-india-now-near-future-and-ever-after/)). Another says unorganised multi-brand workshops capture about 53% of car-service revenue. [S] ([Ken Research](https://www.kenresearch.com/industry-reports/india-multi-brand-car-service-market)). Both numbers are unaudited.
- **Industry voice.** AutocarPro calls the sector "highly fragmented", with "thousands of small, unorganised players". It says "most mechanics lack formal training and certification" and that "many customers feel apprehensive about being overcharged or not getting genuine parts". [V] ([AutocarPro](https://www.autocarpro.in/news/-transforming-indias-aftermarket-servicing-industry-121897))
- **How the skill is learned.** Barber's participant-observation study in northern India found that "observation, imitation, and copying" dominate how auto mechanics learn. This is the ustad–shagird (master–apprentice) pattern. [S] ([Barber 2004, Int. J. Training & Development](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-2419.2004.00202.x))
  - *Implication [U]:* mechanics learn by watching. A short demo, or a first-run "watch me do it" animation, will teach better than written instructions. Medhi's "full-context video" work supports this: video "dramatically improved task completion" for non-literate users. [S] ([Medhi & Toyama, ICTD 2007](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/ictd2007_medhi_toyama.pdf))
- **One person does everything.** In an independent garage, "a single individual may simultaneously oversee customer interactions, procurement, billing, operations, and issue resolution". The same source says "every additional screen, manual entry, approval step, or navigation requirement introduces friction". [V] ([Hello Entrepreneurs](https://helloentrepreneurs.com/corporate/insight/why-digitising-the-garage-is-harder-than-digitising-the-enterprise-97606/))

### 2.2 Education, literacy and vision

| Data point | Value | Tag and source |
|---|---|---|
| General education of NIC 4520 workers (PLFS 2022-23) | Most educated up to middle school | [V] [NCAER](https://ncaer.org/wp-content/uploads/2025/10/NCAER-Policy-Brief-Oct-2025.pdf) |
| NIC 4520 workers with no technical education | 93% | [V] same |
| NIC 4520 workers with non-formal vocational training | 60% | [V] same |
| NIC 4520 skill level | "Low-medium skilled" | [V] same |
| India literacy, age 7+ (PLFS 2023-24) | 80.9% overall; men 87.2%; Bihar 74.3%; UP 78.2% | [S] [class24](https://www.class24.study/current-affairs/india-literacy-rate-plfs-2024), [induqin](https://www.induqin.com/post/india-s-literacy-landscape-insights-from-the-plfs-2023-24-report) |
| Ages 14–18 who cannot read Class-2 text fluently in their regional language (ASER 2023) | 25% | [V] [Careers360](https://news.careers360.com/over-86-8-percent-in-14-18-age-group-enrolled-25-cent-of-them-cant-read-class-2-text-fluently-aser) |
| Class 8 government-school pupils who can read Class-2 text (ASER 2024) | 67.5% | [S] [dtnext / ASER 2024 coverage](https://www.dtnext.in/news/tamilnadu/reading-ability-in-primary-classes-abysmal-says-aser-2024-report-820957) |
| Adults 15+ who can send or receive email (CAMS 2022-23) | 43.4% | [V] [ThePrint](https://theprint.in/india/50-of-indias-internet-users-dont-know-how-to-send-email-a-third-know-online-banking-govt-survey/2308129/) |
| Adults 15+ who can operate a mobile phone (CAMS 2022-23) | 86.5% | [V] same |
| Ages 15–24 who can send messages with attachments (NSS 78th round) | 78.4% | [S] [Business Standard](https://www.business-standard.com/india-news/over-82-of-rural-youth-able-to-use-internet-in-india-says-govt-survey-124100901062_1.html) |
| Presbyopia prevalence, age 35+, rural Haryana | 42.9% | [S] [JFMPC](https://www.ovid.com/jnls/jfmpc/fulltext/10.4103/jfmpc.jfmpc_1148_21~prevalence-of-presbyopia-spectacles-coverage-and-barriers) |
| Near-vision impairment, Telangana, age 40+ | 55.8% | [S] [IJO](https://www.ovid.com/jnls/ijo/fulltext/10.4103/ijo.ijo_1235_18~prevalence-of-refractive-errors-uncorrected-refractive-error) |

**Reading of the data.** Assume the owner (often 35–55 [U]) can read numbers and short familiar Hindi words, may need reading glasses he isn't wearing, and types slowly or not at all.

Gupta et al. report the following about emergent users [V] ([COMPASS '22](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/05/compass22-34-taps.pdf)):
- They "often type slowly and are not comfortable with spellings".
- They "feared damaging their devices unknowingly".
- Low-literate users "displayed hesitancy to use anything apart from what they have been told".
- 23 of 30 depended on an intermediary, such as a child or a "bhaisaab", to set up apps.

### 2.3 The phone

| Attribute | Data | Tag and source |
|---|---|---|
| OS | Android 93.89%, iOS 6.05% (India, Sept 2026) | [V] [Statcounter OS](https://gs.statcounter.com/os-market-share/mobile/india) |
| Vendor (web-traffic share) | vivo 21.3%, Oppo 15.1%, Xiaomi 14.8%, Samsung 12.4%, realme 8.9%, Motorola 6.5% | [V] [Statcounter vendor](https://gs.statcounter.com/vendor-market-share/mobile/india) |
| Viewport | 360×800 is #1 at 15.28%; next are 393×873 (6.6%) and 384×832 (4.2%) | [V] [Statcounter resolution](https://gs.statcounter.com/screen-resolution-stats/mobile/india) |
| Android version | Android 16 at 38.8%, 15 at 19.9%, 13 at 10.1%, 14 at 10.0%, 12 at 7.2%, 11 at 6.8% | [V] [Statcounter](https://gs.statcounter.com/android-version-market-share/mobile-tablet/india). Caveat [U]: Chrome's reduced user-agent string can distort version stats, and budget phones skew older. |
| Entry level | The sub-US$100 segment grew 35.3% YoY in 2025; Xiaomi, realme and vivo hold over 50% of it | [S] (IDC via [BusinessToday](https://www.businesstoday.in/technology/news/story/india-smartphone-shipments-drop-7-in-q1-2025-vivo-and-apple-lead-growth-as-xiaomi-slumps-474928-2025-05-06) and [IDC](https://my.idc.com/getdoc.jsp?containerId=prAP53921425)) |
| Data | India has "among the most affordable data plans in the world, at USD 0.21/GB", yet users ration data. They turn on data only to send things, borrow hotspots (10 of 30), and say voice search "does not work in case of slow internet". | [V] [COMPASS '22](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/05/compass22-34-taps.pdf) |
| Device sharing | 22 of 30 shared phones with family; everyone knew the pattern lock | [V] same |

### 2.4 Apps and communication habits

- **WhatsApp is the internet.**
  - India had 530 million WhatsApp users per the government in Feb 2021. [S] ([Entrackr](https://entrackr.com/2021/02/govt-says-whatsapp-has-530-mn-users-in-india/))
  - An MSME survey found 97% use WhatsApp or WhatsApp Business. [S] ([Entrepreneur India](https://india.entrepreneur.com/news-and-trends/whatsapp-and-whatsapp-business-dominate-msme-landscape-with/476232))
  - All 30 emergent users in the COMPASS study used WhatsApp. Several found Facebook "overwhelming" compared with it. [V]
  - Google Design's emerging-markets research says "social media is the internet" for many users. [V] ([Google Design](https://design.google/library/connectivity-culture-and-credit))
- **Voice notes are normal.**
  - WhatsApp users send about 7 billion voice messages a day worldwide. [V] ([TechCrunch 2022](https://techcrunch.com/2022/03/30/people-are-sending-7-billion-voice-messages-on-whatsapp-every-day))
  - The claim that 22% of Indian WhatsApp communication is voice notes comes only from an aggregator. [U] ([hyperleap](https://hyperleap.ai/blog/whatsapp-statistics-india-2026))
  - In COMPASS, voice messages were used "by non-literate users, and by low-literate users when they were in a hurry, required to type something longer, or to communicate in their local dialect". One participant added: "if there are people around or chances of noise, then I type and send". [V]
- **YouTube is used for learning and entertainment.** It was used by all 30 participants, often as a "virtual mediator" for learning (10 of 30). [V] (COMPASS '22). Hindi mechanic channels exist with large audiences, for example "Bike Point" with about 1.26M subscribers. [S] ([tyremarket](https://www.tyremarket.com/roadtales/top-10-automotive-youtubers-in-india/), [Mechanic India](https://www.youtube.com/@mechanicindia1))
- **UPI apps set the bar for ease of use.** Participants found "Google Pay and Phone Pe the easiest to use". [V] (COMPASS '22). PhonePe for Business had 15 million merchant partners in Dec 2020. [V] ([PhonePe](https://www.phonepe.com/press/phonepe-launches-vernacular-voice-notifications-on-its-business-app/))
- **Soundbox and voice-alert culture.**
  - PhonePe's Hindi and other voice alerts let merchants confirm payment without "check[ing] the customer's phone screen, or waiting for a bank SMS". [V] ([PhonePe](https://www.phonepe.com/press/phonepe-launches-vernacular-voice-notifications-on-its-business-app/))
  - Google said voice alerts help "multitasking shopkeepers and assistants". Paytm had distributed "more than 5.8 million devices" by early 2023. [V] ([TechCrunch](https://techcrunch.com/2023/01/17/google-pay-soundbox-india/))
  - A later report gives "over 8 million" Paytm soundboxes, a 73% drop in disputes and 3x retention. [U] ([India Fintech substack](https://indiafintech.substack.com/p/the-soundbox-economy-episode-62))
- **Ledger and billing apps.**
  - Khatabook kept the bahi-khata notebook look in its early UI so adoption "feel[s] like an upgrade rather than a replacement". [S] ([markhub24](https://www.markhub24.com/post/khatabook-s-digital-ledger-adoption-strategy-for-small-businesses), [ameya substack](https://ameya.substack.com/p/how-khatabook-became-the-premier))
  - OkCredit and Khatabook use ledger words like "jama/udhaar" rather than banking jargon. [S]
  - Vyapar and similar apps share invoices as PDF on WhatsApp. [S] ([Vyapar](https://vyaparapp.in/blog/vyapar-app-features/))

### 2.5 How estimates and job cards are done today

- **Paper slips, registers and verbal quotes.** Vendor pages describe the status quo [S, vendor]:
  - "Paper job cards, handwritten registers, and Excel sheets". [S] ([GarageSaarthi job card](https://www.garagesaarthi.com/solutions/garage-job-card-software/))
  - Advisors writing "repair instructions on paper slips", leading to "lost vehicle details, forgotten complaints, and manual calculation errors". [S] (same)
  - "Paper bills prone to getting lost or damaged" and "hours wasted waiting for clients to answer phone calls" for approvals. [S] ([GarageSaarthi automation](https://garagesaarthi.com/features/automation/))
  - "WhatsApp overload", where numbers, photos and voice notes get mixed together. [S] (garage-software marketing seen in search results; [Mechanic Mate](https://play.google.com/store/apps/details?id=com.mfinityinfotech.mechanicmate))
- **Kacha bill vs pakka bill.** A *kacha bill* is a handwritten or temporary slip with no tax record. A *pakka bill* is a proper invoice recorded in the books, with GST. Customers often prefer kacha bills to avoid the tax, and vendors go along. [S] ([mapsofindia](https://www.mapsofindia.com/my-india/government/can-gst-bill-really-kill-the-kachcha-bill-system), [taxreturnwala](https://www.taxreturnwala.com/will-gst-help-curbing-black-money/))
  - *Implication [U]:* do **not** call the sealed card a "पक्का बिल" unless it is a GST tax invoice. Call it "मंज़ूर एस्टीमेट" / "मंज़ूर पर्चा" (approved estimate / approved slip).
- **Existing garage software converges on WhatsApp plus a PDF.** Autorox ("1200 garages, 20+ cities", Hindi and other Indian languages), GaragePro ("English and हिन्दी", WhatsApp built in) and Mechanic Mate (Hindi, PDF estimates to WhatsApp) all do this. [S] ([Autorox Play](https://play.google.com/store/apps/details?id=apps.autorox.co&hl=en_US), [GaragePro](https://garagepro.me/), [Mechanic Mate](https://play.google.com/store/apps/details?id=com.mfinityinfotech.mechanicmate&hl=en_US)). None that I found is voice-first. [U]
- **Why adoption fails.** Owners are not digitally illiterate, they are convenience-driven: "If my phone, the apps on it… can achieve something in a second, why would I be motivated to use a different business application?" [V] ([Hello Entrepreneurs](https://helloentrepreneurs.com/corporate/insight/why-digitising-the-garage-is-harder-than-digitising-the-enterprise-97606/))

### 2.6 Common disputes

From consumer-rights guides, which are secondary and whose legal citations I have not checked against statute [S/U]:
- **Verbal estimate, inflated bill.** "You were told 'about Rs 1,800'. You came back to a Rs 4,650 invoice because 'the chain sprocket was worn'". The guide says unagreed upward variation is an unfair trade practice under §2(47) of the Consumer Protection Act 2019. It also says written approval "(call recording, WhatsApp, signed revision)" is needed before fitting extra parts. [S] ([RTI Wiki, bikes](https://righttoinformation.wiki/bike-service-refund-re-repair-rights-india))
- **Minimum documentation.** The same guide says a cash memo is due on demand even from unregistered mechanics, and that a tax invoice is required above ₹200 from a registered provider. It lists the job-card fields a customer should get: the rider's complaint in their own words, odometer, fuel level, parts proposed, estimated labour, estimated total, and a signature on the estimate. [S]
- **Car-side patterns.** Unapproved parts, duplicate labour lines, oil quantity inflation ("bills 5 litres for a car that takes 3.5 litres") and vague "consumables ₹300 to ₹1,500". Also: "An oral one line 'ok' without an itemised written estimate does not amount to informed consent". [S] ([RTI Wiki, cars](https://righttoinformation.wiki/car-service-overcharging-unapproved-parts-india))
- **Hindi auto press says the same.** Readers are told to compare the "जॉब कार्ड और फाइनल बिल" because "कई बार डबल चार्ज लगा दिए जाते हैं" (double charges are often added), and to "पहले एस्टीमेट मांगें" (ask for an estimate first). [S] ([News24 Hindi](https://hindi.news24online.com/auto/car-service-scam-at-service-center-aware-and-avoid-these-things/833660/), [News24 Hindi 2](https://hindi.news24online.com/auto/car-service-scams-keep-in-mind-these-points-and-save-your-money-and-time/972268/))

**Design takeaway [U].** The sealed parcha (slip) is the mechanic's protection as much as the customer's. It should record every line, the time of approval, and the fact that approval was given by voice. That turns a verbal "theek hai" into the kind of written or WhatsApp approval these guides recommend.

### 2.7 Physical environment

- **Noise.**
  - An Indian occupational study (2021–22) measured 81–90 dBA in automobile industries and found noise-induced hearing loss in 55.1% of the automobile workers sampled (n = 29). [S] ([PMC11569067](https://pmc.ncbi.nlm.nih.gov/articles/PMC11569067/); the full text was behind a CAPTCHA, so these figures come from the indexed abstract)
  - In auto repair shops, air guns, wrenches and cut-off wheels mostly exceed 90 dBA. [S] ([Exposure Assessment in Auto Collision Repair Shops](https://www.researchgate.net/publication/51208255_Exposure_Assessment_in_Auto_Collision_Repair_Shops))
  - Technicians average about 86 dBA over a shift. [S] ([Ann. Work Expo. Health, tire-changing facilities](https://academic.oup.com/annweh/article/65/8/930/6316228))
  - *Implications [U]:*
    - Never rely on audio alone for the mechanic. Show text, haptics and a large visual state as well.
    - Assume speech recognition will make mistakes in noise. Show an editable transcript, as COMPASS users already do when they "verify the voice output (displayed in text format)". [V]
    - Prompt the mechanic to bring the phone close to his mouth, and use hold-to-talk or tap-to-start with a visible level meter.
    - Gnani's own Hindi TTS guidance warns that voices degrade at 8 kHz telephony quality. [V] ([Gnani blog](https://www.gnani.ai/resources/blogs/best-text-to-speech-hindi-tools-in-2026-gnani-ai-google-translate-alternatives))
- **Grease, wet or dirty fingers, gloves.** Capacitive screens cannot reliably tell fingers from conductive contaminants such as water, and wet fingers cause phantom or missed touches. [S] ([RainCheck, Goel et al.](https://mynkgoel.github.io/pdfs/raincheck.pdf)). See §4.6 for target sizes.
- **Sunlight.**
  - Under strong ambient light, screen reflectance dominates: "traditional contrast ratios measured in darkness are… irrelevant", and the high-ambient contrast rating "var[ies] by more than 3-to-1" across devices. [V] ([DisplayMate](https://www.displaymate.com/Smartphone_Brightness_ShootOut_1.htm))
  - A budget LCD under direct sun can fall below 2:1 effective contrast. [S] (search-result summary of DisplayMate data)

---

## 3. Persona B: the vehicle owner (customer)

### 3.1 Mindset: low trust and fear of overcharging

- Customers worry about "being overcharged or not getting genuine parts". [V] ([AutocarPro](https://www.autocarpro.in/news/-transforming-indias-aftermarket-servicing-industry-121897))
- Maruti built its approval system because customers were unsure "what parts are replaced, their actual costs and whether these are always a necessary replacement", and because final bills ran above estimates. [V] ([Rushlane](https://www.rushlane.com/maruti-customer-service-launch-new-system-12287133.html))
- The customer may also be a Bharat user. About 70% of Indian users consider local-language content more reliable than English, and nearly 9 in 10 new internet users are not proficient in English. [S] ([KPMG–Google 2017](https://assets.kpmg.com/content/dam/kpmg/in/pdf/2017/04/Indian-languages-Defining-Indias-Internet.pdf), [Quartz](https://qz.com/india/972844/indias-internet-users-have-more-faith-in-content-thats-not-in-english-study-says))
- **Fear of links.** A COMPASS participant uninstalled Paytm after "someone asked me for a link, which I had given. I suffered some loss". [V]. *Implication [U]:* the WhatsApp message must name the garage and the vehicle, say in Hindi what the link does, and the page must never ask for an OTP, PIN or payment on the approval step.

### 3.2 Precedents that shape customer expectations

| Precedent | What the customer sees | Tag and source |
|---|---|---|
| **Maruti online job-card approval (Nov 2018)** | SMS link; log in with mobile number; vehicle and number; part description, quantity, price; **approve or reject each part separately**; optional photos; revised estimate; confirmation call from service advisor | [V] [Rushlane](https://www.rushlane.com/maruti-customer-service-launch-new-system-12287133.html) |
| **Hero MotoCorp on WhatsApp (Apr 2021)** | Service booking, **real-time repair status**, self job-card, **digital invoice copy**, feedback, all in a menu-driven WhatsApp chat | [V] [AutocarPro](https://www.autocarpro.in/news-national/hero-motocorp-introduces-sales-and-aftersales-services-on-whatsapp-78958) |
| **GoMechanic** | Work starts "only after the approval of the customer"; itemised pricing; WhatsApp channel | [S] [GoMechanic FAQ](https://gomechanic.in/faq) |
| **Garage SaaS (GarageSaarthi and others)** | Itemised estimate on WhatsApp with damage photos and one-click approval. Vendor claim: "80% faster" approvals, "95%+ read rate" | [S, vendor] [GarageSaarthi](https://garagesaarthi.com/features/automation/) |
| **Photos of worn parts** | A vendor claims a photo with the estimate "converts far better than a phone call asking for permission" | [S, vendor] [HelloGrowthCRM](https://hellogrowthcrm.com/whatsapp-crm-for-automotive) |

### 3.3 Trust-screen conventions customers already know

- **UPI success screen.** Large amount, payee name, date and time, transaction ID / UPI reference number, a share-receipt button, and a success animation with sound. [S] ([Paytm receipt help](https://paytm.com/support/upi/how-to-get-upi-transaction-receipt-on-paytm), [Cashfree on fake apps copying "brand colors… and even notification sounds"](https://www.cashfree.com/blog/spot-fake-upi-payment-app-scams/))
  - *Why it builds trust:* "green checkmarks, brand logos and success messages trigger automatic trust". [S]
  - *Why that isn't enough:* the same visual trust is exploited by fake screenshots. Advice to shopkeepers: "The customer's screen is not proof… Only money in your account is proof", so turn on audible alerts. [V] ([indianpaycalculator](https://www.indianpaycalculator.in/govt-news/fake-upi-payment-screenshot-scam-shopkeepers-verify-2026))
  - *Implication [U]:* the "sealed" state should be verifiable, not just pretty. It needs a unique parcha number, a server timestamp and a live link that re-opens the record. The mechanic's phone should also get its own audible "मंज़ूर" announcement, soundbox-style, rather than relying on a screenshot from the customer.
- **Order tracking and ETA (Swiggy).** Swiggy shows "order confirmation instantly", live tracking and a visible cancel window, which "reduces anxiety". Sudden ETA jumps "create anxiety and erode confidence". [S] ([Upraised](https://www.upraised.co/blog/swiggy-order-tracking/), [markhub24](https://www.markhub24.com/post/when-every-minute-is-a-brand-promise-swiggy-s-delivery-time-prediction-algorithm))
  - *Implication [U]:* show "गाड़ी कब मिलेगी" (when will I get my vehicle) as a first-class field, and avoid silently moving it.
- **Show the work (operational transparency).** Buell & Norton found that people value a service more when they can see the effort behind it, sometimes even preferring a longer wait. [S] ([HBS, *The Labor Illusion*](https://www.hbs.edu/faculty/Pages/item.aspx?num=40158))
  - *Implication [U]:* each line should say what was done or found ("चेन ढीली थी → चेन-स्प्रॉकेट बदला"), not just "Part ₹850".
- **WhatsApp link previews.** WhatsApp reads `og:title`, `og:description` and `og:image`. Recommended image is 1200×630 px, at least 200×200, and **under about 300 KB**. A larger image silently gives no preview. [S] ([ogpreview](https://ogpreview.app/open-graph/whatsapp), [opengraph.to](https://www.opengraph.to/articles/og-image-too-large))
  - *Implication [U]:* render a per-parcha OG image showing garage name, vehicle number and **total ₹**, with a Hindi title such as "Sharma Auto: आपकी गाड़ी का पर्चा, ₹1,850".

---

## 4. Design guidelines for Bharat / next-billion users (with evidence)

### 4.1 Voice first, with redundant modes

- Medhi's text-free UI principles: "liberal use of graphics and photographs… and voice for providing information normally provided via text", "voice feedback… zealously applied", a consistent help icon, and numbers kept as text. First exposure to voice in their own language made users "thrilled" and "eager to explore". [V] ([ITID 2007](https://ocw.mit.edu/courses/mas-965-nextlab-i-designing-mobile-technologies-for-the-next-billion-users-fall-2008/8ccecb3eacd514b7ea0255f5158de907_MITMAS_965F08_medhi2007.pdf))
- Text UIs were unusable for first-time low-literacy users, and a live operator was up to 10 times more accurate. [S] ([TOCHI 2011](https://dl.acm.org/doi/10.1145/1959022.1959024))
- Users want to check what was heard: "a few low-literate users reported verifying the voice output (displayed in text format)". They asked for voice autocomplete. Authors recommend "validation checks for voice-based input". [V] ([COMPASS '22](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/05/compass22-34-taps.pdf))
- Users speak code-mixed Hindi, saying "certain words in English (instead of Hindi) so that the system could understand". [V] (same)

### 4.2 Language and copy register

- **Use familiar words over correct ones.**
  - Duolingo's "मणि" (gem) confused users, who said "coin"/"diamond". Swapping in English words during onboarding gave about a 1% completion gain. [V] ([Duolingo](https://blog.duolingo.com/language-learning-for-the-next-billion-duolingo-in-india/))
  - Meesho changed "प्रोडक्ट विवरण" to "प्रोडक्ट की जानकारी" and "समान प्रोडक्ट्स" to "मिलते-जुलते प्रोडक्ट्स". [V] ([Meesho](https://medium.com/meesho-tech/my-first-6-months-as-a-product-designer-at-meesho-90b7144c955b)). It also chose "zaroori" over "anivarya" for "required". [S] ([BW Disrupt via search](https://www.bwdisrupt.com/article/meesho-adds-8-new-vernacular-languages-strengthens-regional-foothold-441680))
- **English loanwords are now Hindi.** "Terminologies (in English) have become part of the user's vocabulary and a preference as opposed to elaborate local translation" (examples: 'network', 'hotspot', 'share'). [V] ([COMPASS '22](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/05/compass22-34-taps.pdf)). Hindi auto journalism writes the service vocabulary as English words in Devanagari: जॉब कार्ड, बिल, एस्टीमेट, पार्ट्स, लेबर चार्ज, सर्विस. [S] ([News24 Hindi](https://hindi.news24online.com/auto/car-service-scam-at-service-center-aware-and-avoid-these-things/833660/))
- **Formal Hindi backfires.** Think with Google gives the example "जानें कि प्रीमियम कितना होगा" vs the formal "प्रीमियम का कोट पाएँ" and recommends avoiding direct translation. [S] (search snippet; the original page now redirects: [Think with Google](https://www.thinkwithgoogle.com/intl/en-apac/future-of-marketing/creativity/app-website-localization-indian-users/))
- **Pair icons with words.** NBU guidance: "pair culture-oriented iconography with text" and keep fixed screen positions for positive actions such as Save or Submit. [S] ([Shopify NBU summary](https://www.shopify.com/partners/blog/next-billion-users), [uxspot](https://uxspot.io/nbu/)). Low-literacy users rely on "symbolic and visual literacy". [V] ([Google Design](https://design.google/library/connectivity-culture-and-credit))

### 4.3 Script: Devanagari for reading, Roman typing tolerated

- **Typing:** a 2014 study of code-mixed social media found **93.17%** of native Hindi speakers' posts were in Roman script and only 2.93% in Devanagari. Hinglish-preferring users rose from 44.9% to 56.3% after 2020. [S] (via search; [Nature HSSC 2024](https://www.nature.com/articles/s41599-024-03058-6))
- **Reading:** Romanised Hindi ("Romanagari") is slower to recognise than Hindi in Devanagari or English in Roman script, and imposes "an additional cognitive demand". [S] ([Nature India 2013](https://www.nature.com/articles/nindia.2013.23), [Reading & Writing 2021](https://link.springer.com/article/10.1007/s11145-021-10241-7))
- **Conclusion [U, inference]:** for *display* labels use Devanagari Hindi with loanwords, plus an optional small Roman/English secondary line. For *any text input*, accept Roman Hinglish and Devanagari, and prefer voice. I found **no direct A/B evidence** on Hindi-primary vs English-primary bilingual labels for mechanics. The recommendation rests on the reading-speed evidence, the KPMG trust stat, Duolingo/Meesho/COMPASS on loanwords, and the fact that Hindi-medium schooling teaches Devanagari. Validate in the field.

### 4.4 Numbers and money

- **Use international digits (0–9), not Devanagari digits (०–९).** The Constitution (Art. 343) prescribes "the international form of Indian numerals" for official Union purposes. [S] ([constitutionofindia.net](https://www.constitutionofindia.net/articles/article-343-official-language-of-the-union/)). Non-literate users recognise these digits. [V] (Medhi 2007)
- **Indian grouping.** "1,00,000" uses the 2-2-3 convention, and ₹1,50,000 is said as "1.5 lakh". [V] ([Wikipedia: Lakh](https://en.wikipedia.org/wiki/Lakh)). `new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR'})` gives "₹12,34,567.89". [S] ([W3C i18n](https://www.w3.org/International/questions/qa-number-format), [MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat))
- **Speaking amounts.**
  - Hindi number words 1–99 are almost all irregular and have to be memorised individually. [V] ([Wikipedia: Hindustani numerals](https://en.wikipedia.org/wiki/Hindustani_numerals))
  - "The lakh and crore system does not map onto a generic number handler". Code-mixed sentences such as "Aapka payment due date 15th hai" are the norm, and schwa deletion errors are "the single most tell[ing sign] of a weak Hindi voice". [V] ([Gnani TTS guide](https://www.gnani.ai/resources/blogs/best-text-to-speech-hindi-tools-in-2026-gnani-ai-google-translate-alternatives))
  - *Implication [U]:* normalise amounts to words before TTS (for example "एक हज़ार आठ सौ पचास रुपये"). Always show the digits on screen while they are being read out.

### 4.5 Devanagari typography

- **Material Design guidance for "tall" scripts (Hindi):**
  - Font size **+1px** over English for Title through Caption styles.
  - Line height **+0.1em**.
  - "Use Regular weight… avoiding Bold… native speakers [said] Bold is too heavy" (this refers to Noto).
  [V] ([Material v1 typography](https://m1.material.io/style/typography.html))
- **Alphabettes:**
  - Match Devanagari's headline mass (shirorekha to baseline) to the Latin x-height.
  - Devanagari "may require additional line spacing".
  - Avoid tracking, which breaks the shirorekha.
  - Use ragged-right text, not justified.
  [V] ([Alphabettes](https://www.alphabettes.org/devanagari-typography-101-a-guide-for-typesetting-with-latin/))
- **Weight.** Devanagari letters "lose their distinct features and blur together" as they get heavier. [V] ([Google Design](https://design.google/library/new-wave-indian-type-design)). Use Medium or SemiBold for emphasis, and keep Black weights for large numerals only. [U]
- **Practical values.** Body text at 1.25rem (20px) and line-height 1.6 are reported recommendations, and Marathi sites use 1.7. [S] (search snippets). Combined with presbyopia and sunlight: **body 18–20px, line-height 1.5–1.7, amounts 28–40px**. [U]
- **Font candidates (all on Google Fonts, OFL licence):**

| Font | Character | Use in Kaam ka Parcha | Tag and source |
|---|---|---|---|
| **Mukta** (Ek Type) | Humanist, mono-linear; 7 weights; Devanagari and Latin; used by Dainik Jagran and Lokmat online | Primary UI face. It matches what Hindi newspaper readers already see. | [V] [Google Design](https://design.google/library/new-wave-indian-type-design), [GitHub](https://github.com/EkType/Mukta) |
| **Hind** (Indian Type Foundry) | "Developed explicitly for… User Interface design"; 5 weights; large x-height, open apertures | Alternative primary UI face | [S] [Google Fonts](https://fonts.google.com/specimen/Hind) |
| **Baloo 2** (Ek Type) | Soft, rounded display face; 5 weights | Friendly headings or brand, used sparingly | [S] [Ek Type](https://ektype.in/baloo-family.html) |
| **Noto Sans Devanagari** | 9 weights; variable width and weight | Safe fallback | [S] [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari) |
| **Tiro Devanagari Hindi** | Serif, 1 weight, northern style, from the Murty Classical Library | "Printed slip" header or seal text only | [S] [Fontsource](https://fontsource.org/fonts/tiro-devanagari-hindi) |

- **Performance [U].** Load at most 2 weights, use `font-display: swap`, and rely on Google Fonts' `unicode-range` subsetting so Latin-only screens don't download Devanagari.

### 4.6 Touch targets for greasy or gloved hands

| Standard or study | Minimum | Tag and source |
|---|---|---|
| WCAG 2.2 SC 2.5.8 (AA) | 24×24 CSS px or enough spacing | [S] [TetraLogical](https://tetralogical.com/blog/2022/12/20/foundations-target-size/) |
| WCAG 2.5.5 (AAA), Apple HIG | 44×44 | [S] same |
| Material Design | 48×48 dp (about 9 mm) | [S] [Material accessibility](https://m1.material.io/usability/accessibility.html) |
| Parhi, Karlson & Bederson 2006 (thumb, one-handed) | 9.2 mm discrete, 9.6 mm serial | [S] [MSR PDF](https://www.microsoft.com/en-us/research/wp-content/uploads/2006/01/parhi-mobileHCI06.pdf) |
| NN/g | "at least 1cm × 1cm"; larger for gloves and use on the move; fingertips are 1.6–2 cm wide | [V] [NN/g](https://www.nngroup.com/articles/touch-target-size/) |
| MIL-STD-1472 (as cited) | 15 mm square bare-hand, about 20 mm gloved, 3 mm gaps | [S/U] [Springer chapter](https://link.springer.com/chapter/10.1007/978-3-319-40406-6_7) |

On Android, 1 CSS px ≈ 1 dp ≈ 1/160 inch, so 1 mm ≈ 6.3 CSS px (approximate; it varies by device). That gives:
- **1 cm ≈ 63 px**
- **15 mm ≈ 95 px**
- **20 mm ≈ 126 px**

**Recommendation [U]:**
- Every tappable element: at least 48 px, with at least 8 px gaps.
- Every primary action: at least 64 px tall and full width (meets NN/g's 1 cm).
- The mic, "हाँ, ठीक है" (yes, OK) and "बदलो" (change): at least 88–96 px (about MIL-STD's 15 mm).
- No swipe-only, long-press-only or double-tap-only interactions, because wet or greasy fingers cause phantom and missed touches. [S] ([RainCheck](https://mynkgoel.github.io/pdfs/raincheck.pdf))

### 4.7 Theme: sunlight and contrast

- In users with normal vision, "light mode leads to better performance most of the time" (pupil constriction, more depth of field). In bright daytime conditions, Dobres et al. found no significant polarity effect. [V] ([NN/g](https://www.nngroup.com/articles/dark-mode/))
- Outdoors, reflectance dominates, so the content itself must have very high contrast. [V] ([DisplayMate](https://www.displaymate.com/Smartphone_Brightness_ShootOut_1.htm)). WCAG AAA 1.4.6 asks for 7:1 and notes the benefit for "glare, bright sunlight… older devices". [S] ([W3C](https://w3c.github.io/wcag/understanding/contrast-enhanced.html))
- Khatabook's success with a notebook look supports a **paper-slip** visual metaphor. [S] ([markhub24](https://www.markhub24.com/post/khatabook-s-digital-ledger-adoption-strategy-for-small-businesses))
- **Recommendation [U]:**
  - Light "paper" theme: warm off-white background, near-black ink text, at least 7:1 contrast for body text.
  - No light-grey secondary text below 4.5:1.
  - No thin weights.
  - Dark mode optional, never the default.

### 4.8 Colour semantics

- **Red is not simply "danger" in India.** The bahi-khata ledger is "covered in the auspicious colour red for good luck", which is why India's Finance Minister carries a red bahi-khata on Budget day. [S] ([NewsBytes](https://www.newsbytesapp.com/news/business/what-is-bahi-khata-the-red-ledger-sitharaman-carries-during-budget/story), [Asia InCH](https://asiainch.org/craft/bahi-clothbound-books-of-rajasthan/)). Saffron is sacred and yellow is auspicious. [S] ([Study.com](https://study.com/academy/lesson/colors-in-indian-culture.html))
- **Payments have their own convention.** UPI apps make green ticks the success signal. [S] ([Cashfree](https://www.cashfree.com/blog/spot-fake-upi-payment-app-scams/))
- **Colour must match real-world meaning.** Medhi's users rejected yellow roads because "roads can never be yellow". [V] (Medhi 2007)
- **Recommendation [U]:**
  - Green = हाँ / मंज़ूर / sealed.
  - Amber or turmeric = "check this" (fields flagged for the mechanic) and "बदलो" (change). A change is a correction, not a rejection, so it should not be red.
  - Red only for errors and delete.
  - A deep maroon or sindoor-red brand header for the parcha is culturally positive (ledger association).
  - Never use colour alone; always pair it with an icon and a word.

### 4.9 Trust signals

- **Rubber stamps.** Stamps invest paper with "qualities that render them visible to the state and valuable to the individual", and spread to "small traders" by the interwar years. [V] ([Mukharji, UPenn](https://web.sas.upenn.edu/mukharji/2021/01/02/the-art-of-rubber-stamps/)). A company stamp next to a live signature is still common in Indian business practice. [S] ([Legistify](https://legistify.com/blogs/wet-typed-stamped-digital-signatures/))
- **Reassurance copy.** Google Station's research led to the line "Your number is safe with us" before asking for a phone number. [V] ([Google Design](https://design.google/library/connectivity-culture-and-credit))
- **Redundant confirmation.** "Redundancy isn't waste, it's architecture" in low-trust environments. [S] ([India Fintech](https://indiafintech.substack.com/p/the-soundbox-economy-episode-62))
- **Recommendation [U]:** the sealed parcha should show:
  - A circular stamp-style seal, "✓ ग्राहक ने मंज़ूर किया" (customer approved), with date and time.
  - The parcha number.
  - Garage name and phone.
  - The customer's masked number (******4321).
  - "आवाज़ से मंज़ूरी" (approved by voice) with a play button for the recorded "haan".
  - A share button.
  - A live link back to the record.

### 4.10 Low-end performance

- Android "Build for Billions" guidance [V] ([Android UI for billions](https://developer.android.com/docs/quality-guidelines/build-for-billions/ui)):
  - "Target 60 frames per second on low-cost devices".
  - "Reduce or remove animations on low-cost devices".
  - Give touch feedback "on all touchable elements".
  - "Avoid blocking dialogs with loading indicators".
  - Use placeholder UI rather than a blank screen.
- Data can cost "upwards of 10% of a typical user's monthly income" in some markets. [S] ([data cost](https://developer.android.com/docs/quality-guidelines/build-for-billions/data-cost))
- Emerging-market phones cost US$40–60 and have little storage; apps should work offline-first. [V] ([Google Design](https://design.google/library/connectivity-culture-and-credit))
- Voice upload fails on slow links. [V] (COMPASS '22). *Implication [U]:* queue and retry audio, show "भेज रहे हैं…" (sending…) progress, and never lose a recording.

---

## 5. Proposed Hindi/Hinglish UI lexicon

Every entry below is an inference [U] built on the evidence in §4.2 and §2.6. Test it with 5–8 mechanics.

| Concept | Use (primary, Devanagari) | Small secondary | Avoid (too formal or rare) | Why |
|---|---|---|---|---|
| Job slip | **पर्चा** | Job card | कार्य पत्रक | The product name; vernacular "parcha/parchi" |
| New slip | **नया पर्चा** | New | नवीन प्रविष्टि | — |
| Speak (mic) | **बोलिए** / "बोलकर बताइए" | Tap & speak | ध्वनि इनपुट | Voice-first |
| Part | **पार्ट** | Part | पुर्ज़ा (OK in speech, rarer in writing) | Loanword in the Hindi auto press |
| Labour | **लेबर** / मज़दूरी | Labour | श्रम शुल्क | "लेबर चार्ज" is used in the Hindi auto press |
| Total | **कुल** / **टोटल** | Total | योग | Both are common; test which reads faster |
| Cost | **खर्चा** | Cost | लागत / व्यय | Colloquial |
| Estimate | **एस्टीमेट** | Estimate | अनुमानित लागत | Hindi press: "पहले एस्टीमेट मांगें" |
| Ready time | **गाड़ी कब मिलेगी:** आज शाम 6 बजे | Ready by | वितरण समय | Mirrors the customer's own question |
| Check flagged field | **एक बार देख लीजिए** | Check | सत्यापित करें | Polite, colloquial |
| Approve | **हाँ, ठीक है** | Approve | पुष्टि करें | Given in the brief; spoken register |
| Change one item | **बदलो** / बदलिए | Change | संपादित करें | Given in the brief |
| Send | **भेजो** / WhatsApp पर भेजें | Send | प्रेषित करें | — |
| Approved (seal) | **मंज़ूर** | Approved | अनुमोदित | Urdu-origin, everyday word |
| Save | **सेव करो** / रख लो | Save | सहेजें | Duolingo/Meesho pattern |

Register [U]: address the customer with **आप**. For the mechanic, use friendly imperatives (बोलिए, देख लीजिए).

---

## 6. Ranked design requirements

| # | Requirement | Evidence |
|---|---|---|
| 1 | **Voice-first primary action.** One giant mic (at least 88–96 px) in the thumb zone. Hold-to-talk or tap-to-start with a level meter. | COMPASS (28/30 voice search, 20/30 voice notes); Medhi 2011 (text unusable); WhatsApp voice culture |
| 2 | **Live, editable transcript and itemised read-back** before sending. Only flagged fields need review. | COMPASS (users verify voice output); noise 81–90+ dBA causes ASR errors; Hello Entrepreneurs ("every additional screen… friction") |
| 3 | **Audio confirmation on both sides.** The customer hears the estimate. The mechanic's phone announces "₹X का पर्चा मंज़ूर" when the customer approves. | Paytm, PhonePe and GPay soundbox / voice alerts; Medhi's voice feedback; fake-screenshot risk |
| 4 | **₹ amounts are the hero.** International digits, Indian grouping (`en-IN`), 28–40 px bold numerals, amounts normalised to words for TTS. | Medhi (numerals readable by non-literate users); Art. 343; Wikipedia Lakh; Gnani TTS (lakh/crore normalisation) |
| 5 | **Hindi-first Devanagari labels in everyday loanwords** (पार्ट, लेबर, टोटल, एस्टीमेट), with an optional small English line. Accept Roman Hinglish input. | KPMG (~70% trust local language); Duolingo; Meesho; COMPASS loanwords; Romanagari reading cost; 93% Roman typing. Bilingual ordering is [U]. |
| 6 | **Large touch targets.** At least 48 px everywhere, 64 px or more for primary buttons, 88–96 px for mic / हाँ / बदलो, at least 8 px gaps, no gesture-only actions. | NN/g 1 cm; Material 48 dp; MIL-STD 15/20 mm [S/U]; RainCheck (wet or conductive fingers) |
| 7 | **Light "paper-slip" theme with at least 7:1 text contrast.** No light greys or thin weights; dark mode not the default. | NN/g polarity; DisplayMate reflectance; WCAG 1.4.6; Khatabook notebook metaphor |
| 8 | **Devanagari typography.** Body 18–20 px, line-height 1.5–1.7, no letter-spacing on Devanagari, Medium or SemiBold for emphasis. Mukta or Hind, at most 2 weights. | Material tall-script rules; Alphabettes; Google Design; presbyopia 43–56% in over-35s/40s [S] |
| 9 | **Customer screen as a phone call.** Incoming-call style screen with a green answer button. The estimate is read aloud. Two huge buttons: "हाँ, ठीक है" (green) and "बदलो" (amber), with voice reply allowed. | Medhi 2011 (live operator up to 10x more accurate); Maruti's advisor confirmation call; 27/30 COMPASS users make video calls |
| 10 | **Line-item card with per-line change**, each line carrying a reason and optional photo, plus a clear total. | Maruti per-part approve/reject with photos; labour-illusion research; dispute patterns (duplicate labour, vague consumables) |
| 11 | **Verifiable seal.** Stamp-style "✓ मंज़ूर" with timestamp, parcha number, garage identity, masked customer number, voice-approval replay and a live link. Never label it "पक्का बिल" unless it is a GST invoice. | UPI success-screen elements; fake-screenshot scams; rubber-stamp culture; kacha vs pakka; CPA approval guidance [S] |
| 12 | **"गाड़ी कब मिलेगी" as a first-class field** on the card and in the WhatsApp text, kept stable. | Swiggy ETA anxiety research [S]; Hero real-time status on WhatsApp |
| 13 | **WhatsApp-native hand-off.** Prefilled Hindi message naming garage and vehicle; per-parcha OG image (1200×630, under 300 KB) showing the total; PDF as follow-up; no OTP or payment on the approval page. | WhatsApp OG constraints; garage SaaS conventions (PDF on WhatsApp); 530M users; COMPASS link-fraud anecdote |
| 14 | **Colour semantics.** Green = yes/approved, amber = check/change, red only for errors or delete, maroon "ledger" brand accent. Always icon + word + colour. | UPI green-tick convention; bahi-khata red as auspicious; Medhi colour-meaning mismatch; NBU "pair icons with text" |
| 15 | **Built for a 360×800 low-end Android on flaky 4G.** Small JS, few animations, instant touch feedback, placeholder UI, audio queued and retried offline, no login wall (phones are shared). | Statcounter (360×800 top, Android 94%); Build for Billions; COMPASS (data rationing, 22/30 share phones, voice fails on slow internet) |

---

## 7. Open questions to check in the field

1. **Bilingual order.** Does Hindi-primary with English-secondary actually beat English-primary for mechanics in Tier-1 cities, who may be more Hinglish/Roman-literate? No direct evidence was found. Run a 5-user preference and timed-read test. [U]
2. **"कुल" vs "टोटल", and "लेबर" vs "मज़दूरी".** Which is recognised faster? [U]
3. **Hold-to-talk vs tap-to-toggle with greasy fingers.** Long-press is risky on wet screens (RainCheck), so test both. [U]
4. **Does the customer accept a simulated call from a web page,** or does it read as a scam? This relates to COMPASS's link-fraud fear. [U]
5. **Typical mechanic phone.** Check RAM, Android version and whether the screen is LCD or AMOLED in the actual target garages. The Statcounter data is skewed towards web traffic. [U]
6. **Noise.** Measure dBA at 2–3 real garages. The Indian 81–90 dBA figure comes from an abstract (automobile industry, not roadside garages). [S]
7. **Legal claims** (CGST ₹200 invoice threshold, CPA §2(47) wording, any Motor Vehicles Act provisions on estimates) come from a consumer-rights wiki. Verify them before using them in product copy. [S/U]

---

## 8. Source list (by section)

**Primary or official (read in full or in the relevant section) [V]**
- Gupta, Mehta, Punj, Medhi Thies. *Sophistication with Limitation: Understanding Smartphone Usage by Emergent Users in India*. COMPASS '22. https://www.microsoft.com/en-us/research/wp-content/uploads/2022/05/compass22-34-taps.pdf
- Medhi, Sagar, Toyama. *Text-Free User Interfaces for Illiterate and Semiliterate Users*. ITID 2007. https://ocw.mit.edu/courses/mas-965-nextlab-i-designing-mobile-technologies-for-the-next-billion-users-fall-2008/8ccecb3eacd514b7ea0255f5158de907_MITMAS_965F08_medhi2007.pdf
- Dayal & Bhandari. *Skill Shortages and Gaps in the Motor Vehicles Sector*. NCAER Policy Brief No. 1, Oct 2025. https://ncaer.org/wp-content/uploads/2025/10/NCAER-Policy-Brief-Oct-2025.pdf
- AutocarPro, aftermarket servicing: https://www.autocarpro.in/news/-transforming-indias-aftermarket-servicing-industry-121897
- AutocarPro, Hero MotoCorp WhatsApp: https://www.autocarpro.in/news-national/hero-motocorp-introduces-sales-and-aftersales-services-on-whatsapp-78958
- Hello Entrepreneurs, digitising the garage: https://helloentrepreneurs.com/corporate/insight/why-digitising-the-garage-is-harder-than-digitising-the-enterprise-97606/
- Rushlane, Maruti online job-card approval: https://www.rushlane.com/maruti-customer-service-launch-new-system-12287133.html
- PhonePe press release, voice notifications: https://www.phonepe.com/press/phonepe-launches-vernacular-voice-notifications-on-its-business-app/
- TechCrunch, Google Pay Soundpod: https://techcrunch.com/2023/01/17/google-pay-soundbox-india/
- TechCrunch, 7 billion WhatsApp voice messages a day: https://techcrunch.com/2022/03/30/people-are-sending-7-billion-voice-messages-on-whatsapp-every-day
- Duolingo, India localisation: https://blog.duolingo.com/language-learning-for-the-next-billion-duolingo-in-india/
- Meesho Tech, designer's first 6 months: https://medium.com/meesho-tech/my-first-6-months-as-a-product-designer-at-meesho-90b7144c955b
- Meesho Tech, videos and social commerce: https://medium.com/meesho-tech/videos-and-social-commerce-a709d5f4856
- Google Design, *Connectivity, culture and credit*: https://design.google/library/connectivity-culture-and-credit
- Google Design, *New wave of Indian type design*: https://design.google/library/new-wave-indian-type-design
- Android, UI and content for billions: https://developer.android.com/docs/quality-guidelines/build-for-billions/ui
- Material Design v1 typography: https://m1.material.io/style/typography.html
- Alphabettes, Devanagari Typography 101: https://www.alphabettes.org/devanagari-typography-101-a-guide-for-typesetting-with-latin/
- NN/g, dark mode: https://www.nngroup.com/articles/dark-mode/
- NN/g, touch target size: https://www.nngroup.com/articles/touch-target-size/
- DisplayMate, bright-light shoot-out: https://www.displaymate.com/Smartphone_Brightness_ShootOut_1.htm
- Statcounter (Sept 2026): https://gs.statcounter.com/os-market-share/mobile/india · https://gs.statcounter.com/vendor-market-share/mobile/india · https://gs.statcounter.com/screen-resolution-stats/mobile/india · https://gs.statcounter.com/android-version-market-share/mobile-tablet/india
- Gnani, Hindi TTS guide: https://www.gnani.ai/resources/blogs/best-text-to-speech-hindi-tools-in-2026-gnani-ai-google-translate-alternatives
- Mukharji, *The Art of Rubber Stamps*: https://web.sas.upenn.edu/mukharji/2021/01/02/the-art-of-rubber-stamps/
- ThePrint, CAMS 2022-23: https://theprint.in/india/50-of-indias-internet-users-dont-know-how-to-send-email-a-third-know-online-banking-govt-survey/2308129/
- Careers360, ASER 2023: https://news.careers360.com/over-86-8-percent-in-14-18-age-group-enrolled-25-cent-of-them-cant-read-class-2-text-fluently-aser
- Wikipedia, Lakh: https://en.wikipedia.org/wiki/Lakh
- Wikipedia, Hindustani numerals: https://en.wikipedia.org/wiki/Hindustani_numerals
- RTI Wiki, bike service rights: https://righttoinformation.wiki/bike-service-refund-re-repair-rights-india
- RTI Wiki, car service overcharging: https://righttoinformation.wiki/car-service-overcharging-unapproved-parts-india
- indianpaycalculator, fake UPI screen: https://www.indianpaycalculator.in/govt-news/fake-upi-payment-screenshot-scam-shopkeepers-verify-2026
- News24 Hindi, car service scam: https://hindi.news24online.com/auto/car-service-scam-at-service-center-aware-and-avoid-these-things/833660/
- GarageSaarthi, automation (vendor): https://garagesaarthi.com/features/automation/

**Secondary, search-snippet or aggregator [S]**
- Medhi et al., TOCHI 2011: https://dl.acm.org/doi/10.1145/1959022.1959024
- Barber 2004: https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-2419.2004.00202.x
- Medhi & Toyama, full-context video: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/ictd2007_medhi_toyama.pdf
- KPMG–Google 2017: https://assets.kpmg.com/content/dam/kpmg/in/pdf/2017/04/Indian-languages-Defining-Indias-Internet.pdf
- Quartz on KPMG–Google: https://qz.com/india/972844/indias-internet-users-have-more-faith-in-content-thats-not-in-english-study-says
- Entrackr, 530M WhatsApp users: https://entrackr.com/2021/02/govt-says-whatsapp-has-530-mn-users-in-india/
- Entrepreneur India, MSME WhatsApp use: https://india.entrepreneur.com/news-and-trends/whatsapp-and-whatsapp-business-dominate-msme-landscape-with/476232
- India Fintech substack, soundbox economy: https://indiafintech.substack.com/p/the-soundbox-economy-episode-62
- The Hard Copy, Paytm voice: https://thehardcopy.co/paytm-uses-voice-to-reassure-small-businesses/
- Khatabook adoption: https://www.markhub24.com/post/khatabook-s-digital-ledger-adoption-strategy-for-small-businesses · https://ameya.substack.com/p/how-khatabook-became-the-premier
- Autorox: https://play.google.com/store/apps/details?id=apps.autorox.co&hl=en_US
- GaragePro: https://garagepro.me/
- Mechanic Mate: https://play.google.com/store/apps/details?id=com.mfinityinfotech.mechanicmate&hl=en_US
- GarageSaarthi job card: https://www.garagesaarthi.com/solutions/garage-job-card-software/
- HelloGrowthCRM: https://hellogrowthcrm.com/whatsapp-crm-for-automotive
- GoMechanic FAQ: https://gomechanic.in/faq
- Kacha vs pakka bill: https://www.mapsofindia.com/my-india/government/can-gst-bill-really-kill-the-kachcha-bill-system · https://www.taxreturnwala.com/will-gst-help-curbing-black-money/
- Noise: https://pmc.ncbi.nlm.nih.gov/articles/PMC11569067/ · https://www.researchgate.net/publication/51208255_Exposure_Assessment_in_Auto_Collision_Repair_Shops · https://academic.oup.com/annweh/article/65/8/930/6316228
- RainCheck: https://mynkgoel.github.io/pdfs/raincheck.pdf
- Parhi, Karlson & Bederson 2006: https://www.microsoft.com/en-us/research/wp-content/uploads/2006/01/parhi-mobileHCI06.pdf
- Material accessibility: https://m1.material.io/usability/accessibility.html
- TetraLogical, target size: https://tetralogical.com/blog/2022/12/20/foundations-target-size/
- MIL-STD touch zones: https://link.springer.com/chapter/10.1007/978-3-319-40406-6_7
- WCAG 1.4.6: https://w3c.github.io/wcag/understanding/contrast-enhanced.html
- Constitution of India, Art. 343: https://www.constitutionofindia.net/articles/article-343-official-language-of-the-union/
- W3C number formatting: https://www.w3.org/International/questions/qa-number-format
- MDN Intl.NumberFormat: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat
- Nature India 2013: https://www.nature.com/articles/nindia.2013.23
- Reading & Writing 2021: https://link.springer.com/article/10.1007/s11145-021-10241-7
- Nature HSSC 2024: https://www.nature.com/articles/s41599-024-03058-6
- Buell & Norton, *The Labor Illusion*: https://www.hbs.edu/faculty/Pages/item.aspx?num=40158
- Swiggy tracking: https://www.upraised.co/blog/swiggy-order-tracking/ · https://www.markhub24.com/post/when-every-minute-is-a-brand-promise-swiggy-s-delivery-time-prediction-algorithm
- WhatsApp OG: https://ogpreview.app/open-graph/whatsapp · https://www.opengraph.to/articles/og-image-too-large
- Bahi-khata red: https://www.newsbytesapp.com/news/business/what-is-bahi-khata-the-red-ledger-sitharaman-carries-during-budget/story · https://asiainch.org/craft/bahi-clothbound-books-of-rajasthan/
- Colour symbolism: https://study.com/academy/lesson/colors-in-indian-culture.html
- PLFS 2023-24 literacy: https://www.class24.study/current-affairs/india-literacy-rate-plfs-2024 · https://www.induqin.com/post/india-s-literacy-landscape-insights-from-the-plfs-2023-24-report
- NSS 78th round: https://www.business-standard.com/india-news/over-82-of-rural-youth-able-to-use-internet-in-india-says-govt-survey-124100901062_1.html
- Presbyopia: https://www.ovid.com/jnls/jfmpc/fulltext/10.4103/jfmpc.jfmpc_1148_21~prevalence-of-presbyopia-spectacles-coverage-and-barriers · https://www.ovid.com/jnls/ijo/fulltext/10.4103/ijo.ijo_1235_18~prevalence-of-refractive-errors-uncorrected-refractive-error
- IDC / BusinessToday, smartphone market: https://my.idc.com/getdoc.jsp?containerId=prAP53921425 · https://www.businesstoday.in/technology/news/story/india-smartphone-shipments-drop-7-in-q1-2025-vivo-and-apple-lead-growth-as-xiaomi-slumps-474928-2025-05-06
- Fonts: https://github.com/EkType/Mukta · https://fonts.google.com/specimen/Hind · https://ektype.in/baloo-family.html · https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari · https://fontsource.org/fonts/tiro-devanagari-hindi
- NBU summaries: https://www.shopify.com/partners/blog/next-billion-users · https://uxspot.io/nbu/
- Cashfree, fake UPI apps: https://www.cashfree.com/blog/spot-fake-upi-payment-app-scams/
- Paytm UPI receipt help: https://paytm.com/support/upi/how-to-get-upi-transaction-receipt-on-paytm
- Mechanic YouTube: https://www.tyremarket.com/roadtales/top-10-automotive-youtubers-in-india/ · https://www.youtube.com/@mechanicindia1
- Garage counts (unaudited): https://autofintechs.com/automotive-aftermarket-garages-in-india-now-near-future-and-ever-after/ · https://www.kenresearch.com/industry-reports/india-multi-brand-car-service-market

**Not reachable (blocked or paywalled), cited only through secondary summaries:** Team-BHP (Maruti approval thread), Medium/Khatabook blog, Think with Google localisation page (now redirects), the PMC noise study full text, the Springer MIL-STD chapter, and factly.in (NSS ICT skills).
