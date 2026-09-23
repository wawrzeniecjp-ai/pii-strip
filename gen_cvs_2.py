#!/usr/bin/env python3
"""
Generate 10 fake CVs with 10 different layouts for text-extraction testing.

Dependencies:
    pip install faker reportlab
"""

import os
import random
from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OUTPUT_DIR = "fake_cvs"
PAGE_W, PAGE_H = A4  # 595 x 842 points
MARGIN = 25 * mm

fake = Faker()
Faker.seed(42)
random.seed(42)

# Helpers
import unicodedata

def _ascii_safe(s: str) -> str:
    """Strip diacritics; return only Latin-1-safe characters."""
    normalized = unicodedata.normalize("NFKD", s)
    return "".join(c for c in normalized if not unicodedata.combining(c))

# ---------------------------------------------------------------------------
# Curated pools — Faker's company() is useless for realistic names
# ---------------------------------------------------------------------------

COMPANIES = [
    "Northwind Analytics", "Acme Cloud Services", "Helix Biotech",
    "Vertex Logistics", "Blue Ridge Consulting", "Pinnacle Financial",
    "Copperfield Media", "Summit Health Systems", "Ironwood Software",
    "Lakeshore Manufacturing", "Brightline Energy", "Evergreen Retail Group",
    "Quantum Edge Labs", "Redwood Legal Partners", "Meridian Insurance",
    "Cascade Robotics", "Silverline Telecom", "Harborview Hospitality",
    "Meadowlark Publishing", "Northgate Pharmaceuticals",
    "Atlas Freight Co.", "Beacon Education Group", "Clearwater Utilities",
    "Driftwood Studios", "Foxglove Design", "Granite Peak Mining",
]

UNIVERSITIES = [
    "University of Michigan", "Purdue University", "Ohio State University",
    "University of Texas at Austin", "Georgia Institute of Technology",
    "Pennsylvania State University", "University of Washington",
    "North Carolina State University", "Arizona State University",
    "University of Colorado Boulder", "Rutgers University",
    "University of Florida", "Texas A&M University",
    "University of Illinois Urbana-Champaign", "Boston University",
    "Northeastern University", "Pomona College", "Harvey Mudd College",
]

ROLE_TEMPLATES = {
    "software": [
        ("Software Engineer", "Computer Science"),
        ("Senior Software Engineer", "Computer Science"),
        ("Backend Engineer", "Computer Science"),
        ("Frontend Engineer", "Computer Science"),
        ("Full Stack Developer", "Computer Science"),
        ("DevOps Engineer", "Computer Science"),
        ("Machine Learning Engineer", "Computer Science"),
        ("Data Engineer", "Computer Science"),
    ],
    "data": [
        ("Data Analyst", "Statistics"),
        ("Data Scientist", "Statistics"),
        ("Business Intelligence Analyst", "Information Systems"),
        ("Quantitative Analyst", "Mathematics"),
    ],
    "business": [
        ("Product Manager", "Business Administration"),
        ("Project Manager", "Business Administration"),
        ("Management Consultant", "Business Administration"),
        ("Operations Manager", "Business Administration"),
        ("Financial Analyst", "Finance"),
        ("Marketing Manager", "Marketing"),
        ("HR Business Partner", "Human Resources"),
    ],
    "engineering": [
        ("Mechanical Engineer", "Mechanical Engineering"),
        ("Electrical Engineer", "Electrical Engineering"),
        ("Civil Engineer", "Civil Engineering"),
        ("Chemical Engineer", "Chemical Engineering"),
    ],
    "creative": [
        ("UX Designer", "Design"),
        ("Graphic Designer", "Design"),
        ("Content Strategist", "Communications"),
        ("Technical Writer", "English"),
    ],
    "healthcare": [
        ("Clinical Research Associate", "Biology"),
        ("Regulatory Affairs Specialist", "Life Sciences"),
        ("Healthcare Analyst", "Public Health"),
    ],
}


def _pick_career_track():
    return random.choice(list(ROLE_TEMPLATES.keys()))


def _make_bullets(track, title):
    """Role-appropriate bullet points, not generic lorem."""
    templates = {
        "software": [
            "Designed and shipped {feature} used by {n}K+ daily users",
            "Reduced API latency by {pct}% through query optimization",
            "Led migration from monolith to microservices",
            "Mentored {n} junior engineers and ran code reviews",
            "Built CI/CD pipeline cutting deploy time from hours to minutes",
        ],
        "data": [
            "Built dashboards tracking {n} KPIs for executive reporting",
            "Developed churn model improving retention by {pct}%",
            "Automated ETL pipeline processing {n}M records daily",
            "Partnered with marketing to design A/B tests",
        ],
        "business": [
            "Managed {n}-person team across {n2} workstreams",
            "Delivered ${n}M in annual cost savings",
            "Owned roadmap for {product} product line",
            "Negotiated vendor contracts reducing spend by {pct}%",
        ],
        "engineering": [
            "Designed {component} for {product} production line",
            "Cut manufacturing defects by {pct}% via process redesign",
            "Led compliance effort for ISO {iso} certification",
            "Coordinated with suppliers on {n}-month project timeline",
        ],
        "creative": [
            "Redesigned onboarding flow increasing activation by {pct}%",
            "Produced {n} campaigns across web, print, and social",
            "Ran user research sessions with {n}+ participants",
            "Built design system adopted across {n} product teams",
        ],
        "healthcare": [
            "Coordinated {n} clinical trials across {n2} sites",
            "Prepared regulatory submissions for FDA review",
            "Analyzed patient outcomes across {n}K records",
            "Trained clinical staff on new protocols",
        ],
    }
    pool = templates.get(track, templates["business"])
    chosen = random.sample(pool, k=min(3, len(pool)))
    return [
        b.format(
            feature=random.choice(["search", "checkout", "billing", "auth", "reporting"]),
            product=random.choice(["core platform", "mobile app", "analytics suite"]),
            component=random.choice(["cooling system", "control module", "sensor array"]),
            iso=random.choice(["9001", "27001", "14001"]),
            n=random.choice([2, 3, 5, 8, 12, 20, 50]),
            n2=random.choice([2, 3, 4, 6]),
            pct=random.choice([12, 18, 22, 30, 45]),
        )
        for b in chosen
    ]


