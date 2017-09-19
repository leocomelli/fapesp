import requests
import lxml.html
from django.core.paginator import Paginator
from urlparse import urlparse
import json
import unicodedata


def remove_accents(input_str):
    try:
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
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

def get_article_details(url):
    print url
    r = requests.get(url)
    if r.status_code == 200:
        dom = lxml.html.fromstring(r.text)
        resume = remove_accents(dom.xpath('string(//*[@id="conteudo"]/div[2]/div/div/div[2]/section/div/div[1]/p[2])'))
        details = {'resume': resume, 'citations': []}
        citations = dom.xpath('//div[@class="description"]')
        for citation in citations:
            if len(citation.xpath('span/text()')):
                publication_type =  remove_accents(citation.xpath('span/text()')[0])
                total = len(citation.xpath('div')) - 1
                details['citations'].append({'type': publication_type, 'total': total})
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
            artile_url = element.xpath('h2/a/@href')[0]
            title = remove_accents(element.xpath('h2/a/text()')[0])
            artile_url = '%s://%s%s' % (url_parsed.scheme, url_parsed.netloc, artile_url)            
            details = get_article_details(artile_url)
            item = {'url': artile_url, 'title': title, 'properties': []}
            item.update(details)

            properties = element.xpath('table/tr')
            for p in properties:
                label = p.xpath('td')[0].text
                values = p.xpath('td')[1]
                item['properties'].append({'label': label, 'values': extract_values(values)})            
            items.append(item)
        return items
    else:
        raise Exception('error retrieve url %s, status code %s' % (url, r.status_code))

start_url = 'http://bv.fapesp.br/pt/pesquisa/?sort=-data_inicio&q2=%28%28auxilio_exact%3A%22Aux%C3%ADlios+Regulares%22%29%29+AND+%28%28situacao_exact%3A%22Conclu%C3%ADdos%22+AND+auxilio%3A%2A%29%29&count=50'
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
