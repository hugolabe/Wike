# This file is part of Wike (com.github.hugolabe.Wike)
# SPDX-FileCopyrightText: 2021-25 Hugo Olabera
# SPDX-License-Identifier: GPL-3.0-or-later


import json, urllib.parse

from gi.repository import Soup


# Create a Soup session and set user agent

session = Soup.Session.new()
session.set_user_agent('Wike/3.2.0 (https://github.com/hugolabe)')

# Get Wikipedia random page

def get_random(lang, callback):
  endpoint = 'https://' + lang + '.wikipedia.org/w/api.php'
  params = { 'action': 'query',
             'generator': 'random',
             'grnlimit': 1,
             'grnnamespace': 0,
             'prop': 'info',
             'inprop': 'url',
             'format': 'json' }

  _request(endpoint, params, callback, None)

# Get random result from response data

def random_result(async_result):
  response = session.send_and_read_finish(async_result)
  data = response.get_data()
  result = json.loads(data)

  pages = result['query']['pages']
  page_props = list(pages.values())[0]
  uri = page_props['fullurl']
  return uri

# Search Wikipedia with a limit of responses

def search(text, lang, limit, callback):
  endpoint = 'https://' + lang + '.wikipedia.org/w/api.php'
  params = { 'action': 'opensearch',
             'search': text,
             'limit': limit,
             'namespace': 0,
             'redirects': 'resolve',
             'format': 'json' }

  if callback:
    _request(endpoint, params, callback, None)
    return

  data = _request(endpoint, params, None, None)

  if data:
    result = json.loads(data)
    if len(result[1]) > 0:
      return result[1], result[3]

  return None

# Get search results from response data

def search_result(async_result):
  response = session.send_and_read_finish(async_result)
  data = response.get_data()
  result = json.loads(data)

  if len(result[1]) > 0:
    return result[1], result[3]
  else:
    return None

# Get various properties for Wikipedia page

def get_properties(page, lang, callback, user_data):
  endpoint = 'https://' + lang + '.wikipedia.org/w/api.php'
  params = { 'action': 'parse',
             'prop': 'sections|langlinks',
             'redirects': 1,
             'page': page,
             'format': 'json' }

  _request(endpoint, params, callback, user_data)

# Get properties result from response data

def properties_result(async_result):
  response = session.send_and_read_finish(async_result)
  data = response.get_data()
  result = json.loads(data)

  return result['parse']

# Perform query to Wikipedia API with given parameters

def _request(endpoint, params, callback, user_data):
  global session

  params_encoded = urllib.parse.urlencode(params, safe='%=&|')
  message = Soup.Message.new_from_encoded_form('GET', endpoint, params_encoded)

  if callback:
    session.send_and_read_async(message, 0, None, callback, user_data)
    return
  else:
    response = session.send_and_read(message, None)

  if message.get_status() == Soup.Status.OK:
    data = response.get_data()
    return data
  else:
    return None