def _make_experience(track, n=3):
    """Generate a coherent work history, most recent first."""
    roles = ROLE_TEMPLATES[track]
    end_year = random.randint(2023, 2025)
    experience = []
    for _ in range(n):
        title, field = random.choice(roles)
        duration = random.randint(2, 4)
        start_year = end_year - duration
        experience.append({
            "title": title,
            "field": field,
            "company": random.choice(COMPANIES),
            "start": start_year,
            "end": end_year,
            "bullets": _make_bullets(track, title),
        })
        end_year = start_year
    return experience


def _make_education(track, earliest_work_year):
    """Education that ends before the first job."""
    degrees = [
        ("B.Sc.", 4),
        ("M.Sc.", 2),
        ("B.A.", 4),
        ("M.A.", 2),
    ]
    if track in ("data", "healthcare", "engineering") and random.random() < 0.3:
        degrees.append(("Ph.D.", 5))

    education = []
    grad_year = earliest_work_year
    degree, duration = random.choice(degrees)
    field = ROLE_TEMPLATES[track][0][1]
    education.append({
        "degree": degree,
        "field": field,
        "institution": random.choice(UNIVERSITIES),
        "start": grad_year - duration,
        "end": grad_year,
    })
    if random.random() < 0.4:
        degree2, duration2 = random.choice(degrees)
        education.append({
            "degree": degree2,
            "field": field,
            "institution": random.choice(UNIVERSITIES),
            "start": grad_year - duration - duration2,
            "end": grad_year - duration,
        })
    return education


def _make_summary(track, experience):
    years = sum(e["end"] - e["start"] for e in experience)
    latest = experience[0]
    return (
        f"{latest['title']} with {years}+ years of experience in "
        f"{latest['field'].lower()}. Proven track record at "
        f"{latest['company']} and prior roles, with strengths in "
        f"{random.choice(['cross-functional collaboration', 'systems thinking', 'stakeholder communication', 'process improvement'])}."
    )

import re
def clean_phone(raw: str) -> str:
    # Drop everything from the "x" / "ext" onward
    return re.sub(r"\s*(?:x|ext\.?)\s*\d+$", "", raw, flags=re.IGNORECASE).strip()

def generate_cv_data() -> dict:
    """Return a coherent set of realistic CV fields."""
    first = _ascii_safe(fake.first_name())
    last = _ascii_safe(fake.last_name())
    track = _pick_career_track()
    experience = _make_experience(track)
    earliest_work = min(e["start"] for e in experience)
    education = _make_education(track, earliest_work)

    return {
        "name": f"{first} {last}",
        "title": experience[0]["title"],
        "email": f"{first.lower()}.{last.lower()}@{random.choice(['gmail.com', 'outlook.com', 'protonmail.com', 'yahoo.com'])}",
        "phone": clean_phone(fake.phone_number()),
        "city": fake.city(),
        "country": fake.country(),
        "linkedin": f"linkedin.com/in/{first.lower()}-{last.lower()}",
        "summary": _make_summary(track, experience),
        "experience": experience,
        "education": education,
        "skills": random.sample(
            ["Python", "JavaScript", "SQL", "Machine Learning", "Docker",
             "AWS", "Git", "Agile", "Data Analysis", "React", "Java", "C++",
             "Kubernetes", "Terraform", "PostgreSQL", "TypeScript"],
            k=random.randint(4, 7),
        ),
        "languages": [
            {"lang": "English", "level": "Native"},
            {"lang": random.choice(["French", "Spanish", "German", "Mandarin", "Portuguese"]),
             "level": random.choice(["Fluent", "Intermediate", "Basic"])},
        ],
        "certifications": random.sample(
            ["AWS Certified Solutions Architect", "PMP",
             "Google Data Analytics", "Certified Scrum Master",
             "Cisco CCNA", "Azure Administrator Associate",
             "Certified Kubernetes Administrator"],
            k=random.randint(1, 2),
        ),
    }


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _text(c: canvas.Canvas, x, y, txt, font="Helvetica", size=10,
          color=black, anchor="left"):
    c.setFont(font, size)
    c.setFillColor(color)
    if anchor == "center":
        c.drawCentredString(x, y, txt)
    elif anchor == "right":
        c.drawRightString(x, y, txt)
    else:
        c.drawString(x, y, txt)


def _wrap_text(c: canvas.Canvas, x, y, txt, max_w, font="Helvetica",
               size=10, color=black, leading=14):
    c.setFont(font, size)
    c.setFillColor(color)
    words = txt.split()
    line, lines = "", []
    for w in words:
        test = f"{line} {w}".strip()
        if c.stringWidth(test, font, size) <= max_w:
            line = test
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    for ln in lines:
        c.drawString(x, y, ln)
        y -= leading
    return y


def _line(c: canvas.Canvas, x1, y1, x2, y2, color=black, width=0.5):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)


