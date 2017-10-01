# -*- coding: utf-8 -*-
import json
import re
from datetime import datetime
import os.path
import unicodedata


def remove_accents(input_str):
    try:
        line = input_str.decode('utf-8', 'ignore') if isinstance(input_str, str) else input_str
        line = ''.join((c for c in unicodedata.normalize('NFD', line)
                        if unicodedata.category(c) != 'Mn')).lower().encode('utf-8')
        return re.sub(' +', ' ', line).replace('\n', '').replace('\t', '').strip()
    except Exception:
        return input_str


if __name__ == "__main__":
    start = datetime.now()

    with open('data/research.json') as d:
        data = json.load(d)

    group = 1
    bag = []

    for d in data:
        research = remove_accents(d.get('pesquisador')[0])
        url = d.get('google_scholar').get('url')

        filename = '{0}/{1}.json'.format('data/researchers', research.replace(' ', '_'))

        if os.path.exists(filename):
            continue

        bag.append(d)

        if len(bag) == 1500:
            with open('{0}/{1}.json'.format('data/researchers/group/', group), 'w') as fp:
                json.dump(bag, fp)
            group += 1
            bag = []
