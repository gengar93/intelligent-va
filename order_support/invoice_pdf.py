"""Render an invoice snapshot into a downloadable PDF (Atelier style).

The PDF is generated on demand from the stored invoice snapshot — no files are
persisted. Fonts are bundled (IBM Plex, SIL OFL) so output is identical on any
host. See order_support/fonts/OFL.txt for the license.
"""

from datetime import datetime
from pathlib import Path

from fpdf import FPDF

FONT_DIR = Path(__file__).resolve().parent / "fonts"
SERIF_REGULAR = FONT_DIR / "IBMPlexSerif-Regular.ttf"
SERIF_SEMIBOLD = FONT_DIR / "IBMPlexSerif-SemiBold.ttf"
SANS = FONT_DIR / "IBMPlexSans-VF.ttf"

# Placeholder seller identity — the demo has no real merchant entity to bill from.
SELLER = {
    "name": "Meridian Retail Private Limited",
    "address": "4th Floor, Prestige Tech Park,\nBengaluru 560103",
    "gstin": "GSTIN 29ABCDE1234F1Z5",
}

# Atelier palette
PAPER = (246, 241, 233)
CARD = (255, 253, 249)
INK = (38, 33, 28)
INK2 = (92, 83, 74)
INK3 = (138, 128, 117)
ACCENT = (180, 73, 31)
ACCENT_DEEP = (143, 55, 23)
HAIR = (222, 214, 201)

L, R = 18, 192
W = R - L
PAD = 6
IL, IR = L + PAD, R - PAD  # inner content edges of the line-item card


def _money(minor, currency):
    symbol = "₹" if currency == "INR" else f"{currency} "
    return f"{symbol}{minor / 100:,.2f}"


def _issued(value):
    try:
        dt = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{dt.day} {dt:%b %Y}"


def _fit(pdf, text, max_w):
    """Truncate text with an ellipsis so it never exceeds max_w in the current font."""
    if pdf.get_string_width(text) <= max_w:
        return text
    while text and pdf.get_string_width(text + "...") > max_w:
        text = text[:-1]
    return (text.rstrip() + "...") if text else "..."


