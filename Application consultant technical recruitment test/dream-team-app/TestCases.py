import app
import requests 
requests.packages.urllib3.disable_warnings()

def test_getDeals(): 
    ans = app._getDeals() 
    assert ans != None 

def test_getCompanies(): 
    ans = app._getCompanies() 
    assert ans != None 

def testgetDeals():
    """
    Test if getDeals function works 
    """
    ans = app.getDeals(splitMonths = True)
    assert(len(ans[0]) == 12 and ans[1] > 0) 
    ans = app.getDeals(fromDate= "2021-01-21",splitMonths = True)
    assert(len(ans[0]) == 12 and ans[1] > -1) 
    ans = app.getDeals(fromDate= "2021")
    assert(len(ans[0]) >= 0 and ans[1] > -1) 
    ans = app.getDeals(fromDate= "2021-01-21",nbrOfYears=0)
    assert(len(ans[0]) == 0 and ans[1] == 0) 

def testgetCompanies(): 
    ansNotSplit = app.getCompanies(False)
    ansSplit = app.getCompanies(True)
    assert(len(ansSplit) == 5)  

def testformatNumber(): 
    nbr = app.formatNumber(293938463092028)
    assert(str(nbr).__contains__(" "))





