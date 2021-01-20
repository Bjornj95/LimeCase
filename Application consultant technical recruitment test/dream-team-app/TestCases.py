import app
import requests 
requests.packages.urllib3.disable_warnings()

def test_getDeals(): 
    ans = app._getDeals() 
    assert ans != None 

def test_getCompanies(): 
    ans = app._getCompanies() 
    assert ans != None 


def test_getDeals():
    ans = app.getDeals(splitMonths = True)
    assert(len(ans[0]) == 12 and ans[1] > 0) 

def test_getCompanies(): 
    ansNotSplit = app.getCompanies(False)
    ansSplit = app.getCompanies(True)
    assert(len(ansSplit) == 5 and len(ansNotSplit[0]) == 1)  





