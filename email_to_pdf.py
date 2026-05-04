#!/usr/bin/env python3
"""
email_to_pdf.py
---------------
Called by the n8n "Execute Command" node.
Reads email thread data from stdin (JSON), writes a formatted PDF transcript.

Usage:
  python3 email_to_pdf.py --output /path/to/output.pdf --addresses "alice@example.com,bob@example.com"

Stdin format (from n8n Code node):
  JSON array of message objects:
  [
    {
      "subject": "Re: Project Update",
      "from": "alice@example.com",
      "to": "bob@example.com",
      "date": "2024-03-15T10:30:00Z",
      "body": "Hi Bob, just following up..."
    },
    ...
  ]
"""

import sys
import json
import argparse
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

# ── Colour palette ────────────────────────────────────────────────────────────
DARK        = colors.HexColor("#1a1a2e")
ACCENT      = colors.HexColor("#4f46e5")
SENT_BG     = colors.HexColor("#eef2ff")
RECV_BG     = colors.HexColor("#f8fafc")
BORDER      = colors.HexColor("#e2e8f0")
META_GREY   = colors.HexColor("#64748b")
WHITE       = colors.white

def make_styles(my_addresses):
    base = {
        "fontName": "Helvetica",
        "fontSize": 10,
        "leading": 15,
        "textColor": DARK,
    }
    return {
        "cover_title": ParagraphStyle("cover_title",
            fontName="Helvetica-Bold", fontSize=26, textColor=WHITE,
            leading=32, spaceAfter=6),
        "cover_sub": ParagraphStyle("cover_sub",
            fontName="Helvetica", fontSize=12, textColor=colors.HexColor("#a5b4fc"),
            leading=18),
        "section_header": ParagraphStyle("section_header",
            fontName="Helvetica-Bold", fontSize=13, textColor=ACCENT,
            leading=18, spaceBefore=14, spaceAfter=4),
        "meta_label": ParagraphStyle("meta_label",
            fontName="Helvetica-Bold", fontSize=8, textColor=META_GREY,
            leading=12, spaceAfter=1),
        "meta_value": ParagraphStyle("meta_value",
            fontName="Helvetica", fontSize=9, textColor=DARK,
            leading=13, spaceAfter=4),
        "body_sent": ParagraphStyle("body_sent",
            **{**base, "leftIndent": 4, "rightIndent": 4}),
        "body_recv": ParagraphStyle("body_recv",
            **{**base, "leftIndent": 4, "rightIndent": 4}),
        "sender_sent": ParagraphStyle("sender_sent",
            fontName="Helvetica-Bold", fontSize=9, textColor=ACCENT,
            leading=13),
        "sender_recv": ParagraphStyle("sender_recv",
            fontName="Helvetica-Bold", fontSize=9, textColor=colors.HexColor("#0f766e"),
            leading=13),
        "timestamp": ParagraphStyle("timestamp",
            fontName="Helvetica", fontSize=8, textColor=META_GREY,
            leading=12, alignment=TA_RIGHT),
        "footer": ParagraphStyle("footer",
            fontName="Helvetica", fontSize=8, textColor=META_GREY,
            leading=12, alignment=TA_CENTER),
        "toc_entry": ParagraphStyle("toc_entry",
            fontName="Helvetica", fontSize=10, textColor=DARK,
            leading=16, leftIndent=8),
        "toc_header": ParagraphStyle("toc_header",
            fontName="Helvetica-Bold", fontSize=11, textColor=ACCENT,
            leading=16, spaceAfter=6),
    }

def fmt_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%A, %d %B %Y  •  %H:%M UTC")
    except Exception:
        return date_str

def short_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y")
    except Exception:
        return date_str

