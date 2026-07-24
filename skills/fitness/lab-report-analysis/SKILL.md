---
name: lab-report-analysis
description: "Parse and interpret bloodwork/lab reports: flag out-of-range biomarkers, prioritize by severity, and contextualize for fitness and nutrition planning."
version: 1.0.0
author: Friday
license: MIT
metadata:
  hermes:
    tags: [health, fitness, nutrition, bloodwork, lab, biomarkers, coaching]
    related_skills: [ocr-and-documents]
---

# Lab Report Analysis

## When to Use

When Tanzim shares a lab report (PDF or image) for himself or a trainee (Blair, Sagar, etc.) and wants it analyzed — either for general health awareness or to inform training/nutrition programming.

---

## Step 1: Extract the PDF

Use `pdftotext` first (fastest, no Python needed):

```bash
sudo apt-get install -y poppler-utils
pdftotext /path/to/report.pdf /tmp/lab_output.txt
cat /tmp/lab_output.txt
```

If poppler is unavailable, fall back to pymupdf:

```bash
pip install pymupdf --break-system-packages
python3 -c "
import pymupdf
doc = pymupdf.open('report.pdf')
for page in doc:
    print(page.get_text())
"
```

---

## Step 2: Identify Flagged Values

Scan for any result explicitly marked High / Low / Critical / Alert by the lab. These are the non-negotiables — always surface these.

---

## Step 3: Prioritize by Severity

Group findings into three tiers:

**Critical (act now):** Out of range + clinically significant for health risk or training capacity. Examples: Vitamin D severely deficient, LDL very high, fasting glucose high.

**Elevated / Watch:** Borderline or trending in wrong direction across draws. Examples: WBC just above ceiling, ALP persistently high, HDL barely above low threshold.

**In Range but Notable:** Within reference but trending or relevant to fitness context. Examples: BUN/Creatinine low (protein intake?), hemoglobin dipping, TSH trending toward high end.

---

## Step 4: Contextualize for Fitness/Nutrition

For each flagged metric, note its relevance to:
- Training performance (energy, recovery, muscle function)
- Body composition
- Cardiovascular risk (especially lipids)
- Hormonal health (Vitamin D, TSH)
- Inflammation markers (WBC, ALP)

---

## Step 5: Flag for Action Plan

After analysis, note which markers should drive the training/nutrition intervention. Tanzim will use these to build the actual program — your job is the analysis and prioritization, not the prescription.

---

## Key Biomarkers Reference (Fitness Context)

| Marker | Optimal (fitness) | Why it matters |
|---|---|---|
| Vitamin D | 40-80 ng/mL | Muscle function, testosterone, immunity, recovery |
| LDL | <100 mg/dL | Cardiovascular risk |
| HDL | >50 mg/dL (men) | Cardioprotection |
| Triglycerides | <100 mg/dL (fasted) | Metabolic health, note: non-fasting inflates by ~20-30% |
| Total Chol/HDL ratio | <5.0 | Overall CV risk indicator |
| TSH | 1.0-2.5 uIU/mL | Thyroid; higher = sluggish metabolism |
| Fasting glucose | 70-90 mg/dL | Insulin sensitivity |
| BUN/Creatinine | 10-20 | Low can signal low protein intake |
| WBC | 4.5-8.0 x10E3/uL | Chronic elevation = inflammation |
| Hemoglobin | 14-17.5 g/dL (men) | Aerobic capacity, oxygen delivery |

---

## Pitfalls

- **Non-fasting lipids**: Triglycerides drawn non-fasting are artificially elevated by ~20-30%. Note this in the analysis — don't over-alarm.
- **Reference ranges vary by lab**: Always use the lab's own reference interval, not general textbook values.
- **Trending matters more than single draw**: Always compare to previous results if available.
- **Don't prescribe**: Friday flags and contextualizes. Tanzim as the licensed trainer/nutritionist designs the intervention.
- **Confidential PHI**: Lab reports contain protected health information. Handle accordingly — do not log or expose to unauthorized parties.