def _rect(c: canvas.Canvas, x, y, w, h, fill=None, stroke=None, width=0.5):
    if fill:
        c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(width)
    if fill and stroke:
        c.rect(x, y, w, h, fill=1, stroke=1)
    elif fill:
        c.rect(x, y, w, h, fill=1, stroke=0)
    else:
        c.rect(x, y, w, h, fill=0, stroke=1)


def _section_heading(c, x, y, text, font="Helvetica-Bold", size=12,
                     color=black):
    _text(c, x, y, text.upper(), font, size, color)
    return y - 16


def _draw_experience_block(c, y, d):
    for exp in d["experience"]:
        _text(c, MARGIN, y, exp["title"], "Helvetica-Bold", 10)
        _text(c, PAGE_W - MARGIN, y, f"{exp['start']} – {exp['end']}",
              "Helvetica", 9, HexColor("#666666"), anchor="right")
        y -= 13
        _text(c, MARGIN, y, exp["company"], "Helvetica-Oblique", 9,
              HexColor("#444444"))
        y -= 14
        for b in exp["bullets"]:
            _text(c, MARGIN + 10, y, f"• {b}", "Helvetica", 9)
            y -= 12
        y -= 6
    return y


def _draw_education_block(c, y, d):
    for ed in d["education"]:
        _text(c, MARGIN, y,
              f"{ed['degree']} {ed['field']}", "Helvetica-Bold", 10)
        _text(c, PAGE_W - MARGIN, y, f"{ed['start']} – {ed['end']}",
              "Helvetica", 9, HexColor("#666666"), anchor="right")
        y -= 13
        _text(c, MARGIN, y, ed["institution"], "Helvetica-Oblique", 9)
        # In _draw_education_block, after drawing the institution line:
        if ed.get("supervisor"):
            y = _draw_supervisor_line(c, MARGIN, y, ed["supervisor"])
        y -= 16
    return y

def _draw_exp_academic(c, y, d):
    for exp in d["experience"]:
        _text(c, MARGIN, y, f"{exp['title']}, {exp['company']}",
              "Times-Bold", 9)
        _text(c, PAGE_W - MARGIN, y, f"{exp['start']} – {exp['end']}",
              "Times-Italic", 9, anchor="right")
        y -= 12
        for b in exp["bullets"]:
            y = _wrap_text(c, MARGIN + 12, y, f"— {b}",
                           PAGE_W - 2 * MARGIN - 12, "Times-Roman", 9,
                           leading=11)
        y -= 4
    return y


def _draw_edu_academic(c, y, d):
    for ed in d["education"]:
        _text(c, MARGIN, y,
              f"{ed['degree']} {ed['field']}, {ed['institution']}",
              "Times-Bold", 9)
        _text(c, PAGE_W - MARGIN, y, f"{ed['start']} – {ed['end']}",
              "Times-Italic", 9, anchor="right")
        y -= 14
    return y


def _draw_exp_compact(c, y, d, m):
    for exp in d["experience"]:
        _text(c, m, y, exp["title"], "Helvetica-Bold", 8)
        _text(c, m + 180, y, exp["company"], "Helvetica", 8,
              HexColor("#555555"))
        _text(c, PAGE_W - m, y, f"{exp['start']} – {exp['end']}",
              "Helvetica", 7, HexColor("#888888"), anchor="right")
        y -= 10
        for b in exp["bullets"]:
            _text(c, m + 6, y, f"- {b}", "Helvetica", 7)
            y -= 9
        y -= 3
    return y


def _draw_edu_compact(c, y, d, m):
    for ed in d["education"]:
        _text(c, m, y, f"{ed['degree']} {ed['field']}", "Helvetica-Bold", 8)
        _text(c, m + 180, y, ed["institution"], "Helvetica", 8)
        _text(c, PAGE_W - m, y, f"{ed['start']} – {ed['end']}",
              "Helvetica", 7, HexColor("#888888"), anchor="right")
        y -= 12
    return y


def _format_author_list(authors: list[dict]) -> str:
    """Join author names as 'A, B and C'."""
    names = [f"{a['first']} {a['last']}" for a in authors]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f" and {names[-1]}"


def _draw_publications_block(c, y, d):
    if not d.get("publications"):
        return y
    for pub in d["publications"]:
        _text(c, MARGIN, y, pub["title"], "Helvetica-Bold", 9)
        _text(c, PAGE_W - MARGIN, y, str(pub["year"]), "Helvetica", 9,
              HexColor("#666666"), anchor="right")
        y -= 12
        authors = _format_author_list(
            [{"first": d["name"].split()[0], "last": d["name"].split()[-1]}]
            + pub["coauthors"]
        )
        _text(c, MARGIN, y, authors, "Helvetica-Oblique", 9,
              HexColor("#444444"))
        y -= 12
        _text(c, MARGIN, y, pub["venue"], "Helvetica", 9,
              HexColor("#666666"))
        y -= 14
    return y


def _draw_references_block(c, y, d):
    if not d.get("references"):
        return y
    for ref in d["references"]:
        _text(c, MARGIN, y, ref["name"], "Helvetica-Bold", 9)
        y -= 12
        _text(c, MARGIN, y, f"{ref['affiliation']} — {ref['email']}",
              "Helvetica", 9, HexColor("#555555"))
        y -= 14
    return y


def _draw_supervisor_line(c, x, y, supervisor):
    """Render 'PhD under the direction of Prof. X' as a single line."""
    _text(c, x, y,
          f"PhD under the direction of {supervisor['title']} "
          f"{supervisor['first']} {supervisor['last']}",
          "Helvetica-Oblique", 8, HexColor("#666666"))
    return y - 12

