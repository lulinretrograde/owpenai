import re
import random

FACES = ["(・`ω´・)", ";;w;;", "owo", "UwU", ">w<", "^w^", "✿", "nyaa~~", ":3", "XD", "mya", "✨"]

def uwuify(text):
    if not text or not text.strip():
        return text

    # r/l -> w
    text = re.sub(r'(?<![a-zA-Z])r(?![a-zA-Z])', 'w', text)
    text = re.sub(r'r', 'w', text)
    text = re.sub(r'l', 'w', text)
    text = re.sub(r'R', 'W', text)
    text = re.sub(r'L', 'W', text)

    # th -> d
    text = re.sub(r'[Tt][Hh]', lambda m: 'D' if m.group()[0].isupper() else 'd', text)

    # n + vowel -> ny + vowel
    text = re.sub(r'n([aeiouAEIOU])', lambda m: 'ny' + m.group(1) if m.group(1).islower() else 'nY' + m.group(1), text)
    text = re.sub(r'N([aeiouAEIOU])', lambda m: 'Ny' + m.group(1), text)

    # ove -> uv
    text = text.replace('ove', 'uv').replace('Ove', 'Uv')

    # stutter ~5% of words
    words = text.split(' ')
    stuttered = []
    for w in words:
        if w and len(w) > 1 and random.random() < 0.05:
            w = f"{w[0]}-{w}"
        stuttered.append(w)
    text = ' '.join(stuttered)

    # inject face after sentence-ending punctuation ~40% of the time
    def maybe_face(m):
        if random.random() < 0.4:
            return m.group(0) + ' ' + random.choice(FACES)
        return m.group(0)

    text = re.sub(r'[.!?](?=\s|$)', maybe_face, text)

    return text
