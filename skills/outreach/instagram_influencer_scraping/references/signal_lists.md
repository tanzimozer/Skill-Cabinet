# Signal Lists

## FEMALE_SIGNALS
Used to detect female-identifying accounts. Check in bio + full_name + username (lowercased, combined).

```python
FEMALE_SIGNALS = [
    'she','her','woman','women','girl','lady','female','mum','mom','mama',
    'queen','sis','sister','wife','daughter','she/her','♀','👩','💁','🧘',
    '💃','🧖','👸','🤱','🌸','💅','🌺','💄','🦋','miss','mrs','bride',
    'doula','she/','/her','auntie','aunty','niece','goddess','🙋','🤰','👧',
]
```

## COMPANY_SIGNALS
Used to reject business/service accounts. Check same combined string. ANY match = remove.

```python
COMPANY_SIGNALS = [
    ' studio',' studios',' gym ',' clinic',' centre',' center',
    ' institute',' academy',' school',' college',' services',' solutions',
    ' therapies',' physio',' physiotherapy',' chiropractic',
    'iv therapy',' infusion','cosmetic clinic','skin clinic',
    'run club','running club','boot camp','bootcamp','dance studio',
    'spin studio','pilates studio','yoga studio','energy drink',
    'protein powder','not-for-profit','nonprofit','community hub',
    ' photographer',' photography',' videographer','real estate',
    'mortgage',' ltd',' llc',' inc',' pty',
]
```

## Caveats
- `' gym '` (with spaces) avoids false-positives on "gym lover", "gym girl" etc.
- Personal coaches with "coaching" in bio are fine — "coaching" is NOT in company signals
- Keyword filter is imperfect — always follow up with Opus classification pass
- Opus removes false positives that keywords miss and saves false negatives that keywords wrongly remove