# ---------------------------------------------------------------------------
# Layout 1 – Classic Single-Column with Horizontal Rules
# ---------------------------------------------------------------------------

def layout_1_classic(c: canvas.Canvas, d: dict):
    y = PAGE_H - MARGIN
    _text(c, PAGE_W / 2, y, d["name"], "Helvetica-Bold", 22, anchor="center")
    y -= 18
    _text(c, PAGE_W / 2, y, d["title"], "Helvetica", 12,
          HexColor("#555555"), anchor="center")
    y -= 16
    _text(c, PAGE_W / 2, y,
          f"{d['email']}  |  {d['phone']}  |  {d['city']}, {d['country']}",
          "Helvetica", 8, HexColor("#777777"), anchor="center")
    y -= 20
    _line(c, MARGIN, y, PAGE_W - MARGIN, y, width=1)
    y -= 18

    for heading, body_fn in [
        ("Summary", lambda c, y: _wrap_text(c, MARGIN, y, d["summary"],
                                            PAGE_W - 2 * MARGIN)),
        ("Experience", lambda c, y: _draw_experience_block(c, y, d)),
        ("Education", lambda c, y: _draw_education_block(c, y, d)),
        ("Skills", lambda c, y: _wrap_text(c, MARGIN, y,
                                           ", ".join(d["skills"]),
                                           PAGE_W - 2 * MARGIN)),
        ("Publications", lambda c, y: _draw_publications_block(c, y, d)),
        ("References", lambda c, y: _draw_references_block(c, y, d)),
    ]:
        y = _section_heading(c, MARGIN, y, heading)
        y = body_fn(c, y)
        y -= 10
        _line(c, MARGIN, y, PAGE_W - MARGIN, y, HexColor("#CCCCCC"))
        y -= 14


# ---------------------------------------------------------------------------
# Layout 2 – Modern Two-Column (sidebar left)
# ---------------------------------------------------------------------------

def layout_2_two_column(c: canvas.Canvas, d: dict):
    side_w = 180
    accent = HexColor("#2C3E50")
    _rect(c, 0, 0, side_w, PAGE_H, fill=accent)

    sy = PAGE_H - MARGIN
    _text(c, side_w / 2, sy, d["name"], "Helvetica-Bold", 16, white,
          anchor="center")
    sy -= 16
    _text(c, side_w / 2, sy, d["title"], "Helvetica", 9,
          HexColor("#BDC3C7"), anchor="center")
    sy -= 30

    for label, value in [("Email", d["email"]), ("Phone", d["phone"]),
                         ("Location", f"{d['city']}, {d['country']}")]:
        _text(c, 15, sy, label.upper(), "Helvetica-Bold", 7,
              HexColor("#ECF0F1"))
        sy -= 11
        sy = _wrap_text(c, 15, sy, value, side_w - 30, "Helvetica", 8,
                        white, 11)
        sy -= 10

    sy -= 10
    _text(c, 15, sy, "SKILLS", "Helvetica-Bold", 9, HexColor("#ECF0F1"))
    sy -= 14
    for sk in d["skills"]:
        _text(c, 20, sy, f"▸ {sk}", "Helvetica", 8, white)
        sy -= 12

    sy -= 10
    _text(c, 15, sy, "LANGUAGES", "Helvetica-Bold", 9, HexColor("#ECF0F1"))
    sy -= 14
    for lg in d["languages"]:
        _text(c, 20, sy, f"{lg['lang']} – {lg['level']}", "Helvetica", 8,
              white)
        sy -= 12

    mx = side_w + 20
    mw = PAGE_W - mx - MARGIN
    my = PAGE_H - MARGIN
    my = _section_heading(c, mx, my, "Profile", color=accent)
    my = _wrap_text(c, mx, my, d["summary"], mw)
    my -= 14
    my = _section_heading(c, mx, my, "Experience", color=accent)
    for exp in d["experience"]:
        _text(c, mx, my, exp["title"], "Helvetica-Bold", 10)
        _text(c, PAGE_W - MARGIN, my, f"{exp['start']} – {exp['end']}",
              "Helvetica", 8, HexColor("#888888"), anchor="right")
        my -= 12
        _text(c, mx, my, exp["company"], "Helvetica-Oblique", 9,
              HexColor("#555555"))
        my -= 13
        for b in exp["bullets"]:
            my = _wrap_text(c, mx + 8, my, f"• {b}", mw - 8, "Helvetica", 8,
                            leading=11)
            my -= 2
        my -= 6
    my = _section_heading(c, mx, my, "Education", color=accent)
    for ed in d["education"]:
        _text(c, mx, my, f"{ed['degree']} {ed['field']}", "Helvetica-Bold", 10)
        my -= 12
        _text(c, mx, my, f"{ed['institution']}  ({ed['start']} – {ed['end']})",
              "Helvetica", 9, HexColor("#555555"))
        my -= 16


# ---------------------------------------------------------------------------
# Layout 3 – Minimal / Lots of Whitespace
# ---------------------------------------------------------------------------

