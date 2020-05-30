import re
import string
from typing import Dict, List, Callable, Any, Tuple


def extract_words(
    raw_tweets: Dict[str, Dict], bots: List
) -> Tuple[Dict[str, List], str]:
    out = {}
    bot_set = set(bots)
    k = ""
    for k, tweet in sorted(raw_tweets.items(), key=lambda x: x[0]):
        if tweet is None:
            continue
        elif tweet["user"]["screen_name"] in bot_set:
            continue
        raw_words = re.split(r"\s", tweet["text"])
        words_no_spaces = [
            "".join([ch for ch in w if ch in set(string.printable)])
            for w in raw_words
            if w.strip() != ""
        ]
        out[k] = words_no_spaces
    return out, k


def count_words(
    extracted_words: Dict[str, List], prev_word_counts: Dict[str, Callable[[], Dict]]
):
    import datetime

    current_dt = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S:%f")
    agg_counts = (
        prev_word_counts[max(prev_word_counts.keys())]()
        if len(prev_word_counts.keys())
        else {}
    )

    # Assumes confirms raw_tweets
    for _, words in extracted_words.items():
        for word in words:
            agg_counts[word] = agg_counts.get(word, 0) + 1

    return {current_dt: agg_counts} if len(agg_counts) > 0 else {}


def create_graphs(word_counts: Dict[str, Dict]) -> Tuple[Dict[str, Dict], Any]:
    import matplotlib.pyplot as plt

    plt.ioff()

    out = {}

    for k, count in sorted(word_counts.items(), key=lambda x: x[0]):
        if count is None:
            continue
        top_10 = list(sorted(count.items(), key=lambda x: x[1], reverse=True))[:10]
        x_values = [x[0] for x in top_10]
        y_values = [x[1] for x in top_10]
        out[k] = plt.figure(figsize=(12, 12))
        plt.bar(x_values, y_values)
        plt.close()

    last_figure = plt.figure(figsize=(12, 12))
    plt.close()
    if len(out) > 0:
        last_figure = out[max(out.keys())]

    return out, last_figure
