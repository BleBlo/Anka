# arXiv to ACL Rolling Review Conversion Checklist

## Submission Details
- **Deadline**: January 5, 2026
- **Format**: ACL 2023 LaTeX template (two-column)
- **Page Limit**: 8 pages main content + unlimited references/appendix
- **Current Status**: 6 pages (within limit)

---

## Anonymization Completed

| Item | Status | Details |
|------|--------|---------|
| Author name removed | DONE | "Saif Khalfan Saif Al Mazrouei" → "Anonymous" |
| Email removed | DONE | Removed completely |
| Affiliation removed | DONE | "University of Wisconsin-Madison" → removed |
| GitHub URL anonymized | DONE | Changed to "Anonymous repository (link available upon acceptance)" |
| Self-citations checked | DONE | No self-citations present |
| Code/data links anonymized | DONE | Footnote added in abstract |

---

## Format Changes

| Item | Status | Details |
|------|--------|---------|
| Template converted | DONE | Using `acl.sty` with `[review]` option |
| Two-column layout | DONE | Automatic with ACL style |
| Line numbers added | DONE | Automatic with `[review]` option |
| Page numbers | DONE | Automatic for review mode |
| Font (Times) | DONE | Using `times.sty` |
| Citations (natbib) | DONE | Using `acl_natbib.bst` |

---

## Content Restructuring

| Section | Status | Changes |
|---------|--------|---------|
| Abstract | DONE | Condensed slightly, added anonymous repo footnote |
| Introduction | DONE | Condensed from 2 pages to ~1.5 columns |
| Related Work | DONE | Condensed from 1.5 pages to ~0.75 columns |
| Anka Language | DONE | Condensed implementation details, kept core syntax |
| Methodology | DONE | Kept essential details, trimmed verbose descriptions |
| Results | DONE | Kept all tables and figures, condensed analysis |
| Discussion | DONE | Condensed subsections |
| Limitations | DONE | Required section - already present (Section 7) |
| Conclusion | DONE | Kept main points |
| Ethics Statement | DONE | Present (unnumbered section) |
| References | DONE | 18 citations (unlimited pages) |
| Appendix | DONE | Moved: Grammar spec, Extended examples, Prompts, Task examples |

---

## Required Sections Verification

| Section | Required | Present |
|---------|----------|---------|
| Abstract | Yes | Page 1 |
| Introduction | Yes | Section 1 |
| Related Work | Recommended | Section 2 |
| Methodology | Yes | Section 4 |
| Results | Yes | Section 5 |
| Limitations | **REQUIRED** | Section 7 (present) |
| Ethics Statement | Recommended | Present (after Section 8) |

---

## Files in anka-acl Directory

```
anka-acl/
├── anka_acl.tex          # Main LaTeX source
├── anka_acl.pdf          # Compiled PDF (6 pages)
├── references.bib        # Bibliography (18 entries)
├── complexity_advantage.png  # Figure 1
├── acl.sty               # ACL style file
├── acl_natbib.bst        # Bibliography style
└── CONVERSION_CHECKLIST.md   # This file
```

---

## Before Submission

- [ ] Verify no author-identifying information in PDF metadata
- [ ] Check figure resolution (300 DPI minimum)
- [ ] Verify all citations resolve correctly
- [ ] Run spell check
- [ ] Read through for any remaining identifying information
- [ ] Upload to OpenReview (ARR submission system)

---

## Key Differences from arXiv Version

1. **Page count**: 11 pages → 6 pages (8 limit + appendix)
2. **Format**: Single column → Two column
3. **Author info**: Full author block → "Anonymous"
4. **GitHub link**: Direct URL → "Available upon acceptance"
5. **Line numbers**: None → Present (for review)
6. **Detailed grammar/implementation**: Main body → Appendix
