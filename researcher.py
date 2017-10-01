# -*- coding: utf-8 -*-
import os
import json


def main(dir):
    researchers = []
    urls = []

    total = 0
    gtotal = 0
    utotal = 0

    files = os.listdir(dir)
    for f in files:
        with open(os.path.join(dir, f)) as data_file:
            data = json.load(data_file)

            for d in data:
                total += 1
                research = d.get('pesquisador_responsavel')

                gscholar = d.get('google_scholar')
                if gscholar is not None:
                    url = gscholar.get('url')
                    r = {'pesquisador': research, 'google_scholar': {'url': url}}

                    gtotal += 1
                    if url in urls:
                        continue

                    urls.append(url)
                    utotal += 1
                    researchers.append(r)

    print 'total: %s' % total
    print 'gtotal: %s' % gtotal
    print 'utotal: %s' % utotal

    with open('data/research.json', 'w') as fp:
        json.dump(researchers, fp)


if __name__ == "__main__":
    main('data/full')
