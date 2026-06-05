<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# help me refine the regexes to better handle multi‑pincode lines and mixed Email/Phone on the same line, based on how i want the DB cleaned

You can make this quite robust by (a) decoupling extraction from labels, and (b) using **separate passes** for PIN, phone, and email, with well‑scoped text slices.

Below are refined regexes + patterns and how to wire them into your scraper.

***

## 1. Refined PIN code extraction (multi‑PIN safe)

For Indian PINs, you want:

- Exactly 6 digits
- First digit not 0
- Optional space in the middle (e.g., `600 001`)

A good pattern is:

```python
PIN_RE = re.compile(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b")
```

This is essentially the `[1-9]\d{5}` pattern with an optional space after the first three digits.[^1][^2][^3]

**Usage for multi‑pincode lines:**

```python
pin_candidates = PIN_RE.findall(details_text)
# e.g., ["600001", "600 002"]

# Normalise (strip spaces)
pin_candidates = [p.replace(" ", "") for p in pin_candidates]

# Strategy 1: keep all as list field
pincodes = sorted(set(pin_candidates))  # for a multi-valued column

# Strategy 2: pick one canonical PIN per hospital
pincode = pincodes[-1] if pincodes else None  # e.g., last one in the line/block
```

For your DB:

- Store `pincode` (single) as the canonical one you choose.
- Optionally have `pincode_all` as a JSON array if you want to preserve all matches for QC later.

Because PINs are 6‑digit and phones are 10‑digit, this regex will **not** collide with Indian mobile numbers.[^4]

***

## 2. Phone and email extraction when they share a line

### 2.1 Base regexes

**Email** (simple, robust enough for scraped pages):

```python
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
```

This is in line with common email-detection patterns used in automation tools.[^5]

**Indian phone (mobile + optional +91 / 0):**

```python
PHONE_RE = re.compile(
    r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b"
)
```

Pattern aligns with standard Indian phone rules: 10 digits, starting 6–9, with optional `+91`/0.[^6][^1]

You can later extend `PHONE_RE` if you want to also capture landlines like `044-22223333`.

***

### 2.2 Scope by labels: “Phone” vs “Email”

Instead of running `PHONE_RE` and `EMAIL_RE` over the entire block, scope by labels:

```python
def extract_between(label_start, label_end, text):
    """
    Return substring between label_start and label_end (or end of text).
    """
    start = re.search(label_start, text, flags=re.IGNORECASE)
    if not start:
        return ""
    start_idx = start.end()
    if label_end:
        end = re.search(label_end, text, flags=re.IGNORECASE)
        end_idx = end.start() if end else len(text)
    else:
        end_idx = len(text)
    return text[start_idx:end_idx]

details_text = details_text or ""

# 1. Get the phone block: between 'Phone' and 'Email' (if present)
phone_block = extract_between(r"Phone\s*:", r"Email\s*:", details_text)

# 2. Get the email block: from 'Email' to end
email_block = extract_between(r"Email\s*:", None, details_text)

phones = PHONE_RE.findall(phone_block)
emails = EMAIL_RE.findall(email_block)

phone = phones[^0] if phones else None
email = emails[^0] if emails else None
```

So a line like:

`Phone : 9876543210, 044-22223333 Email : info@hospital.org`

will be split into:

- `phone_block = " 9876543210, 044-22223333 "`
- `email_block = " info@hospital.org"`

Your `PHONE_RE` picks the mobile; you can optionally add a second regex for landlines.

***

## 3. Handling multiple phones and emails

In real pages you may see:

`Phone : 9876543210 / 9444433221 Email : admin@hosp.org, help@hosp.org`

Refine behavior:

```python
phones = PHONE_RE.findall(phone_block)
emails = EMAIL_RE.findall(email_block)

# Normalise phones: remove spaces/dashes from Indian format
phones = [re.sub(r"[^\d]", "", p)[-10:] for p in phones]  # keep last 10 digits

# DB cleaning policies
primary_phone = phones[^0] if phones else None
all_phones = sorted(set(phones))  # optional JSON list

primary_email = emails[^0] if emails else None
all_emails = sorted(set(emails))
```

You can decide:

