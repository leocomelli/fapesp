# -*- coding: utf-8 -*-
import re
import json
from datetime import datetime

import requests
import lxml.html
import unicodedata
import os.path

import sys


def main(url):
    scholar_url = url
    url = url + '&cstart={0}&pagesize={1}&hl=pt-br'

    page_from = 0
    page_to = 100

    start_url = url.format(page_from, page_to)
    r = requests.get(start_url)
    if r.status_code == 200:
        try:
            dom = lxml.html.fromstring(r.text)
            #with open(r'/home/leocomelli/Downloads/gscholar.html', 'r') as f:
            #    page = f.read()
            #dom = lxml.html.fromstring(page)

            data = dom.xpath('//div[@id="gsc_prf_i"]/div')
            name = data[0].text
            university = data[1].text_content()
            email = data[2].text
            areas = dom.xpath('//div[@id="gsc_prf_int"]/a')
            areas = [remove_accents(a.text_content()) for a in areas]

            arts = []

            while True:
                arts += load_articles(dom)
                more = dom.xpath('//button[@id="gsc_bpf_more"]')
                if 'disabled' in more[0].attrib:
                    break

                page_from = page_from + page_to
                start_url = url.format(page_from, page_to)

                r = requests.get(start_url)
                if r.status_code == 200:
                    dom = lxml.html.fromstring(r.text)
                elif r.status_code == 404:
                    return None
                elif r.status_code == 503:
                    return []

            result = {'nome': remove_accents(name), 'url': scholar_url, 'instituicao': remove_accents(university),
                      'email': remove_accents(email), 'areas_interesse': areas, 'artigos': arts, 'total_artigos': len(arts)}

            return result
        except Exception as ex:
            print ex
            return [0]

    else:
        return [r.status_code]


def load_articles(dom):
    arts = []
    articles = dom.xpath('//tbody[@id="gsc_a_b"]/tr')
    for article in articles:
        columns = article.xpath('td')
        url = columns[0].xpath('a/@data-href')[0]
        title = remove_accents(columns[0].xpath('a')[0].text_content())
        authors = remove_accents(columns[0].xpath('div')[0].text)
        details = remove_accents(columns[0].xpath('div')[1].text)

        cited_by = columns[1].xpath('a')[0].text_content()
        cited_by_url = columns[1].xpath('a/@href')[0]

        year = columns[2].xpath('span')[0].text

        art = {'titulo': title, 'url': url, 'autores': authors, 'detalhes': details, 'citado_por': cited_by,
               'citado_por_url': cited_by_url, 'ano': year}

        arts.append(art)

    return arts


def load_citations():
    with open(r'/home/leocomelli/Downloads/gscholar_citations.html', 'r') as f:
        page = f.read()
    dom = lxml.html.fromstring(page)
    title = dom.xpath('//div[@id="gsc_vcd_title"]')[0].text_content()
    url = dom.xpath('//div[@id="gsc_vcd_title"]/a/@href')
    url = url[0] if url else None

    print title
    print url

    fields = dom.xpath('//div[@id="gsc_vcd_table"]/div')
    for field in fields:
        key = field.xpath('div[@class="gsc_vcd_field"]')[0]
        value = field.xpath('div[@class="gsc_vcd_value"]')[0]

        key_str = remove_accents(key.text).replace(' ', '_')
        value_str = remove_accents(value.text)

        if key_str == 'total_de_citacoes':
            value_str = value.xpath('div/a')[0].text
        elif key_str == 'artigos_do_google_academico':
            snippets = value.xpath('//div[@class="gsc_vcd_merged_snippet"]/div')
            gtitle = remove_accents(snippets[0].text_content())
            gurl = snippets[0].xpath('a/@href')[0]
            gdetail = remove_accents(snippets[1].text)
            ginfos = snippets[2].xpath('a')
            for i in ginfos:
                text = remove_accents(i.text_content())
                url = i.xpath('@href')[0]

                print text
                print url

            print gtitle
            print gurl
            print gdetail
            print ginfos

        print key_str
        print value_str


def remove_accents(input_str):
    try:
        line = input_str.decode('utf-8', 'ignore') if isinstance(input_str, str) else input_str
        line = ''.join((c for c in unicodedata.normalize('NFD', line)
                        if unicodedata.category(c) != 'Mn')).lower().encode('utf-8')
        return re.sub(' +', ' ', line).replace('\n', '').replace('\t', '').strip()
    except Exception:
        return input_str


if __name__ == "__main__":

    #main('https://scholar.google.com.br/citations?user=WHdCNq0AAAAJ&cstart={0}&pagesize={1}')

    start = datetime.now()

    idx = sys.argv[1]

    #with open('data/research.json') as d:
    with open('data/researches/group/{0}.json'.format(idx)) as d:
        data = json.load(d)

    block = 0

    total = len(data)
    cur = 1
    for d in data:
        research = d.get('pesquisador')[0]
        url = d.get('google_scholar').get('url')

        filename = '{0}/{1}.json'.format('data/researchers', research.replace(' ', '_'))

        print '{0}/{1} - {2}'.format(cur, total, research)
        if os.path.exists(filename):
            print 'skiping...'
            cur += 1
            continue

        r = main(url)

        if len(r) == 1:
            if r[0] == 404:
                print 'pagina nao encontrada... {0} - {1}'.format(research, url)
                continue
            elif r[0] == 503:
                print 'google bloqueando... {0} - {1}'.format(research, url)

                if block > 3:
                    print 'google bloqueou de vez! :('
                    break

                block += 1
                continue
            else:
                print 'erro inesperado [{0}]... {1} - {2}'.format(r[0], research, url)

        with open(filename, 'w') as fp:
            json.dump(r, fp)

        cur += 1

    end = datetime.now()

    print 'start: {0}, end: {1}'.format(start, end)
    #load_citations()
