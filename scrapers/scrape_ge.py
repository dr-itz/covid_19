#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import datetime
import sys
from bs4 import BeautifulSoup
import scrape_common as sc

# parse tested from PDF
d = sc.download('https://www.ge.ch/document/covid-19-bilan-epidemiologique-hebdomadaire', silent=True)
soup = BeautifulSoup(d, 'html.parser')
pdf_url = soup.find(title=re.compile("\.pdf$")).get('href')
assert pdf_url, "pdf URL is empty"
if not pdf_url.startswith('http'):
    pdf_url = f'https://www.ge.ch{pdf_url}'
pdf = sc.pdfdownload(pdf_url, silent=True)

week_number = sc.find(r'Situation semaine (\d+)', pdf)
week_end_date = datetime.datetime.strptime('2020-W' + week_number + '-7', '%G-W%V-%u').date()
number_of_tests = sc.find(r'N total tests : (\d+\'\d+)', pdf)
number_of_tests = number_of_tests.replace('\'', '')

dd_test = sc.DayData(canton='GE', url=pdf_url)
dd_test.datetime = week_end_date.isoformat()
dd_test.tested = number_of_tests
print(dd_test)

# xls
d = sc.download('https://www.ge.ch/document/covid-19-donnees-completes-debut-pandemie', silent=True)
soup = BeautifulSoup(d, 'html.parser')
xls_url = soup.find(title=re.compile("\.xlsx$")).get('href')
assert xls_url, "xls URL is empty"
if not xls_url.startswith('http'):
    xls_url = f'https://www.ge.ch{xls_url}'

xls = sc.xlsdownload(xls_url, silent=True)
rows = sc.parse_xls(xls, header_row=0, skip_rows=2)
for i, row in enumerate(rows):
    if not isinstance(row['Date'], datetime.datetime):
        print(f"WARNING: {row['Date']} is not a valid date, skipping.", file=sys.stderr)
        continue

    print('-' * 10)
    is_first = False
    
    # TODO: remove when source is fixed
    # handle wrong value on 2020-04-09, see issue #819
    if row['Date'].date().isoformat() == '2020-04-09':
        row['Cumul COVID-19 sorties d\'hospitalisation'] = ''

    dd = sc.DayData(canton='GE', url=xls_url)
    dd.datetime = row['Date'].date().isoformat()
    dd.cases = row['Cumul cas COVID-19']
    dd.hospitalized = row['Total hospitalisations COVID-19 actifs ']
    dd.icu = row['Patients COVID-19 actifs aux soins intensifs ']
    dd.icf = row['Patients COVID-19 actifs aux soins intermédiaires']
    dd.deaths = row['Cumul décès COVID-19 ']
    dd.recovered = row['Cumul COVID-19 sorties d\'hospitalisation']
    dd.isolated = row['Nombre de personnes en isolement ce jour']
    dd.quarantined = row['Nombre de personnes en quarantaine ce jour ']
    dd.quarantine_riskareatravel = row['Nombre de personnes en quarantaine ce jour suite à un retour de voyage']

    # Since 2020-07-01 new_hosp is no longer provided
    #dd.new_hosp = row['Nb nouveaux patients COVID-19 hospitalisés']

    ## Since 2020-07-27 vent is no longer provided 
    #dd.vent = row['Patients COVID-19 aux soins intensifs intubés']

    # TODO: check if Nombre tests is added again
    # on 2020-06-09 GE removed the `Nombre tests` column
    #dd.tested = sum(r['Nombre tests'] for r in rows[:i+1])
    print(dd)

