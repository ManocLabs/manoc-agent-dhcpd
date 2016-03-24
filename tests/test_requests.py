import pytest_httpbin
from manoc_agents.common import requests

def test_simple_get(httpbin):
    url = httpbin.url + '/get'

    r = requests.GET(url)
    assert r.code() == 200

def test_basic_auth(httpbin):
    user   = 'myuser'
    passwd = 'mypass'    
    url = httpbin.url + '/basic-auth/' + user + '/' + passwd
    assert requests.GET(url, auth=(user, passwd)).code() == 200
    
def test_simple_post(httpbin):
    url = httpbin.url + '/post'    
    r = requests.POST(url, 'test=value')
    assert r.code() == 200
    data = r.json()
    assert data['form']['test'] == 'value'

def test_post_json(httpbin):
    url = httpbin.url + '/post'    
    r = requests.POST(url, json={'foo' : 'bar'})
    assert r.code() == 200
    data = r.json()
    assert data['json']['foo'] == 'bar'