- For `hospital.phone`: store `primary_phone`.
- For `hospital.phone_all`: keep all as JSON list for future outreach tooling.

Same for emails.

***

## 4. Making label-based extraction more tolerant

District pages sometimes vary label spacing and case: `Phone :`, `Phone:`, `PHONE :`. Use a label regex like:

```python
PHONE_LABEL = r"Phone\s*:?"
EMAIL_LABEL = r"Email\s*:?"
PIN_LABEL   = r"Pincode\s*:?"
```

Then your general extractor:

```python
def extract_label_value(label_regex, text):
    # Captures text after label up to next label or line break
    pattern = rf"{label_regex}\s*(?P<value>[^:]+?)(?=(Phone\s*:|Email\s*:|Pincode\s*:|\n|\r|$))"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return m.group("value").strip() if m else None
```

For `Pincode`, you can then run `PIN_RE.findall(value)` to support multiple PINs in the “pincode line”.

***

## 5. Putting it together in your scraper

Combining everything into your previous `records.append` logic:

```python
details_text = " ".join(details_nodes)

# 1) Pincodes
pin_candidates = PIN_RE.findall(details_text)
pin_candidates = [p.replace(" ", "") for p in pin_candidates]
pincodes_all = sorted(set(pin_candidates))
pincode = pincodes_all[-1] if pincodes_all else None

# 2) Scoped phone/email
phone_block = extract_between(r"Phone\s*:", r"Email\s*:", details_text)
email_block = extract_between(r"Email\s*:", None, details_text)

phones = PHONE_RE.findall(phone_block)
phones = [re.sub(r"[^\d]", "", p)[-10:] for p in phones]  # normalise
phone = phones[^0] if phones else None

emails = EMAIL_RE.findall(email_block)
email = emails[^0] if emails else None

record = {
    "name": name,
    "address": address,
    "pincode": pincode,
    "pincodes_all": pincodes_all,
    "phone": phone,
    "phones_all": sorted(set(phones)),
    "email": email,
    "emails_all": sorted(set(emails)),
}
```

This setup:

- Avoids mis‑classifying phone digits as pincodes by using 6‑digit vs 10‑digit patterns and word boundaries.[^3][^1]
- Works whether `Phone` and `Email` are on the same line or not, as long as labels exist.
- Gives you single “clean” values plus optional arrays for QC and multi‑contact usage.

If you share a sample `details_text` block from one of the trickier districts, I can tune the patterns further to that exact variation.
<span style="display:none">[^10][^11][^12][^13][^14][^15][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://stackoverflow.com/questions/76825512/write-regex-for-pincode-of-6-digits-ie-indian-pincode

[^2]: https://stackoverflow.com/questions/33865525/indian-pincode-validation-regex-only-six-digits-shouldnt-start-with-0

[^3]: https://regexpattern.com/indian-postal-pin-zip-code/

[^4]: https://en.wikipedia.org/wiki/Postal_Index_Number

[^5]: https://forum.uipath.com/t/how-to-extract-email-phone-number-from-a-text/544582

[^6]: https://gist.github.com/bkanhu/bf07ba56db19669a353a1bd94080dc15

[^7]: https://forum.keyboardmaestro.com/t/regex-help-extract-f-l-name-email-phone-and-text-message/13568/2

[^8]: https://stackoverflow.com/questions/75209722/extract-phone-numbers-from-email-signature-regex

[^9]: https://forum.bubble.io/t/detecting-emails-phone-numbers-and-links-via-extract-with-regex/17448

[^10]: https://www.emailparser.com/d/email-parser/capturing-text-with-regular-expressions

[^11]: https://stackoverflow.com/questions/365487/parse-email-content-with-regular-expressions

[^12]: https://stackoverflow.com/questions/72123498/regex-to-match-a-few-specific-6-digit-numbers-indian-pin-codes

[^13]: https://github.com/captn3m0/india-pincode-regex

[^14]: https://regex101.com/library/J0pFbM?orderBy=MOST_RECENT\&search=email\&page=5

[^15]: https://www.geeksforgeeks.org/dsa/how-to-validate-pin-code-of-india-using-regular-expression/

