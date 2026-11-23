from html import escape
from pathlib import Path

OUT = Path(__file__).with_name('ai-model-routing-guide-2026.svg')
parts = ['''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img" aria-labelledby="title desc">
<title id="title">AI Model Guide for Creative and Marketing Teams (2026)</title>
<desc id="desc">A simple guide to models for writing, visual work, image creation, and effort levels.</desc>
<defs><filter id="shadow" x="-10%" y="-20%" width="120%" height="150%"><feDropShadow dx="0" dy="5" stdDeviation="10" flood-color="#20334e" flood-opacity=".10"/></filter></defs>
<rect width="1920" height="1080" fill="#f0f4f7"/><rect width="1920" height="10" fill="#168f91"/>
<g font-family="Inter, Segoe UI, Arial, sans-serif" fill="#1c2c42">''']

def rect(x, y, w, h, fill, rx=20, extra=''):
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>')

def text(x, y, value, size=20, weight=400, fill='#1c2c42', extra=''):
    parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" {extra}>{escape(value)}</text>')

text(90, 76, 'Which AI model should I use?', 45, 800)
text(92, 112, 'A quick guide for creative and marketing work · 2026', 21, fill='#64748b')
rect(1490, 48, 340, 58, '#daf2ef', 29)
text(1660, 85, 'START WITH SOL + MEDIUM', 19, 800, '#087e7e', 'text-anchor="middle"')
text(90, 175, 'FOR WRITING, IDEAS & EVERYDAY TASKS', 24, 800)
text(90, 202, 'Pick the card that sounds most like your task.', 17, fill='#64748b')

cards = [
    (90, 225, 'GPT-6.2 Sol', 'Your everyday choice', 'Content ideas, captions, emails, briefs,', 'outlines, summaries and general tasks.', '#119b98', '#dff5f0', '1'),
    (955, 225, 'GPT-6 Luna', 'Quick, simple jobs', 'Short rewrites, formatting, tagging and', 'repeat tasks with clear instructions.', '#34aaa0', '#e4f7f2', '2'),
    (90, 403, 'GPT-6.1 Terra', 'When you need to show it something', 'Review screenshots, visuals or charts;', 'help with tasks inside apps.', '#6674d7', '#ebeefe', '3'),
    (955, 403, 'GPT-6.2 Astra', 'Big, difficult projects', 'Campaign strategy, complex research,', 'or decisions with many moving parts.', '#d89c2e', '#fff2da', '4'),
]
for x, y, name, sub, line1, line2, accent, pale, icon in cards:
    rect(x, y, 845 if x == 90 else 875, 160, '#ffffff', 23, 'filter="url(#shadow)"')
    rect(x, y, 11, 160, accent, 5)
    parts.append(f'<circle cx="{x+59}" cy="{y+48}" r="26" fill="{pale}"/>')
    text(x+59, y+57, icon, 27, 800, accent, 'text-anchor="middle"')
    text(x+105, y+45, name, 27, 800)
    text(x+105, y+74, sub, 18, 700, accent)
    text(x+32, y+113, line1, 19, fill='#4c6077')
    text(x+32, y+140, line2, 19, fill='#4c6077')

text(90, 622, 'FOR CREATING OR EDITING IMAGES', 24, 800)
text(90, 649, 'Choose an image model when you want an actual visual.', 17, fill='#64748b')
for x, w, color, accent, name, use, desc in [
    (90, 845, '#e8f7f5', '#087d7d', 'GPT-Image-2.6 Flare', 'Fast concepts and variations', 'Explore mood boards, directions and first drafts.'),
    (955, 875, '#ecedff', '#5664bd', 'GPT-Image-2.6 Sunburst', 'Detailed visuals and careful edits', 'Use when accuracy, layout or polish matters most.'),
]:
    rect(x, 670, w, 134, color, 23, 'filter="url(#shadow)"')
    text(x+32, 713, name, 26, 800, accent)
    text(x+32, 745, use, 20, 700)
    text(x+32, 776, desc, 18, fill='#4c6077')

text(90, 861, 'WHICH EFFORT LEVEL?', 24, 800)
text(90, 889, 'Use Medium for most work. Move up only when the task needs more thought.', 17, fill='#64748b')
levels = [
    ('Light', 'Quick rewrites', 'and simple edits'),
    ('Medium', 'Ideas, captions', 'and daily work'),
    ('High', 'Multi-step briefs', 'and research'),
    ('Extra High', 'Complex plans', 'and comparisons'),
    ('Ultra', 'Rare, toughest', 'decisions'),
]
for i, (name, line1, line2) in enumerate(levels):
    x = 90 + 349*i
    rect(x, 909, 334 if i < 4 else 344, 119, '#dff5f0' if i == 1 else '#ffffff', 18, 'filter="url(#shadow)"')
    text(x+25, 949, name, 23, 800, '#087e7e' if i == 1 else '#1c2c42')
    text(x+25, 982, line1, 18, fill='#53677e')
    text(x+25, 1006, line2, 18, fill='#53677e')

parts.append('</g></svg>')
OUT.write_text('\n'.join(parts), encoding='utf-8')