def layout_3_minimal(c: canvas.Canvas, d: dict):
    y = PAGE_H - 60
    _text(c, MARGIN, y, d["name"], "Helvetica", 28, HexColor("#222222"))
    y -= 20
    _text(c, MARGIN, y, d["title"], "Helvetica", 12, HexColor("#999999"))
    y -= 30
    _text(c, MARGIN, y,
          f"{d['email']}   {d['phone']}   {d['linkedin']}",
          "Helvetica", 8, HexColor("#AAAAAA"))
    y -= 40

    sections = [
        ("About", lambda c, y: _wrap_text(c, MARGIN, y, d["summary"],
                                          PAGE_W - 2 * MARGIN, size=9,
                                          color=HexColor("#444444"),
                                          leading=14)),
        ("Work", lambda c, y: _draw_experience_block(c, y, d)),
        ("Education", lambda c, y: _draw_education_block(c, y, d)),
        ("Skills", lambda c, y: _wrap_text(c, MARGIN, y,
                                           "  ·  ".join(d["skills"]),
                                           PAGE_W - 2 * MARGIN, size=9)),
        ("Publications", lambda c, y: _draw_publications_block(c, y, d)),
        ("References", lambda c, y: _draw_references_block(c, y, d)),                                           
    ]
    for heading, fn in sections:
        _text(c, MARGIN, y, heading, "Helvetica-Bold", 10,
              HexColor("#BBBBBB"))
        y -= 18
        y = fn(c, y)
        y -= 24


# ---------------------------------------------------------------------------
# Layout 4 – Bold Coloured Header Block
# ---------------------------------------------------------------------------

def layout_4_bold_header(c: canvas.Canvas, d: dict):
    header_h = 120
    accent = HexColor("#E74C3C")
    _rect(c, 0, PAGE_H - header_h, PAGE_W, header_h, fill=accent)
    _text(c, MARGIN, PAGE_H - 50, d["name"], "Helvetica-Bold", 28, white)
    _text(c, MARGIN, PAGE_H - 72, d["title"], "Helvetica", 13,
          HexColor("#FADBD8"))
    _text(c, MARGIN, PAGE_H - 95,
          f"{d['email']}  |  {d['phone']}", "Helvetica", 9, white)

    y = PAGE_H - header_h - 25
    for heading, fn in [
        ("Summary", lambda c, y: _wrap_text(c, MARGIN, y, d["summary"],
                                            PAGE_W - 2 * MARGIN)),
        ("Experience", lambda c, y: _draw_experience_block(c, y, d)),
        ("Education", lambda c, y: _draw_education_block(c, y, d)),
        ("Skills", lambda c, y: _wrap_text(c, MARGIN, y,
                                           " | ".join(d["skills"]),
                                           PAGE_W - 2 * MARGIN)),
        ("Publications", lambda c, y: _draw_publications_block(c, y, d)),
        ("References", lambda c, y: _draw_references_block(c, y, d)),                                           
    ]:
        y = _section_heading(c, MARGIN, y, heading, color=accent)
        y = fn(c, y)
        y -= 12


# ---------------------------------------------------------------------------
# Layout 5 – Academic / Dense Serif-style
# ---------------------------------------------------------------------------

def layout_5_academic(c: canvas.Canvas, d: dict):
    y = PAGE_H - MARGIN
    _text(c, PAGE_W / 2, y, d["name"].upper(), "Times-Bold", 18,
          anchor="center")
    y -= 14
    _text(c, PAGE_W / 2, y, f"{d['city']}, {d['country']}", "Times-Roman", 9,
          HexColor("#333333"), anchor="center")
    y -= 12
    _text(c, PAGE_W / 2, y,
          f"Tel: {d['phone']}  ·  {d['email']}", "Times-Roman", 9,
          HexColor("#333333"), anchor="center")
    y -= 10
    _line(c, MARGIN, y, PAGE_W - MARGIN, y, width=1.5)
    y -= 16

    for heading, fn in [
        ("Research Interests", lambda c, y: _wrap_text(
            c, MARGIN, y, d["summary"], PAGE_W - 2 * MARGIN,
            "Times-Roman", 9, leading=12)),
        ("Professional Experience", lambda c, y: _draw_exp_academic(c, y, d)),
        ("Education", lambda c, y: _draw_edu_academic(c, y, d)),
        ("Skills & Competencies", lambda c, y: _wrap_text(
            c, MARGIN, y, ", ".join(d["skills"]),
            PAGE_W - 2 * MARGIN, "Times-Roman", 9, leading=12)),
        ("Certifications", lambda c, y: _wrap_text(
            c, MARGIN, y, ", ".join(d["certifications"]),
            PAGE_W - 2 * MARGIN, "Times-Roman", 9, leading=12)),
        ("Publications", lambda c, y: _draw_publications_block(c, y, d)),
        ("References", lambda c, y: _draw_references_block(c, y, d)),
    ]:
        _text(c, MARGIN, y, heading, "Times-Bold", 11)
        y -= 4
        _line(c, MARGIN, y, PAGE_W - MARGIN, y, width=0.5)
        y -= 12
        y = fn(c, y)
        y -= 10


# ---------------------------------------------------------------------------
# Layout 6 – Colour-Banded Sections
# ---------------------------------------------------------------------------

def layout_6_color_bands(c: canvas.Canvas, d: dict):
    bands = [
        ("#1ABC9C", "Profile", d["summary"]),
        ("#3498DB", "Experience", None),
        ("#9B59B6", "Education", None),
        ("#E67E22", "Skills", ", ".join(d["skills"])),
    ]
    y = PAGE_H - MARGIN
    _text(c, PAGE_W / 2, y, d["name"], "Helvetica-Bold", 24,
          HexColor("#2C3E50"), anchor="center")
    y -= 16
    _text(c, PAGE_W / 2, y,
          f"{d['title']}  ·  {d['email']}  ·  {d['phone']}",
          "Helvetica", 9, HexColor("#7F8C8D"), anchor="center")
    y -= 28

    for color, heading, body in bands:
        col = HexColor(color)
        _rect(c, MARGIN, y - 4, PAGE_W - 2 * MARGIN, 18, fill=col)
        _text(c, MARGIN + 8, y, heading.upper(), "Helvetica-Bold", 10, white)
        y -= 26
        if heading == "Experience":
            y = _draw_experience_block(c, y, d)
        elif heading == "Education":
            y = _draw_education_block(c, y, d)
        else:
            y = _wrap_text(c, MARGIN + 5, y, body, PAGE_W - 2 * MARGIN - 10)
        y -= 14


