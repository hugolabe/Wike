# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-23 Hugo Olabera <hugolabe@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later


import requests


# create a session for wikipedia requests

_session = requests.Session()

# Get Wikipedia random page

def get_random(lang):
  api = 'https://' + lang + '.wikipedia.org/w/api.php'
  params = { 'action': 'query',
             'generator': 'random',
             'grnlimit': 1,
             'grnnamespace': 0,
             'prop': 'info',
             'inprop': 'url',
             'format': 'json' }

  result = _request(api, params)
  pages = result['query']['pages']
  for page, info in pages.items():
    uri = info['fullurl']

  return uri

# Search in Wikipedia with a limit of responses

def search(text, lang, limit):
  api = 'https://' + lang + '.wikipedia.org/w/api.php'
  params = { 'action': 'opensearch',
             'search': text,
             'limit': limit,
             'namespace': 0,
             'redirects': 'resolve',
             'format': 'json' }

  result = _request(api, params)

  if len(result[1]) == 0:
    return None
  else:
    return result[1], result[3]

# Get sections and langlinks for Wikipedia page

def get_properties(page, lang):
  api = 'https://' + lang + '.wikipedia.org/w/api.php'
  params = '?format=json&action=parse&prop=sections|langlinks&redirects&page=' + page

  result = _request(api, params)

  return result['parse']

# Perform query to Wikipedia API with given parameters

def _request(api, params):
  global _session
  headers = { 'User-Agent': 'Wike/2.0.1 (https://github.com/hugolabe)' }

  if type(params) is dict:
    response = _session.get(url=api, params=params, headers=headers, timeout=(4, 12))
  else:
    uri = api + params
    response = _session.get(url=uri, params=None, headers=headers, timeout=(4, 12))

  return response.json()
