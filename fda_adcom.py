#!/usr/bin/env python
#AdCom scraper

from bs4 import BeautifulSoup
import urllib
import dateutil.parser as dateparser
import re
import pprint
import os
#import stocker.peeper #WIP company ticker fuzzy search

BASE_URL = 'http://www.fda.gov'
company_name_cache = {}
PAGE_CACHE_DIR = 'pagecache'
if not os.path.exists(PAGE_CACHE_DIR):
    os.mkdir(PAGE_CACHE_DIR)

def fetch_url(url, use_cache=True):
    if use_cache:
        fs_name = '_'.join(url.split('/'))
        full_path = os.path.join(PAGE_CACHE_DIR, fs_name)
        if not os.path.isfile(full_path):
            print 'Retrieving %s' % url
            urllib.urlretrieve(url, full_path)
        return open(full_path)
    else:
        print 'Retrieving %s' % url
        return urllib.urlopen(url)
    

def guess_company(event_url):
    print 'Parsing %s for company names...' % event_url
    company = None

    if event_url in company_name_cache.keys():
        return company_name_cache[event_url]

    page = fetch_url(BASE_URL + event_url)
    text = page.read()
    soup = BeautifulSoup(text)

    guesses = {
        'submitted by' : '.*submitted by (.*?),',
        'sponsored by' : '.*sponsored by (.*?),',
        'Inc.' : 'by (.*?), Inc.' }

    for guess in guesses.keys():
        matching_paragraph = soup.body.find(text=re.compile(guess))
        if matching_paragraph:
            company = re.match(guesses[guess], matching_paragraph)
        if company:
            company_name = company.group(1)
            break
    else:
        company_name = None

    company_name_cache[event_url] = company_name

    page.close()
    return company_name

def guess_date(event_name_text):
    return dateparser.parse(
        re.sub(':', '',                 #strip ":" as it confuses dateparser
               re.sub(r'(\d+)-\d+',     #just use the first date if it's a range
                      r'\1',
                      event_name_text)),
        fuzzy=True)

def gather_report():
    report = {}

    print 'Scraping calendar...'
    page = fetch_url('http://www.fda.gov/AdvisoryCommittees/Calendar/',
                     use_cache=False)
    text = page.read()
    soup = BeautifulSoup(text)
    months = soup.findAll('div', {'class' : 'panel panel-default box '})

    for month in months:
        'Finding events for %s' % month
        month_text = month.find('h2', {'class' : 'panel-title'}).text.strip()
        report[month_text] = []
        for event in month.findAll('li'):
            company_name = None
            company_info = None
            symbol = None

            event_name_text = event.text.strip()
            date = guess_date(event_name_text)
            event_url = event.find('a').get('href')
            company_name = guess_company(event_url)

#            if company_name:
#                company_info = stocker.peeper.lookup_name(company_name)
#            if company_info:
#                symbol = company_info['Symbol']

            report[month_text].append(
                { 'Day' : date.strftime('%B %d'),
                  'Symbol' : symbol,
                  'Company' : company_name,
                  'Event' : event_name_text[:50] })

    return report
        
pprint.pprint(gather_report())