# ---------------------------------------------------------------------------
# Layout 7 – Table-Based Layout
# ---------------------------------------------------------------------------

def layout_7_table(c: canvas.Canvas, d: dict):
    y = PAGE_H - MARGIN
    _text(c, MARGIN, y, d["name"], "Helvetica-Bold", 20)
    y -= 14
    _text(c, MARGIN, y,
          f"{d['email']} | {d['phone']} | {d['city']}, {d['country']}",
          "Helvetica", 8, HexColor("#666666"))
    y -= 24

    _text(c, MARGIN, y, "EXPERIENCE", "Helvetica-Bold", 11)
    y -= 6
    _line(c, MARGIN, y, PAGE_W - MARGIN, y, width=1)
    y -= 14
    col_w = [130, 160, 80, PAGE_W - 2 * MARGIN - 370]
    headers = ["Position", "Company", "Dates", "Key Achievement"]
    x = MARGIN
    for i, h in enumerate(headers):
        _rect(c, x, y - 2, col_w[i], 14, fill=HexColor("#34495E"))
        _text(c, x + 4, y, h, "Helvetica-Bold", 8, white)
        x += col_w[i]
    y -= 18

    for exp in d["experience"]:
        x = MARGIN
        vals = [exp["title"], exp["company"],
                f"{exp['start']} – {exp['end']}",
                exp["bullets"][0][:50]]
        for i, v in enumerate(vals):
            _text(c, x + 3, y, v, "Helvetica", 7)
            _line(c, x, y - 4, x + col_w[i], y - 4, HexColor("#DDDDDD"))
            x += col_w[i]
        y -= 16

    y -= 10
    _text(c, MARGIN, y, "EDUCATION", "Helvetica-Bold", 11)
    y -= 6
    _line(c, MARGIN, y, PAGE_W - MARGIN, y, width=1)
    y -= 14
    for ed in d["education"]:
        _text(c, MARGIN, y, f"{ed['degree']} {ed['field']}", "Helvetica-Bold", 9)
        _text(c, MARGIN + 200, y, ed["institution"], "Helvetica", 9)
        _text(c, PAGE_W - MARGIN, y, f"{ed['start']} – {ed['end']}",
              "Helvetica", 8, HexColor("#888888"), anchor="right")
        y -= 16

    y -= 10
    _text(c, MARGIN, y, "SKILLS", "Helvetica-Bold", 11)
    y -= 14
    x = MARGIN
    for sk in d["skills"]:
        w = c.stringWidth(sk, "Helvetica", 9) + 16
        _rect(c, x, y - 2, w, 14, fill=HexColor("#ECF0F1"),
              stroke=HexColor("#BDC3C7"))
        _text(c, x + 8, y, sk, "Helvetica", 9)
        x += w + 6
        if x > PAGE_W - MARGIN - 60:
            x = MARGIN
            y -= 20


# ---------------------------------------------------------------------------
# Layout 8 – Timeline (dates on the left margin)
# ---------------------------------------------------------------------------

def layout_8_timeline(c: canvas.Canvas, d: dict):
    y = PAGE_H - MARGIN
    accent = HexColor("#27AE60")
    _text(c, PAGE_W / 2, y, d["name"], "Helvetica-Bold", 24, anchor="center")
    y -= 16
    _text(c, PAGE_W / 2, y,
          f"{d['title']}  ·  {d['email']}", "Helvetica", 10,
          HexColor("#777777"), anchor="center")
    y -= 30

    _text(c, MARGIN, y, "EXPERIENCE", "Helvetica-Bold", 12, accent)
    y -= 20
    timeline_x = MARGIN + 70
    _line(c, timeline_x, y + 10, timeline_x, y - 200, accent, 1.5)

    for exp in d["experience"]:
        _text(c, MARGIN, y, f"{exp['start']} – {exp['end']}",
              "Helvetica-Bold", 7, HexColor("#888888"))
        c.setFillColor(accent)
        c.circle(timeline_x, y + 3, 3, fill=1, stroke=0)
        _text(c, timeline_x + 12, y, exp["title"], "Helvetica-Bold", 10)
        y -= 12
        _text(c, timeline_x + 12, y, exp["company"], "Helvetica-Oblique", 9,
              HexColor("#555555"))
        y -= 13
        for b in exp["bullets"]:
            _text(c, timeline_x + 18, y, f"• {b}", "Helvetica", 8)
            y -= 11
        y -= 10

    y -= 6
    _text(c, MARGIN, y, "EDUCATION", "Helvetica-Bold", 12, accent)
    y -= 20
    for ed in d["education"]:
        _text(c, MARGIN, y, f"{ed['start']} – {ed['end']}",
              "Helvetica-Bold", 7, HexColor("#888888"))
        c.setFillColor(accent)
        c.circle(timeline_x, y + 3, 3, fill=1, stroke=0)
        _text(c, timeline_x + 12, y, f"{ed['degree']} {ed['field']}",
              "Helvetica-Bold", 10)
        y -= 12
        _text(c, timeline_x + 12, y, ed["institution"], "Helvetica", 9)
        y -= 18


# ---------------------------------------------------------------------------
# Layout 9 – Compact Professional (small margins, tight)
# ---------------------------------------------------------------------------

