import requests
import lxml.html

url = 'http://bv.fapesp.br/pt/pesquisa/?sort=-data_inicio&q2=%28%28auxilio_exact%3A%22Aux%C3%ADlios+Regulares%22%29%29+AND+%28%28situacao_exact%3A%22Conclu%C3%ADdos%22+AND+auxilio%3A%2A%29%29'
r = requests.get(url)

if r.status_code == 200:
    if r.encoding in 'UTF-8':
        dom = lxml.html.fromstring(r.text)
    else:
        dom = lxml.html.fromstring(r.text.encode('utf-8'))

    elements = dom.xpath('//div[@class=\"table_details\"]')    
    for element in elements:
        # title = element.xpath('h2/a/@title')[0]
        title = element.xpath('h2/a/text()')[0]
        print title
        print element        
else:
    # logger.error('%s invalid status %s, from url %s' % (isbn, r.status_code, sb.url))
    raise Exception('Error retrieve url %s, Status Code %s' % (url, r.status_code))
