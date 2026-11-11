"""Readable names for the question topics (owner: B).

The question bank uses short ids like "konjunktiv2_modalverben". The names shown on
screen are in core/strings_en.json under "topic_<id>". A topic without a name there
is shown as its id with spaces.
"""
from core.strings import t


def label(topic):
    name = t(f"topic_{topic}")
    if name.startswith("["):          # t() returns "[key]" when the text is missing
        return topic.replace("_", " ")
    return name