def render_invoice_pdf(invoice: dict) -> bytes:
    """Return the bytes of a one-page A4 PDF for one invoice snapshot."""
    currency = invoice["currency"]
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_font("serif", "", str(SERIF_REGULAR))
    pdf.add_font("serif", "B", str(SERIF_SEMIBOLD))
    pdf.add_font("sans", "", str(SANS))
    pdf.add_page()

    pdf.set_fill_color(*PAPER)
    pdf.rect(0, 0, 210, 297, "F")

    # Masthead
    pdf.set_fill_color(*ACCENT)
    pdf.rect(L, 20, 9, 9, "F")
    pdf.set_font("serif", "B", 14)
    pdf.set_text_color(*INK)
    pdf.set_xy(L + 12, 21)
    pdf.cell(90, 8, "Support Console")
    pdf.set_font("serif", "", 32)
    pdf.set_text_color(*ACCENT_DEEP)
    pdf.set_xy(R - 90, 15)
    pdf.cell(90, 13, "Invoice", align="R")

    def eyebrow(x, y, text):
        pdf.set_font("sans", "", 7)
        pdf.set_text_color(*INK3)
        try:
            pdf.set_char_spacing(1.2)
        except Exception:
            pass
        pdf.set_xy(x, y)
        pdf.cell(90, 4, text.upper())
        try:
            pdf.set_char_spacing(0)
        except Exception:
            pass

    pdf.set_draw_color(*HAIR)
    pdf.set_line_width(0.4)
    pdf.line(L, 37, R, 37)

    # Meta row
    eyebrow(L, 44, "Invoice no.")
    eyebrow(L + 60, 44, "Issued")
    eyebrow(L + 110, 44, "Order")
    pdf.set_font("sans", "", 10.5)
    pdf.set_text_color(*INK)
    pdf.set_xy(L, 49)
    pdf.cell(60, 5, invoice["invoice_number"])
    pdf.set_xy(L + 60, 49)
    pdf.cell(50, 5, _issued(invoice["issued_at"]))
    pdf.set_xy(L + 110, 49)
    pdf.cell(50, 5, invoice["order_id"])

    def party(x, label, name, address, extra=None):
        eyebrow(x, 63, label)
        pdf.set_font("serif", "B", 12)
        pdf.set_text_color(*INK)
        pdf.set_xy(x, 68)
        pdf.cell(85, 6, name)
        pdf.set_font("sans", "", 9.5)
        pdf.set_text_color(*INK2)
        pdf.set_xy(x, 75)
        pdf.multi_cell(85, 4.8, address, align="L")
        if extra:
            pdf.set_x(x)
            pdf.cell(85, 4.8, extra)

    party(L, "Billed to", invoice["billing_name"], invoice["billing_address"])
    party(L + 95, "From", SELLER["name"], SELLER["address"], SELLER["gstin"])

    # Line-item card
    items = invoice["items"]
    top = 97
    rows_h = 11 * len(items) + 14
    pdf.set_fill_color(*CARD)
    pdf.set_draw_color(*HAIR)
    pdf.set_line_width(0.4)
    pdf.rect(L, top, W, rows_h, "DF")

    cols = [(84, "Item", "L"), (16, "Qty", "C"), (31, "Unit", "R"), (31, "Amount", "R")]
    y = top + 6
    x = IL
    for w, title, align in cols:
        pdf.set_font("sans", "", 7)
        pdf.set_text_color(*INK3)
        pdf.set_xy(x, y)
        pdf.cell(w, 4, title.upper(), align=align)
        x += w
    y += 7
    pdf.set_draw_color(*HAIR)
    pdf.line(IL, y, IR, y)
    y += 2

    for index, item in enumerate(items):
        x = IL
        pdf.set_font("serif", "B", 11)
        pdf.set_text_color(*INK)
        pdf.set_xy(x, y)
        pdf.cell(cols[0][0], 6, _fit(pdf, item["description"], cols[0][0] - 3))
        x += cols[0][0]
        pdf.set_font("sans", "", 10.5)
        pdf.set_text_color(*INK)
        pdf.set_xy(x, y)
        pdf.cell(cols[1][0], 6, str(item["quantity"]), align="C")
        x += cols[1][0]
        pdf.set_xy(x, y)
        pdf.cell(cols[2][0], 6, _money(item["unit_price_minor"], currency), align="R")
        x += cols[2][0]
        pdf.set_xy(x, y)
        pdf.cell(cols[3][0], 6, _money(item["line_total_minor"], currency), align="R")
        y += 11
        if index < len(items) - 1:
            pdf.set_draw_color(*HAIR)
            pdf.line(IL, y - 2, IR, y - 2)

    # Totals
    y = top + rows_h + 8

    def total_row(label, value, big=False):
        nonlocal y
        pdf.set_font("sans", "", 9.5)
        pdf.set_text_color(*(INK if big else INK3))
        pdf.set_xy(IR - 80, y)
        pdf.cell(44, 6, label, align="R")
        if big:
            pdf.set_font("serif", "B", 15)
            pdf.set_text_color(*ACCENT_DEEP)
            pdf.set_xy(IR - 36, y - 2)
        else:
            pdf.set_font("sans", "", 9.5)
            pdf.set_text_color(*INK)
            pdf.set_xy(IR - 36, y)
        pdf.cell(36, 6, value, align="R")
        y += 7.5

    total_row("Subtotal", _money(invoice["subtotal_minor"], currency))
    total_row("Tax", _money(invoice["tax_minor"], currency))
    y += 1
    pdf.set_draw_color(*HAIR)
    pdf.line(IR - 80, y, IR, y)
    y += 3
    total_row("Total due", _money(invoice["total_minor"], currency), big=True)

    # Footer
    pdf.set_draw_color(*HAIR)
    pdf.line(L, 274, R, 274)
    pdf.set_font("serif", "", 11)
    pdf.set_text_color(*INK2)
    pdf.set_xy(L, 278)
    pdf.cell(W / 2, 5, "Support Console")
    pdf.set_font("sans", "", 8.5)
    pdf.set_text_color(*INK3)
    pdf.set_xy(L, 278)
    pdf.cell(W, 5, f"Order {invoice['order_id']}  ·  Thank you for your order.", align="R")

    return bytes(pdf.output())
