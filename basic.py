# -*- coding: utf-8 -*-
import os, re
import requests
import lxml.html
from django.core.paginator import Paginator
from urlparse import urlparse
import json
import unicodedata


def remove_accents(input_str):
    try:
        line = input_str.decode('utf-8', 'ignore') if isinstance(input_str, str) else input_str
        line = ''.join((c for c in unicodedata.normalize('NFD', line)
                        if unicodedata.category(c) != 'Mn')).lower().encode('utf-8')
        return re.sub(' +', ' ', line).replace('\n', '').replace('\t', '').strip()
    except Exception:
        return input_str


def extract_values(value):
    values = []
    if value.text:
        values.append(remove_accents(value.text))
    else:        
        for o in value.xpath('a'):
            if o.text:
                values.append(remove_accents(o.text))
    return values


def extract_properties(props):
    properties = {}
    for p in props:
        label = remove_accents(p.xpath('td')[0].text).lower()
        label = label.replace(' ', '_')
        label = label.replace('-', '_')
        label = label.replace('(', '')
        label = label.replace(')', '')
        label = label.replace('.', '')
        label = label.replace(':', '')

        values = extract_values(p.xpath('td')[1])

        if label == 'vigencia':
            v = values[0].split('-')
            properties['vigencia_inicio'] = v[0].strip()
            properties['vigencia_fim'] = v[1].strip()
        elif label == 'processo':
            properties[label] = values[0]
        elif label == 'pesquisador_responsavel':
            onclick_value = p.xpath('td')[1].xpath('a[@class="plataforma_google"]/@onclick')
            if len(onclick_value) > 0:
                url = re.findall(r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?',
                                 onclick_value[0])
                url = 'http://%s' % ''.join(url[0][1:])
                properties['google_scholar'] = {'url': url,
                                                'metricas': extract_google_scholar(url)}

        else:
            properties[label] = values
    return properties


def extract_google_scholar(url):
    r = requests.get(url)
    metrics = {}
    if r.status_code == 200:
        dom = lxml.html.fromstring(r.text)

        lines = dom.xpath('//*[@id="gsc_rsb_st"]/tr')
        for line in lines:
            if len(line.xpath('td')) > 0:
                label = line.xpath('td')[0].xpath('a')[0].text
                label = remove_accents(label.lower().replace('-', '_').replace(' ', '_'))
                value = extract_values(line.xpath('td')[1])

                metrics[label] = value

    return metrics


def get_article_details(url):
    print url
    r = requests.get(url)
    if r.status_code == 200:
        dom = lxml.html.fromstring(r.text)
        resume = remove_accents(dom.xpath('string(//*[@id="conteudo"]/div[2]/div/div/div[2]/section/div/div[1]/p[2])'))
        details = {'resumo': resume, 'citacoes': []}
        citations = dom.xpath('//div[@class="description"]')
        for citation in citations:
            if len(citation.xpath('span/text()')):
                c = {}
                publications = []
                publication_type = remove_accents(citation.xpath('span/text()')[0]).replace(' ', '_')
                citation_detail = citation.xpath('div')

                for cd in citation_detail:
                    try:
                        venue = cd.xpath('strong/text()')[0].replace('\n', '').replace('\t', '').strip()
                        article_title = cd.xpath('a/text()')[0].replace('\n', '').replace('\t', '').strip()
                    except IndexError:
                        continue

                    source = re.sub(' +', ' ', cd.text_content()).replace('\n', '').replace('\t', '').strip()
                    web_of_science = re.findall(r'Cita\xe7\xf5es Web of Science: (\d+).', source)
                    if web_of_science:
                        web_of_science = web_of_science[0]

                    publications.append({'venue': venue, 'title': article_title, 'web_of_science': web_of_science,
                                         'source': source})

                total = len(citation_detail) - 1
                c[publication_type] = {'total': total, 'publicacoes': publications}
                details['citacoes'].append(c)
        return details
    else:
        raise Exception('error retrieve url %s, status code %s' % (url, r.status_code))
        

def get_page(url):
    print '{0}'.format(url)    
    items = []
    r = requests.get(url)
    url_parsed = urlparse(url)
    if r.status_code == 200:
        dom = lxml.html.fromstring(r.text)
        elements = dom.xpath('//div[@class=\"table_details\"]')    
        for element in elements:
            article_url = element.xpath('h2/a/@href')[0]
            title = remove_accents(element.xpath('h2/a/text()')[0])
            article_url = '%s://%s%s' % (url_parsed.scheme, url_parsed.netloc, article_url)

            item = {'url': article_url, 'titulo': title}
            item.update(get_article_details(article_url))
            item.update(extract_properties(element.xpath('table/tr')))

            items.append(item)
        return items
    else:
        raise Exception('error retrieve url %s, status code %s' % (url, r.status_code))


def main():
    start_url = 'http://bv.fapesp.br/pt/pesquisa/?sort=-data_inicio&q2=auxilio_exact%3A%22Aux%C3%ADlios+Regulares%22&&count=50'
    r = requests.get(start_url, allow_redirects=True)
    dom = lxml.html.fromstring(r.text)
    count = int(dom.xpath('string(//*[@id="content"]/div/div/div/div[2]/div/section/div[1]/div/div/div[1]/text())').replace('resultado(s)', '').replace('.', '').strip())
    per_page = 50
    position = 0
    objects = [None] * count
    paginator = Paginator(objects, per_page)

    for index in range(1, paginator.num_pages + 1):
        page = paginator.page(index)
        active_page = '{0}&page={1}'.format(start_url, index)
        articles = get_page(active_page)
        print page
        with open('data/page_{0}.json'.format(index), 'w') as fp:
            json.dump(articles, fp)


if __name__ == "__main__":
    main()