def clean_body(text):
    """Escape XML special chars for ReportLab and preserve line breaks."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Convert newlines to <br/> but collapse excessive blanks
    lines = text.split("\n")
    cleaned = []
    blank_run = 0
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            blank_run += 1
            if blank_run <= 2:
                cleaned.append("<br/>")
        else:
            blank_run = 0
            cleaned.append(stripped)
    return " ".join(cleaned)

def is_sent(msg, my_addresses):
    sender = msg.get("from", "").lower()
    return any(addr.lower() in sender for addr in my_addresses)

def build_message_block(msg, styles, my_addresses, index):
    sent = is_sent(msg, my_addresses)
    bg   = SENT_BG if sent else RECV_BG
    border_color = ACCENT if sent else colors.HexColor("#0d9488")
    label = "YOU" if sent else "THEM"

    sender_style = styles["sender_sent"] if sent else styles["sender_recv"]
    body_style   = styles["body_sent"]   if sent else styles["body_recv"]

    inner = []

    # Header row: sender + timestamp
    sender_p = Paragraph(
        f'<b>{msg.get("from","Unknown")}</b> &nbsp;<font color="#94a3b8" size="7">{label}</font>',
        sender_style
    )
    time_p = Paragraph(fmt_date(msg.get("date", "")), styles["timestamp"])

    header_table = Table(
        [[sender_p, time_p]],
        colWidths=["60%", "40%"]
    )
    header_table.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
    ]))
    inner.append(header_table)

    # Subject line (show if different from previous or first)
    subj = msg.get("subject", "")
    if subj:
        inner.append(Paragraph(
            f'<font color="#94a3b8" size="8">Subject: </font>'
            f'<font size="8"><b>{subj[:120]}</b></font>',
            styles["meta_value"]
        ))

    inner.append(Spacer(1, 4))

    # Body
    body_text = clean_body(msg.get("body", "(no content)"))
    inner.append(Paragraph(body_text, body_style))

    # Wrap in a styled table cell for background + border
    block = Table(
        [[inner]],
        colWidths=[155*mm]
    )
    block.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), bg),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("LINEAFTER",    (0, 0), (0, -1),  3, border_color),
        ("BOX",          (0, 0), (-1, -1), 0.5, BORDER),
        ("ROUNDEDCORNERS", [4]),
    ]))

    return KeepTogether([block, Spacer(1, 6)])


def build_cover_page(story, addresses, total_msgs, date_range, styles):
    """Full-width cover using a coloured table."""
    title_cell = [
        Paragraph("Email Conversation Export", styles["cover_title"]),
        Spacer(1, 8),
        Paragraph(f"Addresses: {' · '.join(addresses)}", styles["cover_sub"]),
        Spacer(1, 4),
        Paragraph(f"{total_msgs} messages  •  {date_range}", styles["cover_sub"]),
        Spacer(1, 4),
        Paragraph(f"Generated: {datetime.utcnow().strftime('%d %B %Y, %H:%M UTC')}",
                  styles["cover_sub"]),
    ]
    cover = Table([[title_cell]], colWidths=[175*mm])
    cover.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), ACCENT),
        ("LEFTPADDING",   (0, 0), (-1, -1), 18),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 18),
        ("TOPPADDING",    (0, 0), (-1, -1), 28),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 28),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(cover)
    story.append(Spacer(1, 10*mm))


def build_pdf(messages, output_path, my_addresses):
    styles = make_styles(my_addresses)
    doc    = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=16*mm,  bottomMargin=16*mm,
        title="Email Conversation Export",
        author="n8n automation",
    )

    story = []

    # Sort by date
    messages.sort(key=lambda m: m.get("date", ""))

    total = len(messages)
    date_range = ""
    if total:
        date_range = f"{short_date(messages[0].get('date',''))} – {short_date(messages[-1].get('date',''))}"

    # Cover
    build_cover_page(story, my_addresses, total, date_range, styles)

    # Group by subject/thread
    threads = {}
    for msg in messages:
        subj = msg.get("subject", "No Subject")
        # Strip Re:/Fwd: prefixes for grouping
        key = subj.lower()
        for prefix in ["re: ", "fwd: ", "fw: "]:
            while key.startswith(prefix):
                key = key[len(prefix):]
        threads.setdefault(key, {"display": subj, "messages": []})
        threads[key]["messages"].append(msg)

    # Table of Contents
    story.append(Paragraph("Contents", styles["toc_header"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=6))
    for i, (key, thread) in enumerate(threads.items(), 1):
        count = len(thread["messages"])
        story.append(Paragraph(
            f'{i}.&nbsp;&nbsp;<b>{thread["display"][:80]}</b>'
            f'&nbsp;&nbsp;<font color="#94a3b8">({count} message{"s" if count != 1 else ""})</font>',
            styles["toc_entry"]
        ))
    story.append(Spacer(1, 10*mm))

    # Threads
    for i, (key, thread) in enumerate(threads.items(), 1):
        msgs = thread["messages"]
        story.append(Paragraph(
            f'Thread {i} of {len(threads)}: {thread["display"][:90]}',
            styles["section_header"]
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))

        for j, msg in enumerate(msgs):
            story.append(build_message_block(msg, styles, my_addresses, j))

        story.append(Spacer(1, 8*mm))

    # Footer note
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=8, spaceAfter=6))
    story.append(Paragraph(
        f"Exported by n8n Email Conversation Workflow  •  {total} messages  •  {date_range}",
        styles["footer"]
    ))

    doc.build(story)
    print(f"PDF written to: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",    required=True, help="Output PDF path")
    parser.add_argument("--addresses", required=True, help="Comma-separated email addresses to track")
    args = parser.parse_args()

    my_addresses = [a.strip() for a in args.addresses.split(",") if a.strip()]
    data = json.load(sys.stdin)

    if not isinstance(data, list):
        print("ERROR: stdin must be a JSON array of message objects", file=sys.stderr)
        sys.exit(1)

    build_pdf(data, args.output, my_addresses)

if __name__ == "__main__":
    main()