def layout_9_compact(c: canvas.Canvas, d: dict):
    m = 18 * mm
    y = PAGE_H - m
    _text(c, m, y, d["name"], "Helvetica-Bold", 16)
    _text(c, PAGE_W - m, y,
          f"{d['email']} | {d['phone']}", "Helvetica", 7,
          HexColor("#666666"), anchor="right")
    y -= 12
    _text(c, m, y, d["title"], "Helvetica", 10, HexColor("#444444"))
    y -= 8
    _line(c, m, y, PAGE_W - m, y, HexColor("#333333"), 1.2)
    y -= 12

    for heading, fn in [
        ("SUMMARY", lambda c, y: _wrap_text(c, m, y, d["summary"],
                                            PAGE_W - 2 * m, size=8,
                                            leading=10)),
        ("EXPERIENCE", lambda c, y: _draw_exp_compact(c, y, d, m)),
        ("EDUCATION", lambda c, y: _draw_edu_compact(c, y, d, m)),
        ("SKILLS", lambda c, y: _wrap_text(c, m, y,
                                           " · ".join(d["skills"]),
                                           PAGE_W - 2 * m, size=8)),
        ("CERTIFICATIONS", lambda c, y: _wrap_text(
            c, m, y, ", ".join(d["certifications"]),
            PAGE_W - 2 * m, size=8)),
        ("LANGUAGES", lambda c, y: _wrap_text(
            c, m, y,
            " | ".join(f"{l['lang']} ({l['level']})" for l in d["languages"]),
            PAGE_W - 2 * m, size=8)),
        ("Publications", lambda c, y: _draw_publications_block(c, y, d)),
        ("References", lambda c, y: _draw_references_block(c, y, d)),            
    ]:
        _text(c, m, y, heading, "Helvetica-Bold", 8, HexColor("#2C3E50"))
        y -= 3
        _line(c, m, y, PAGE_W - m, y, HexColor("#DDDDDD"), 0.4)
        y -= 10
        y = fn(c, y)
        y -= 8


# ---------------------------------------------------------------------------
# Layout 10 – Elegant Bordered Sections
# ---------------------------------------------------------------------------

def layout_10_bordered(c: canvas.Canvas, d: dict):
    y = PAGE_H - MARGIN
    border_col = HexColor("#8E44AD")

    box_h = 50
    _rect(c, MARGIN, y - box_h + 10, PAGE_W - 2 * MARGIN, box_h,
          stroke=border_col, width=1.5)
    _text(c, PAGE_W / 2, y - 10, d["name"], "Helvetica-Bold", 22,
          border_col, anchor="center")
    _text(c, PAGE_W / 2, y - 28,
          f"{d['title']}  |  {d['email']}  |  {d['phone']}",
          "Helvetica", 8, HexColor("#555555"), anchor="center")
    y -= box_h + 14

    sections = [
        ("Profile", lambda c, y: _wrap_text(c, MARGIN + 10, y, d["summary"],
                                            PAGE_W - 2 * MARGIN - 20,
                                            size=9)),
        ("Experience", lambda c, y: _draw_experience_block(c, y, d)),
        ("Education", lambda c, y: _draw_education_block(c, y, d)),
        ("Skills & Languages", lambda c, y: _wrap_text(
            c, MARGIN + 10, y,
            "Skills: " + ", ".join(d["skills"]) + "   |   Languages: " +
            ", ".join(f"{l['lang']} ({l['level']})" for l in d["languages"]),
            PAGE_W - 2 * MARGIN - 20, size=9)),
        ("Publications", lambda c, y: _draw_publications_block(c, y, d)),
        ("References", lambda c, y: _draw_references_block(c, y, d)),
    ]

    for heading, fn in sections:
        sec_h = 90 if heading != "Experience" else 160
        _rect(c, MARGIN, y - sec_h, PAGE_W - 2 * MARGIN, sec_h,
              stroke=HexColor("#D5D8DC"), width=0.6)
        _rect(c, MARGIN, y - 2, 100, 14, fill=border_col)
        _text(c, MARGIN + 6, y, heading.upper(), "Helvetica-Bold", 8, white)
        y -= 18
        y = fn(c, y)
        y -= 14

# ---------------------------------------------------------------------------
# Edge-case injection
# ---------------------------------------------------------------------------

# A second person's identity, used for supervisor / co-author / reference slots
SECOND_PERSON = [
    {"title": "Prof.", "first": "Margaret", "last": "Chen",
     "email": "m.chen@example.edu", "affiliation": "University of Washington"},
    {"title": "Dr.", "first": "Rajesh", "last": "Iyer",
     "email": "r.iyer@example.com", "affiliation": "Helix Biotech"},
    {"title": "Prof.", "first": "Ana", "last": "Oliveira",
     "email": "a.oliveira@example.edu", "affiliation": "Boston University"},
    {"title": "Dr.", "first": "Kwame", "last": "Mensah",
     "email": "k.mensah@example.com", "affiliation": "Northgate Pharmaceuticals"},
]

THIRD_PERSON = {
    "title": "Dr.",
    "first": "Rajesh",
    "last": "Iyer",
    "email": "r.iyer@example.com",
    "affiliation": "Helix Biotech",
}

