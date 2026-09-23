#!/usr/bin/env python3
"""
Generate 10 fake CVs with different layouts for text extraction testing.

Dependencies:
    pip install faker fpdf2

Usage:
    python generate_cvs.py

Output:
    ./fake_cvs/cv_01_classic.pdf
    ./fake_cvs/cv_02_left_sidebar.pdf
    ...
"""

import os
import random
from faker import Faker
from fpdf import FPDF

fake = Faker()
Faker.seed(42)
random.seed(42)

OUTPUT_DIR = "fake_cvs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────
#  DATA GENERATION
# ──────────────────────────────────────────────

def generate_cv_data():
    """Generate realistic fake CV data."""
    first = fake.first_name()
    last = fake.last_name()

    data = {
        "name": f"{first} {last}",
        "title": fake.job(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "address": fake.address().replace("\n", ", "),
        "linkedin": f"linkedin.com/in/{first.lower()}{last.lower()}",
        "summary": fake.paragraph(nb_sentences=4),
        "experience": [],
        "education": [],
        "skills": [],
        "languages": [],
        "certifications": [],
    }

    for _ in range(random.randint(3, 4)):
        end = "Present" if random.random() > 0.3 else fake.date_between(
            start_date="-2y", end_date="today").strftime("%b %Y")
        data["experience"].append({
            "company": fake.company(),
            "title": fake.job(),
            "start": fake.date_between(start_date="-15y", end_date="-2y").strftime("%b %Y"),
            "end": end,
            "bullets": [fake.sentence(nb_words=random.randint(8, 15))
                        for _ in range(random.randint(3, 5))],
        })

    degrees = ["B.Sc.", "M.Sc.", "B.A.", "MBA", "Ph.D."]
    fields = ["Computer Science", "Engineering", "Business Administration",
              "Mathematics", "Data Science", "Economics"]
    for _ in range(random.randint(2, 3)):
        data["education"].append({
            "degree": f"{random.choice(degrees)} in {random.choice(fields)}",
            "institution": f"{fake.last_name()} University",
            "year": str(fake.date_between(start_date="-20y", end_date="-1y").year),
            "gpa": f"{random.uniform(3.0, 4.0):.2f}",
        })

    pool = ["Python", "JavaScript", "SQL", "Machine Learning", "Data Analysis",
            "Project Management", "AWS", "Docker", "Git", "React", "Node.js",
            "TensorFlow", "Tableau", "Excel", "Agile", "Scrum", "REST APIs",
            "Linux", "Java", "C++", "Communication", "Leadership"]
    data["skills"] = random.sample(pool, random.randint(8, 12))

    data["languages"] = [
        {"lang": "English", "level": "Native"},
        {"lang": random.choice(["Spanish", "French", "German", "Mandarin"]),
         "level": random.choice(["Fluent", "Intermediate", "Conversational"])},
    ]

    certs = ["AWS Solutions Architect", "PMP", "Google Data Analytics",
             "Certified Scrum Master", "Cisco CCNA"]
    data["certifications"] = random.sample(certs, random.randint(1, 3))

    return data


# ──────────────────────────────────────────────
#  HELPER: base PDF class
# ──────────────────────────────────────────────

class BaseCV(FPDF):
    def __init__(self, data, **kw):
        super().__init__(**kw)
        self.d = data
        self.set_auto_page_break(auto=True, margin=15)

    def section_title(self, title):
        """Override per layout."""
        raise NotImplementedError

    def build(self):
        raise NotImplementedError


# ──────────────────────────────────────────────
#  LAYOUT 1 – Classic single-column
# ──────────────────────────────────────────────

class Layout01Classic(BaseCV):
    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(0, 51, 102)
        self.cell(0, 8, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 51, 102)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def build(self):
        self.add_page()
        d = self.d
        # Name
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(0, 0, 0)
        self.cell(0, 12, d["name"], align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 11)
        self.set_text_color(80, 80, 80)
        self.cell(0, 6, d["title"], align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        contact = f"{d['email']}  |  {d['phone']}  |  {d['address']}"
        self.cell(0, 6, contact, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

        self.section_title("Professional Summary")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, d["summary"])
        self.ln(4)

        self.section_title("Work Experience")
        for exp in d["experience"]:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(0, 0, 0)
            self.cell(0, 6, f"{exp['title']}  —  {exp['company']}", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, f"{exp['start']} – {exp['end']}", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 10)
            self.set_text_color(30, 30, 30)
            for b in exp["bullets"]:
                self.cell(5)
                self.multi_cell(0, 5, f"• {b}")
            self.ln(3)

        self.section_title("Education")
        for ed in d["education"]:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(0, 0, 0)
            self.cell(0, 6, f"{ed['degree']}  —  {ed['institution']}", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, f"Graduated {ed['year']}  |  GPA: {ed['gpa']}", new_x="LMARGIN", new_y="NEXT")
            self.ln(2)

        self.section_title("Skills")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, "  |  ".join(d["skills"]))
        self.ln(4)

        self.section_title("Certifications")
        for c in d["certifications"]:
            self.cell(5)
            self.multi_cell(0, 5, f"• {c}")


# ──────────────────────────────────────────────
#  LAYOUT 2 – Left sidebar (coloured)
# ──────────────────────────────────────────────

class Layout02LeftSidebar(BaseCV):
    SIDEBAR_W = 65
    MAIN_X = 75

    def section_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.cell(0, 7, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def section_title_main(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(0, 51, 102)
        self.cell(0, 8, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 51, 102)
        self.line(self.get_x(), self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def build(self):
        self.add_page()
        d = self.d
        sw = self.SIDEBAR_W

        # Sidebar background
        self.set_fill_color(44, 62, 80)
        self.rect(0, 0, sw, 297, "F")

        # Sidebar content
        self.set_xy(8, 15)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.multi_cell(sw - 16, 8, d["name"], align="C")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(200, 200, 200)
        self.multi_cell(sw - 16, 5, d["title"], align="C")
        self.ln(8)

        self.set_x(8)
        self.section_title("Contact")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(220, 220, 220)
        for line in [d["email"], d["phone"], d["address"], d["linkedin"]]:
            self.set_x(8)
            self.multi_cell(sw - 16, 4, line)
            self.ln(1)

        self.set_x(8)
        self.ln(4)
        self.section_title("Skills")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(220, 220, 220)
        for s in d["skills"]:
            self.set_x(8)
            self.cell(sw - 16, 5, f"▸ {s}", new_x="LMARGIN", new_y="NEXT")

        self.set_x(8)
        self.ln(4)
        self.section_title("Languages")
        self.set_font("Helvetica", "", 8)
        for lg in d["languages"]:
            self.set_x(8)
            self.cell(sw - 16, 5, f"{lg['lang']} – {lg['level']}", new_x="LMARGIN", new_y="NEXT")

        # Main area
        self.set_xy(self.MAIN_X, 15)
        self.section_title_main("Profile")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(self.w - self.MAIN_X - self.r_margin, 5, d["summary"])
        self.ln(5)

        self.set_x(self.MAIN_X)
        self.section_title_main("Experience")
        for exp in d["experience"]:
            self.set_x(self.MAIN_X)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(0, 0, 0)
            self.cell(0, 6, exp["title"], new_x="LMARGIN", new_y="NEXT")
            self.set_x(self.MAIN_X)
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, f"{exp['company']}  |  {exp['start']} – {exp['end']}",
                      new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(30, 30, 30)
            for b in exp["bullets"]:
                self.set_x(self.MAIN_X + 3)
                self.multi_cell(self.w - self.MAIN_X - self.r_margin - 3, 5, f"• {b}")
            self.ln(2)

        self.set_x(self.MAIN_X)
        self.section_title_main("Education")
        for ed in d["education"]:
            self.set_x(self.MAIN_X)
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(0, 0, 0)
            self.cell(0, 6, ed["degree"], new_x="LMARGIN", new_y="NEXT")
            self.set_x(self.MAIN_X)
            self.set_font("Helvetica", "", 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, f"{ed['institution']}  |  {ed['year']}  |  GPA {ed['gpa']}",
                      new_x="LMARGIN", new_y="NEXT")
            self.ln(2)


# ──────────────────────────────────────────────
#  LAYOUT 3 – Right sidebar
# ──────────────────────────────────────────────

class Layout03RightSidebar(BaseCV):
    SIDEBAR_W = 65

    def build(self):
        self.add_page()
        d = self.d
        main_w = self.w - self.SIDEBAR_W - 10
        sx = self.w - self.SIDEBAR_W

        # Sidebar bg
        self.set_fill_color(52, 73, 94)
        self.rect(sx, 0, self.SIDEBAR_W, 297, "F")

        # Main – name
        self.set_xy(15, 15)
        self.set_font("Times", "B", 24)
        self.set_text_color(52, 73, 94)
        self.cell(main_w, 12, d["name"], new_x="LMARGIN", new_y="NEXT")
        self.set_xy(15, self.get_y())
        self.set_font("Times", "I", 12)
        self.set_text_color(100, 100, 100)
        self.cell(main_w, 7, d["title"], new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

        def main_heading(t):
            self.set_x(15)
            self.set_font("Times", "B", 12)
            self.set_text_color(52, 73, 94)
            self.cell(main_w, 7, t.upper(), new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(52, 73, 94)
            self.line(15, self.get_y(), 15 + main_w, self.get_y())
            self.ln(2)

        main_heading("Summary")
        self.set_x(15)
        self.set_font("Times", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(main_w, 5, d["summary"])
        self.ln(4)

        main_heading("Experience")
        for exp in d["experience"]:
            self.set_x(15)
            self.set_font("Times", "B", 10)
            self.set_text_color(0, 0, 0)
            self.cell(main_w, 6, f"{exp['title']}, {exp['company']}", new_x="LMARGIN", new_y="NEXT")
            self.set_x(15)
            self.set_font("Times", "I", 9)
            self.set_text_color(120, 120, 120)
            self.cell(main_w, 5, f"{exp['start']} – {exp['end']}", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Times", "", 9)
            self.set_text_color(30, 30, 30)
            for b in exp["bullets"]:
                self.set_x(18)
                self.multi_cell(main_w - 3, 5, f"- {b}")
            self.ln(2)

        main_heading("Education")
        for ed in d["education"]:
            self.set_x(15)
            self.set_font("Times", "B", 10)
            self.set_text_color(0, 0, 0)
            self.cell(main_w, 6, ed["degree"], new_x="LMARGIN", new_y="NEXT")
            self.set_x(15)
            self.set_font("Times", "", 9)
            self.set_text_color(100, 100, 100)
            self.cell(main_w, 5, f"{ed['institution']} ({ed['year']})", new_x="LMARGIN", new_y="NEXT")
            self.ln(2)

        # Right sidebar
        y = 15
        self.set_xy(sx + 5, y)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.cell(self.SIDEBAR_W - 10, 7, "CONTACT", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(210, 210, 210)
        for c in [d["email"], d["phone"], d["address"], d["linkedin"]]:
            self.set_x(sx + 5)
            self.multi_cell(self.SIDEBAR_W - 10, 4, c)
            self.ln(1)

        self.set_x(sx + 5)
        self.ln(5)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.cell(self.SIDEBAR_W - 10, 7, "SKILLS", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(210, 210, 210)
        for s in d["skills"]:
            self.set_x(sx + 5)
            self.cell(self.SIDEBAR_W - 10, 5, f"• {s}", new_x="LMARGIN", new_y="NEXT")

        self.set_x(sx + 5)
        self.ln(5)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.cell(self.SIDEBAR_W - 10, 7, "LANGUAGES", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        for lg in d["languages"]:
            self.set_x(sx + 5)
            self.cell(self.SIDEBAR_W - 10, 5, f"{lg['lang']} ({lg['level']})",
                      new_x="LMARGIN", new_y="NEXT")

        self.set_x(sx + 5)
        self.ln(5)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.cell(self.SIDEBAR_W - 10, 7, "CERTIFICATIONS", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        for c in d["certifications"]:
            self.set_x(sx + 5)
            self.multi_cell(self.SIDEBAR_W - 10, 4, f"• {c}")


# ──────────────────────────────────────────────
#  LAYOUT 4 – Modern coloured header bar
# ──────────────────────────────────────────────

class Layout04ModernHeader(BaseCV):
    def section_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(39, 174, 96)
        self.cell(0, 8, title.upper(), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(39, 174, 96)
        self.set_line_width(0.8)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_line_width(0.2)
        self.ln(3)

    def build(self):
        self.add_page()
        d = self.d

        # Big green header
        self.set_fill_color(39, 174, 96)
        self.rect(0, 0, 210, 50, "F")
        self.set_xy(15, 12)
        self.set_font("Helvetica", "B", 26)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, d["name"], new_x="LMARGIN", new_y="NEXT")
        self.set_x(15)
        self.set_font("Helvetica", "", 12)
        self.cell(0, 8, d["title"], new_x="LMARGIN", new_y="NEXT")

        self.set_y(55)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(80, 80, 80)
        self.cell(0, 5, f"{d['email']}   |   {d['phone']}   |   {d['linkedin']}",
                  align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

        self.section_title("About Me")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, d["summary"])
        self.ln(4)

        self.section_title("Experience")
        for exp in d["experience"]:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(0, 0, 0)
            self.cell(120, 6, exp["title"], new_x="RIGHT")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 6, f"{exp['start']} – {exp['end']}", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "I", 10)
            self.set_text_color(39, 174, 96)
            self.cell(0, 5, exp["company"], new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(30, 30, 30)
            for b in exp["bullets"]:
                self.cell(5)
                self.multi_cell(0, 5, f"• {b}")
            self.ln(3)

        self.section_title("Education")
        for ed in d["education"]:
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(0, 0, 0)
            self.cell(120, 6, ed["degree"], new_x="RIGHT")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(100, 100, 100)
            self.cell(0, 6, ed["year"], new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 9)
            self.set_text_color(30, 30, 30)
            self.cell(0, 5, f"{ed['institution']}  |  GPA: {ed['gpa']}", new_x="LMARGIN", new_y="NEXT")
            self.ln(2)

        self.section_title("Skills & Certifications")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, "Skills: " + ", ".join(d["skills"]))
        self.ln(2)
        self.multi_cell(0, 5, "Certifications: " + ", ".join(d["certifications"]))


# ──────────────────────────────────────────────
#  LAYOUT 5 – Minimalist (Courier, thin lines)
# ──────────────────────────────────────────────

class Layout05Minimalist(BaseCV):
    def section_title(self, title):
        self.set_font("Courier", "B", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(180, 180, 180)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def build(self):
        self.add_page()
        d = self.d

        self.set_font("Courier", "B", 18)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, d["name"], new_x="LMARGIN", new_y="NEXT")
        self.set_font("Courier", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, d["title"], new_x="LMARGIN", new_y="NEXT")
        self.set_font("Courier", "", 8)
        self.cell(0, 5, f"{d['email']}  /  {d['phone']}  /  {d['address']}",
                  new_x="LMARGIN", new_y="NEXT")
        self.ln(8)

        self.section_title("summary")
        self.set_font("Courier", "", 9)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5, d["summary"])
        self.ln(5)

        self.section_title("experience")
        for exp in d["experience"]:
            self.set_font("Courier", "B", 9)
            self.set_text_color(0, 0, 0)
            self.cell(0, 5, f"{exp['title']} @ {exp['company']}", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Courier", "", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 5, f"{exp['start']} - {exp['end']}", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Courier", "", 8)
            self.set_text_color(40, 40, 40)
            for b in exp["bullets"]:
                self.cell(4)
                self.multi_cell(0, 4, f"- {b}")
            self.ln(3)

        self.section_title("education")
        for ed in d["education"]:
            self.set_font("Courier", "B", 9)
            self.set_text_color(0, 0, 0)
            self.cell(0, 5, ed["degree"], new_x="LMARGIN", new_y="NEXT")
            self.set_font("Courier", "", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 5, f"{ed['institution']}, {ed['year']}, GPA {ed['gpa']}",
                      new_x="LMARGIN", new_y="NEXT")
            self.ln(2)

        self.section_title("skills")
        self.set_font("Courier", "", 9)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5, ", ".join(d["skills"]))
        self.ln(3)

        self.section_title("languages")
        for lg in d["languages"]:
            self.cell(4)
            self.multi_cell(0, 5, f"{lg['lang']} ({lg['level']})")


# ──────────────────────────────────────────────
#  LAYOUT 6 – Two equal columns
# ──────────────────────────────────────────────

class Layout06TwoColumns(BaseCV):
    def build(self):
        self.add_page()
        d = self.d
        col_w = (self.w - self.l_margin - self.r_margin - 10) / 2
        lx = self.l_margin
        rx = lx + col_w + 10

        # Full-width header
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, d["name"], align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f"{d['title']}  |  {d['email']}  |  {d['phone']}",
                  align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_draw_color(0, 0, 0)
        self.line(lx, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)

        def heading(x, title):
            self.set_x(x)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(128, 0, 0)
            self.cell(col_w, 7, title.upper(), new_x="LMARGIN", new_y="NEXT")
            self.ln(1)

        # LEFT column: Education + Skills + Languages
        y_start = self.get_y()
        heading(lx, "Education")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        for ed in d["education"]:
            self.set_x(lx)
            self.set_font("Helvetica", "B", 9)
            self.multi_cell(col_w, 5, ed["degree"])
            self.set_x(lx)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(100, 100, 100)
            self.multi_cell(col_w, 4, f"{ed['institution']} ({ed['year']}) GPA: {ed['gpa']}")
            self.ln(2)

        self.set_y(self.get_y() + 3)
        heading(lx, "Skills")
        self.set_x(lx)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        for s in d["skills"]:
            self.set_x(lx)
            self.cell(col_w, 5, f"• {s}", new_x="LMARGIN", new_y="NEXT")

        self.ln(3)
        heading(lx, "Languages")
        self.set_font("Helvetica", "", 9)
        for lg in d["languages"]:
            self.set_x(lx)
            self.cell(col_w, 5, f"{lg['lang']} – {lg['level']}", new_x="LMARGIN", new_y="NEXT")

        self.ln(3)
        heading(lx, "Certifications")
        self.set_font("Helvetica", "", 9)
        for c in d["certifications"]:
            self.set_x(lx)
            self.multi_cell(col_w, 5, f"• {c}")

        # RIGHT column: Experience
        self.set_xy(rx, y_start)
        heading(rx, "Experience")
        for exp in d["experience"]:
            self.set_x(rx)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(0, 0, 0)
            self.multi_cell(col_w, 5, exp["title"])
            self.set_x(rx)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(col_w, 4, f"{exp['company']}", new_x="LMARGIN", new_y="NEXT")
            self.set_x(rx)
            self.cell(col_w, 4, f"{exp['start']} – {exp['end']}", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 8)
            self.set_text_color(30, 30, 30)
            for b in exp["bullets"]:
                self.set_x(rx + 2)
                self.multi_cell(col_w - 2, 4, f"• {b}")
            self.ln(2)

        # Summary at bottom full width
        self.set_y(max(self.get_y(), self.get_y()) + 5)
        self.set_x(lx)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(128, 0, 0)
        self.cell(0, 7, "PROFILE", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, d["summary"])


# ──────────────────────────────────────────────
#  LAYOUT 7 – Table / grid based
# ──────────────────────────────────────────────

class Layout07TableGrid(BaseCV):
    def build(self):
        self.add_page()
        d = self.d
        w = self.w - self.l_margin - self.r_margin

        self.set_font("Helvetica", "B", 20)
        self.set_text_color(0, 0, 0)
        self.cell(0, 12, d["name"], align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 6, d["title"], align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

        # Contact table
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(70, 70, 70)
        self.cell(w, 7, "CONTACT INFORMATION", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(0, 0, 0)
        labels = ["Email", "Phone", "Address", "LinkedIn"]
        values = [d["email"], d["phone"], d["address"], d["linkedin"]]
        for lbl, val in zip(labels, values):
            self.set_fill_color(230, 230, 230)
            self.cell(40, 6, lbl, border=1, fill=True)
            self.set_fill_color(255, 255, 255)
            self.cell(w - 40, 6, val, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

        # Summary table
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(70, 70, 70)
        self.cell(w, 7, "PROFESSIONAL SUMMARY", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(0, 0, 0)
        self.multi_cell(w, 5, d["summary"], border=1)
        self.ln(5)

        # Experience table
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(70, 70, 70)
        self.cell(w, 7, "WORK EXPERIENCE", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(0, 0, 0)
        self.set_fill_color(220, 220, 220)
        self.cell(w * 0.35, 6, "Position / Company", border=1, fill=True)
        self.cell(w * 0.25, 6, "Dates", border=1, fill=True)
        self.cell(w * 0.40, 6, "Key Responsibilities", border=1, fill=True,
                  new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        for exp in d["experience"]:
            h = max(len(exp["bullets"]) * 5, 15)
            y0 = self.get_y()
            x0 = self.get_x()
            self.multi_cell(w * 0.35, 5, f"{exp['title']}\n{exp['company']}", border=1)
            self.set_xy(x0 + w * 0.35, y0)
            self.multi_cell(w * 0.25, 5, f"{exp['start']}\n– {exp['end']}", border=1)
            self.set_xy(x0 + w * 0.60, y0)
            bullets_text = "\n".join(f"• {b}" for b in exp["bullets"])
            self.multi_cell(w * 0.40, 5, bullets_text, border=1)
        self.ln(5)

        # Education table
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(70, 70, 70)
        self.cell(w, 7, "EDUCATION", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(0, 0, 0)
        self.set_fill_color(220, 220, 220)
        self.cell(w * 0.45, 6, "Degree", border=1, fill=True)
        self.cell(w * 0.35, 6, "Institution", border=1, fill=True)
        self.cell(w * 0.20, 6, "Year / GPA", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 8)
        for ed in d["education"]:
            self.cell(w * 0.45, 6, ed["degree"], border=1)
            self.cell(w * 0.35, 6, ed["institution"], border=1)
            self.cell(w * 0.20, 6, f"{ed['year']} / {ed['gpa']}", border=1,
                      new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

        # Skills table
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(70, 70, 70)
        self.cell(w, 7, "SKILLS & CERTIFICATIONS", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(0, 0, 0)
        self.multi_cell(w, 5, "Skills: " + ", ".join(d["skills"]), border=1)
        self.multi_cell(w, 5, "Certifications: " + ", ".join(d["certifications"]), border=1)


# ──────────────────────────────────────────────
#  LAYOUT 8 – Academic style (education first)
# ──────────────────────────────────────────────

class Layout08Academic(BaseCV):
    def section_title(self, title):
        self.set_font("Times", "B", 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.5)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.set_line_width(0.2)
        self.ln(3)

    def build(self):
        self.add_page()
        d = self.d

        self.set_font("Times", "B", 20)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, d["name"], align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Times", "", 11)
        self.cell(0, 6, d["address"], align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 6, f"{d['email']}  |  {d['phone']}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

        self.section_title("Education")
        for ed in d["education"]:
            self.set_font("Times", "B", 11)
            self.cell(130, 6, ed["degree"], new_x="RIGHT")
            self.set_font("Times", "", 10)
            self.cell(0, 6, ed["year"], new_x="LMARGIN", new_y="NEXT")
            self.set_font("Times", "I", 10)
            self.cell(0, 5, ed["institution"], new_x="LMARGIN", new_y="NEXT")
            self.set_font("Times", "", 10)
            self.cell(0, 5, f"GPA: {ed['gpa']}", new_x="LMARGIN", new_y="NEXT")
            self.ln(2)

        self.section_title("Professional Experience")
        for exp in d["experience"]:
            self.set_font("Times", "B", 11)
            self.cell(130, 6, exp["title"], new_x="RIGHT")
            self.set_font("Times", "", 10)
            self.cell(0, 6, f"{exp['start']} – {exp['end']}", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Times", "I", 10)
            self.cell(0, 5, exp["company"], new_x="LMARGIN", new_y="NEXT")
            self.set_font("Times", "", 10)
            for b in exp["bullets"]:
                self.cell(8)
                self.multi_cell(0, 5, f"– {b}")
            self.ln(2)

        self.section_title("Research Interests & Summary")
        self.set_font("Times", "", 10)
        self.multi_cell(0, 5, d["summary"])
        self.ln(4)

        self.section_title("Skills")
        self.set_font("Times", "", 10)
        self.multi_cell(0, 5, ", ".join(d["skills"]))
        self.ln(4)

        self.section_title("Languages")
        for lg in d["languages"]:
            self.cell(8)
            self.cell(0, 5, f"{lg['lang']} ({lg['level']})", new_x="LMARGIN", new_y="NEXT")

        self.ln(3)
        self.section_title("Certifications")
        for c in d["certifications"]:
            self.cell(8)
            self.cell(0, 5, c, new_x="LMARGIN", new_y="NEXT")


# ──────────────────────────────────────────────
#  LAYOUT 9 – Compact / dense
# ──────────────────────────────────────────────

class Layout09Compact(BaseCV):
    def __init__(self, data):
        super().__init__(data, format="A4")
        self.set_margins(10, 10, 10)

    def section_title(self, title):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(50, 50, 50)
        self.cell(0, 5, f"  {title.upper()}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def build(self):
        self.add_page()
        d = self.d

        self.set_font("Helvetica", "B", 14)
        self.set_text_color(0, 0, 0)
        self.cell(0, 7, d["name"], new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(80, 80, 80)
        self.cell(0, 4, f"{d['title']} | {d['email']} | {d['phone']} | {d['linkedin']}",
                  new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

        self.section_title("Summary")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 3.5, d["summary"])
        self.ln(1)

        self.section_title("Experience")
        for exp in d["experience"]:
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(0, 0, 0)
            self.cell(100, 4, f"{exp['title']} – {exp['company']}", new_x="RIGHT")
            self.set_font("Helvetica", "", 7)
            self.set_text_color(100, 100, 100)
            self.cell(0, 4, f"{exp['start']}–{exp['end']}", new_x="LMARGIN", new_y="NEXT")
            self.set_font("Helvetica", "", 7)
            self.set_text_color(30, 30, 30)
            for b in exp["bullets"]:
                self.cell(3)
                self.multi_cell(0, 3.5, f"• {b}")
            self.ln(1)

        self.section_title("Education")
        for ed in d["education"]:
            self.set_font("Helvetica", "B", 7)
            self.set_text_color(0, 0, 0)
            self.cell(100, 4, ed["degree"], new_x="RIGHT")
            self.set_font("Helvetica", "", 7)
            self.set_text_color(100, 100, 100)
            self.cell(0, 4, f"{ed['institution']} ({ed['year']}) GPA:{ed['gpa']}",
                      new_x="LMARGIN", new_y="NEXT")

        self.ln(1)
        self.section_title("Skills")
        self.set_font("Helvetica", "", 7)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 3.5, " | ".join(d["skills"]))
        self.ln(1)

        self.section_title("Certifications & Languages")
        self.multi_cell(0, 3.5, "Certs: " + ", ".join(d["certifications"]))
        langs = ", ".join(f"{lg['lang']} ({lg['level']})" for lg in d["languages"])
        self.multi_cell(0, 3.5, f"Languages: {langs}")


# ──────────────────────────────────────────────
#  LAYOUT 10 – Boxed sections
# ──────────────────────────────────────────────

class Layout10Boxed(BaseCV):
    def section_box(self, title, content_fn):
        x0 = self.l_margin
        w = self.w - self.l_margin - self.r_margin
        y0 = self.get_y()

        # Estimate height by running content in a dry-ish way
        # We'll just draw after
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(41, 128, 185)
        self.cell(w, 8, f"  {title.upper()}", fill=True, new_x="LMARGIN", new_y="NEXT")

        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        content_fn()
        self.ln(2)

        y1 = self.get_y()
        # Draw border around whole section
        self.set_draw_color(41, 128, 185)
        self.set_line_width(0.6)
        self.rect(x0, y0, w, y1 - y0)
        self.set_line_width(0.2)
        self.ln(4)

    def build(self):
        self.add_page()
        d = self.d
        w = self.w - self.l_margin - self.r_margin

        # Name box
        self.set_fill_color(41, 128, 185)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 22)
        self.cell(w, 14, d["name"], align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 11)
        self.cell(w, 8, d["title"], align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.cell(w, 6, f"{d['email']}  |  {d['phone']}  |  {d['address']}",
                  align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

        def summary_content():
            self.multi_cell(w - 4, 5, d["summary"])

        self.section_box("Professional Summary", summary_content)

        def exp_content():
            for exp in d["experience"]:
                self.set_font("Helvetica", "B", 10)
                self.set_text_color(0, 0, 0)
                self.cell(0, 6, f"{exp['title']}  @  {exp['company']}",
                          new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(120, 120, 120)
                self.cell(0, 5, f"{exp['start']} – {exp['end']}", new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", "", 9)
                self.set_text_color(30, 30, 30)
                for b in exp["bullets"]:
                    self.cell(4)
                    self.multi_cell(w - 8, 5, f"• {b}")
                self.ln(2)

        self.section_box("Work Experience", exp_content)

        def edu_content():
            for ed in d["education"]:
                self.set_font("Helvetica", "B", 9)
                self.set_text_color(0, 0, 0)
                self.cell(0, 5, f"{ed['degree']} – {ed['institution']} ({ed['year']})",
                          new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", "", 9)
                self.set_text_color(100, 100, 100)
                self.cell(0, 5, f"GPA: {ed['gpa']}", new_x="LMARGIN", new_y="NEXT")
                self.ln(1)

        self.section_box("Education", edu_content)

        def skills_content():
            self.set_font("Helvetica", "", 9)
            self.set_text_color(30, 30, 30)
            self.multi_cell(w - 4, 5, "Skills: " + ", ".join(d["skills"]))
            self.ln(1)
            self.multi_cell(w - 4, 5, "Certifications: " + ", ".join(d["certifications"]))
            self.ln(1)
            langs = " | ".join(f"{lg['lang']} ({lg['level']})" for lg in d["languages"])
            self.multi_cell(w - 4, 5, f"Languages: {langs}")

        self.section_box("Skills & Certifications", skills_content)


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────

LAYOUTS = [
    ("01_classic",        Layout01Classic),
    ("02_left_sidebar",   Layout02LeftSidebar),
    ("03_right_sidebar",  Layout03RightSidebar),
    ("04_modern_header",  Layout04ModernHeader),
    ("05_minimalist",     Layout05Minimalist),
    ("06_two_columns",    Layout06TwoColumns),
    ("07_table_grid",     Layout07TableGrid),
    ("08_academic",       Layout08Academic),
    ("09_compact",        Layout09Compact),
    ("10_boxed_sections", Layout10Boxed),
]


def main():
    data = generate_cv_data()
    print(f"Generated CV data for: {data['name']}")
    print(f"Output directory: {OUTPUT_DIR}/\n")

    for name, cls in LAYOUTS:
        filename = os.path.join(OUTPUT_DIR, f"cv_{name}.pdf")
        pdf = cls(data)
        pdf.build()
        pdf.output(filename)
        print(f"  ✓ {filename}")

    print(f"\nDone! {len(LAYOUTS)} CVs generated in ./{OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
