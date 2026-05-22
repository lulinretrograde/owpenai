import re
import random

faces = ["(・`ω´・)", ";;w;;", "owo", "UwU", ">w<", "^w^", "nyaa~~", ":3", "XD", "mya", "uwu"]

def uwuify(text):
    if not text or not text.strip():
        return text

    text = re.sub(r'r', 'w', text)
    text = re.sub(r'l', 'w', text)
    text = re.sub(r'R', 'W', text)
    text = re.sub(r'L', 'W', text)

    text = re.sub(r'[Tt][Hh]', lambda m: 'D' if m.group()[0].isupper() else 'd', text)

    text = re.sub(r'n([aeiouAEIOU])', lambda m: 'ny' + m.group(1), text)
    text = re.sub(r'N([aeiou])', lambda m: 'Ny' + m.group(1), text)

    text = text.replace('ove', 'uv').replace('Ove', 'Uv')

    words = text.split(' ')
    out = []
    for w in words:
        if w and len(w) > 1 and random.random() < 0.05:
            w = w[0] + '-' + w
        out.append(w)
    text = ' '.join(out)

    def add_face(m):
        if random.random() < 0.4:
            return m.group(0) + ' ' + random.choice(faces)
        return m.group(0)

    text = re.sub(r'[.!?](?=\s|$)', add_face, text)

    return text