VENUES = [
    # Computer science / ML
    "Conference on Neural Information Processing Systems",
    "International Conference on Machine Learning",
    "Annual Meeting of the Association for Computational Linguistics",
    "ACM SIGKDD Conference on Knowledge Discovery and Data Mining",
    "IEEE Conference on Computer Vision and Pattern Recognition",
    "International Joint Conference on Artificial Intelligence",
    "ACM Conference on Human Factors in Computing Systems",
    "USENIX Symposium on Operating Systems Design and Implementation",

    # Data science / statistics
    "Journal of Machine Learning Research",
    "Annals of Applied Statistics",
    "Pattern Recognition Letters",

    # Domain-specific (useful if your CVs span healthcare, biology, etc.)
    "Nature Methods",
    "Nature Biotechnology",
    "Journal of Clinical Oncology",
    "The Lancet Digital Health",
    "PLOS Computational Biology",

    # Engineering
    "IEEE Transactions on Software Engineering",
    "ACM Transactions on Computer-Human Interaction",
    "Journal of Mechanical Design",
]

# A name with diacritics, for offset-drift testing
DIACRITIC_NAME = "José García"

# A non-Latin name, for coverage of scripts the model may not have seen
NON_LATIN_NAME = "李 雷"

# A hyphenated surname, for tokenizer stress
HYPHENATED_NAME = "Martinez-Turner"

# A name that also appears as a company elsewhere
AMBIGUOUS_NAME = "Meridian"  # e.g. "Meridian Insurance" vs. a person named Meridian

def _apply_name_variant(data: dict, variant: str) -> None:
    """Apply a single name variant to `data`. Mutually exclusive by design."""
    if variant == "diacritics":
        data["name"] = DIACRITIC_NAME
        data["email"] = "jose.garcia@example.com"
        data["linkedin"] = "linkedin.com/in/jose-garcia"
    elif variant == "nonlatin":
        data["name"] = NON_LATIN_NAME
        data["email"] = "lei.li@example.com"
        data["linkedin"] = "linkedin.com/in/lei-li"
    elif variant == "hyphenated":
        first = _ascii_safe(fake.first_name())
        data["name"] = f"{first} {HYPHENATED_NAME}"
        data["email"] = f"{first.lower()}.{HYPHENATED_NAME.lower()}@example.com"
        data["linkedin"] = f"linkedin.com/in/{first.lower()}-{HYPHENATED_NAME.lower()}"
    # "none" → leave as-is


def inject_edge_cases(data: dict, *, profile: str = "none") -> dict:
    """
    Mutate `data` to include edge-case fields.

    Publications and references are ALWAYS populated. The profile only
    controls which edge-case variants get injected into them.
    """
    data = dict(data)
    data.setdefault("supervisor", None)

    # --- Publications: always present --------------------------------
    if profile in ("coauthor", "all"):
        coauthors = random.sample(SECOND_PERSON, k=min(2, len(SECOND_PERSON)))
    else:
        coauthors = [random.choice(SECOND_PERSON)]

    data["publications"] = [
        {
            "title": "A Scalable Approach to " + random.choice(
                ["Distributed Inference", "Data Pipeline Design",
                 "Model Compression", "Clinical Trial Analysis"]),
            "venue": random.choice(VENUES),
            "year": random.randint(2018, 2024),
            "coauthors": coauthors,
        }
        for _ in range(random.randint(1, 2))
    ]

    # --- References: always present ----------------------------------
    referee = random.choice(SECOND_PERSON)
    data["references"] = [{
        "name": f"{referee['title']} {referee['first']} {referee['last']}",
        "email": referee["email"],
        "affiliation": referee["affiliation"],
    }]
    if profile in ("references", "all"):
        data["references"].append({
            "name": f"{THIRD_PERSON['title']} {THIRD_PERSON['first']} "
                    f"{THIRD_PERSON['last']}",
            "email": THIRD_PERSON["email"],
            "affiliation": THIRD_PERSON["affiliation"],
        })

    # --- Supervisor (still optional) ---------------------------------
    if profile in ("supervisor", "all"):
        supervisor = random.choice(SECOND_PERSON)
        data["supervisor"] = supervisor
        if data["education"]:
            data["education"][0]["supervisor"] = supervisor

    # --- Name variants -----------------------------------------------
    # Name variant — exactly one, chosen by profile
    if profile in ("diacritics", "nonlatin", "hyphenated"):
        _apply_name_variant(data, profile)
    elif profile == "all":
        # "all" means: pick one variant at random for this CV
        _apply_name_variant(data, random.choice(["diacritics", "nonlatin", "hyphenated"]))
    
    return data

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

LAYOUTS = [
    ("01_classic_single_column", layout_1_classic, "none"),
    ("02_modern_two_column", layout_2_two_column, "supervisor"),
    ("03_minimal_whitespace", layout_3_minimal, "none"),
    ("04_bold_header", layout_4_bold_header, "coauthor"),
    ("05_academic_dense", layout_5_academic, "all"),
    ("06_color_bands", layout_6_color_bands, "references"),
    ("07_table_based", layout_7_table, "diacritics"),
    ("08_timeline", layout_8_timeline, "hyphenated"),
    ("09_compact_professional", layout_9_compact, "diacritics"),
    ("10_elegant_bordered", layout_10_bordered, "supervisor"),
]

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for name, layout_fn, profile in LAYOUTS:
        data = generate_cv_data()
        data = inject_edge_cases(data, profile=profile)
        path = os.path.join(OUTPUT_DIR, f"CV_{name}.pdf")
        c = canvas.Canvas(path, pagesize=A4)
        c.setTitle(f"Fake CV – {data['name']}")
        c.setAuthor("CV Generator Script")
        layout_fn(c, data)
        c.showPage()
        c.save()
        print(f"✓  {path}  ({data['name']})  [profile={profile}]")
    print(f"\nDone – {len(LAYOUTS)} CVs written to '{OUTPUT_DIR}/'")



if __name__ == "__main__":
    main()