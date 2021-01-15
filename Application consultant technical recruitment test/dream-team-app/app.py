# To solve your task you might (or might not) need to import additional libraries
from flask import Flask, render_template, redirect, url_for, request, logging
from dateutil.parser import parse
from datetime import datetime
import requests
import json

#my imports 
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import locale
locale.setlocale(locale.LC_ALL, '')

app = Flask(__name__, static_url_path='/static')

# Headers for REST API call. 
# Paste the API-key you have been provided as the value for "x-api-key"
headers = {
        "Content-Type": "application/json",
        "Accept": "application/hal+json",
        "x-api-key": "860393E332148661C34F8579297ACB000E15F770AC4BD945D5FD745867F590061CAE9599A99075210572"
        }

#Variables
Deals = []
Companies = []
NewsItems = []

timeSinceDealsRequest = None
timeSinceCompaniesRequest = None 
timeSinceNewsUpdated = None 
updatedTime = None 

updateFreq = 120 #In seconds 

#Disable warning to clean up cmd 
requests.packages.urllib3.disable_warnings()

#My functions 
def _getDeals(): 
    global timeSinceDealsRequest
    global Deals
    global updatedTime

    startTime = time.time() 
    if timeSinceDealsRequest == None:
        timeSinceDealsRequest = -updateFreq

    if time.time() - timeSinceDealsRequest > updateFreq: 
        print("New requests made")
        base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
        params = "?_limit=50&_sort=closeddate"
        url = base_url + params
        Deals = get_api_data(headers=headers, url=url)
        
        timeSinceDealsRequest = time.time()
        updatedTime = str(datetime.today())

    print("**In _getDeals** Deals found: ", len(Deals), ". Took ", time.time()-startTime, " seconds.")

    return Deals

def _getCompanies(): 
    global timeSinceCompaniesRequest
    global Companies
    global updatedTime

    startTime = time.time() 
    if timeSinceCompaniesRequest == None:
        timeSinceCompaniesRequest = -updateFreq

    if time.time() - timeSinceCompaniesRequest > updateFreq: 
        print("New requests made")
        base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/company/"
        params = "?_limit=50"
        url = base_url + params
        Companies = get_api_data(headers=headers, url=url)
        timeSinceCompaniesRequest = time.time() 
        updatedTime = str(datetime.today())

    print("**In _getCompanies** Deals found: ", len(Companies), ". Took ", time.time()-startTime, " seconds.")

    return Companies

def getDeals(fromDate = False, nbrOfYears = 1, splitMonths = False):
    '''
    Calculates total value from deals since date provided (default is to get all deals) and average value of the deals. 

    fromYear determins a specific year to get deals from. If splitMonth is set to True a list containing number of deals each month will be returned where indices correspond to month

    Returns List of deals, Total value, Average value, Number of deals
    '''

    startTime = time.time() 

    deals = _getDeals() 
    returnedDeals = []

    totalValueFromDeals = 0 
    averageValue = 0

    if fromDate != False: #If certain deals are to be extracted 
        for deal in deals: 
            #If the deal belongs to the time period requested 
            if deal['closeddate'] != None:
                dealYear = deal['closeddate'].split("-")[0]
                fromYear = fromDate.split("-")[0]
                #print("--------------------Titta här-------------------",dealYear,fromYear)
                if dealYear == fromYear: 
                    returnedDeals.append(deal)


        if splitMonths != False: 
                deals = returnedDeals
                returnedDeals = [0,0,0,0,0,0,0,0,0,0,0,0]
                for deal in deals: 
                    month = int(deal['closeddate'].split("-")[1])
                    returnedDeals[month-1] += 1

        else: 
            for deal in returnedDeals:
                totalValueFromDeals += int(deal['value']) 

            if len(returnedDeals) > 0: 
                averageValue = str(totalValueFromDeals/len(returnedDeals))

    else: 
        returnedDeals = deals


    print("**In getDealsFromDate** Deals found: ", len(returnedDeals), ". Took ", time.time()-startTime, " seconds.")


    return returnedDeals, totalValueFromDeals, averageValue, len(returnedDeals)

def getCompanies(split = False ): 
    '''
    Get info about companies, if split is set to True Four lists are returned. One with only companies that bought the last year (customers), one with companies that never bought (prospects), 
    one with companies that havn't bought last year (inactive) and one with others/notinterested

    Returns list(s) of companies as Limeobjects. Customers, prospects, inactives, others and dictionary containing company:dealValue
    '''
    startTime = time.time() 

    if split: 
        customers = []
        prospects = []
        inactives = []
        others = []

        companyDealsDict = {}
        
        #This could be optimized by not getting last years deals twice 
        dealsFromLastYear,d1,d2,d3 = getDeals(fromDate="2020")
        allDeals = getDeals()[0]
        response_companies = _getCompanies()

        for company in response_companies: 
            customerBool = False 
            inactiveBool = False 

            #To find customers 
            for deal in dealsFromLastYear: 
                if deal['company'] == company['_id']:
                    customerBool = True
                    print(deal['value'])
                    if company['name'] in companyDealsDict:
                        companyDealsDict[company['name']] += deal['value']
                    else: 
                        companyDealsDict[company['name']] = deal['value']


            if customerBool: 
                customers.append(company)
            else: 
                #To find inactives, could remove deals from the last year to speed things up 
                for deal in allDeals: 
                    if deal['company'] == company['_id']:
                        inactiveBool = True 
                        break
                if inactiveBool: 
                    inactives.append(company)
                else: 
                    #To find comapnies that have never bought. Can be both proscpects and notinterested 
                    if company['buyingstatus']['key'] == "notinterested":
                        others.append(company)
                    else: 
                        prospects.append(company)

        print("**In getCompanyInfo** Number of customers: ", len(customers), " number of prospects: ",len(prospects)," number of inactives: ", len(inactives), " number of others: ",len(others), ". Took ", time.time()-startTime, " seconds.") #Hur kan detta vara 111 när limit är 50? 
        return customers, prospects, inactives,others, companyDealsDict



    else: 
        base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/company/"
        params = "?_limit=50"
        url = base_url + params
        response_companies = get_api_data(headers=headers, url=url)

        print("**In getCompanyInfo** Number of companies: ",len(response_companies)) #Hur kan detta vara 111 när limit är 50? 

        return response_companies

def getDealsLastYears(numberYears = 5): 
    '''
    Returns a list of integers conatining the number of deals for that year and value of the deals (10s of milions). Most recent year is first in the list. 
    '''
    startTime = time.time() 

    dealsEachYear = []

    #For adding statistics about revenues each year
    revenueEachYear = []
    #averageRevenueEachYear = [] not currently used 

    for i in range(numberYears):
        y = datetime.today().year - i
        response_deals = getDeals(str(y))

        """
        fromDate =  str(datetime.date(datetime.now() - relativedelta(years=i+1)))
        base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
        params = "?_limit=50&min-closeddate="+str(fromDate)+"T23:59Z&_sort=closeddate"
        if i > 0: 
            params = "?_limit=50&min-closeddate="+str(fromDate)+"T23:59Z&max-closeddate="+str(lastDate)+"T23:59Z&_sort=closeddate"
        url = base_url + params
        print("URL: ",url)
        response_deals = get_api_data(headers=headers, url=url)
        """

        dealsEachYear.append(len(response_deals))

        #lastDate = fromDate
        
        totalValueFromDealsLastYear = 0
        for deal in response_deals[0]:
            totalValueFromDealsLastYear += int(deal['value']/10000000) #/10 000 000 to fit the axis 
        revenueEachYear.append(str(totalValueFromDealsLastYear))
 


    print("**In getDealsLastYears** Number of deals each year: ", dealsEachYear, " revenue each year: ", revenueEachYear, ". Took ", time.time()-startTime, " seconds.")


    return dealsEachYear, revenueEachYear
    
def getNewsItems(): 

    global timeSinceNewsUpdated
    global NewsItems
    global updatedTime

    startTime = time.time() 
    if timeSinceNewsUpdated == None:
        timeSinceNewsUpdated = -updateFreq

    if time.time() - timeSinceNewsUpdated > updateFreq: 
        #Get deals
        deals = getDeals(fromDate=str(datetime.today().year-1))

        #Find last sale
        lastDealBy = requests.get(url=deals[0][0]['_links']['relation_coworker']['href'],
                                headers=headers,
                                data=None,
                                verify=False)

        lastDealBy = json.loads(lastDealBy.text)
        print("Last deal by: ", lastDealBy)
        print("Name is: ",lastDealBy['name'])
        NewsItems = lastDealBy['name']
        
        timeSinceNewsUpdated = time.time()
        updatedTime = str(datetime.today())
    
    return NewsItems

def formatNumber(nbr): 
    return "{:,d}".format(round(float(nbr))).replace(","," ")


# Example of function for REST API call to get data from Lime
def get_api_data(headers, url):
	# First call to get first data page from the API. 
    response = requests.get(url=url,
                               headers=headers,
                               data=None,
                               verify=False)

    # Convert the response string into json data and get embedded limeobjects
    
    json_data = json.loads(response.text)
    limeobjects = json_data.get("_embedded").get("limeobjects")
    #print(limeobjects)
    
    # Check for more data pages and get thoose too
    nextpage = json_data.get("_links").get("next")
    while nextpage is not None:
        url = nextpage["href"]

        """ Had problem with initial function 
        response = api_request.get(url=url,
                                   headers=headers,
                                   data=None,
                                   verify=False)
        """
        response = requests.get(url=url,
                                   headers=headers,
                                   data=None,
                                   verify=False)

        json_data = json.loads(response.text)
        limeobjects += json_data.get("_embedded").get("limeobjects")
        nextpage = json_data.get("_links").get("next")
        #print(nextpage)

    return limeobjects


# Index page
@app.route('/')
def index():
    
    #Get deals
    deals = getDeals(fromDate=str(datetime.today().year-1))

    #Find last sale
    """
    Took the opportunity to understand how the actual request answers look like
    print(deals)
    print("Numer of deals: ", len(deals))
    print(deals[0][0])
    print("URL: ",deals[0][0]['_links']['relation_coworker']['href'])
    """
    lastDealBy = requests.get(url=deals[0][0]['_links']['relation_coworker']['href'],
                               headers=headers,
                               data=None,
                               verify=False)

    lastDealBy = json.loads(lastDealBy.text)
    print("Last deal by: ", lastDealBy)
    print("Name is: ",lastDealBy['name'])
    
    return render_template('home.html',employee = getNewsItems(), upt = updatedTime)


#Deals page 
@app.route('/deals')
def deals():
    labelsAndDataDict = []
    #Get data about deals last year
    dummy,totalValueFromDealsLastYear, averageValueFromDealsLastYear, numberOfDealsLastYear = getDeals(fromDate=str(datetime.today().year-1))
    previousYearsValues = getDeals(fromDate=str(datetime.today().year-2))

    #Total value from deals 
    comparedToLastYear = str(round(totalValueFromDealsLastYear/previousYearsValues[1]))
    labelsAndDataDict.append({'data': 'Total value of deals','value':str(formatNumber(totalValueFromDealsLastYear)) + " SEK ("+comparedToLastYear +"% compared to " + str(datetime.today().year-1) + ")"})

    #Add average deal value to dict
    comparedToLastYear = str(round(float(averageValueFromDealsLastYear)/float(previousYearsValues[2])))
    labelsAndDataDict.append({'data': 'Average value of deals','value':str(formatNumber(averageValueFromDealsLastYear)) + " SEK ("+comparedToLastYear +"% compared to " + str(datetime.today().year-1) + ")"})

    #Data for chart 
    dealsList = []
    dealsList.append(getDeals(fromDate=str(datetime.today().year-1),splitMonths=True)[0])
    dealsList.append(getDeals(fromDate=str(datetime.today().year-2),splitMonths=True)[0])
    dealsList.append(getDeals(fromDate=str(datetime.today().year-3),splitMonths=True)[0])
    dealsList.append(getDeals(fromDate=str(datetime.today().year-4),splitMonths=True)[0])
    dealsList.append(getDeals(fromDate=str(datetime.today().year-5),splitMonths=True)[0])

    #Deal value for each company last year 
    valuePerCompany = getCompanies(True)[4]
    temp = []
    for entry in valuePerCompany: 
        temp.append(entry + ": " +str(formatNumber(valuePerCompany[entry])))
    valuePerCompany = temp

    labelsAndDataDict.append({'data': 'Deal value of all customers','value':valuePerCompany})


    return render_template('deals.html',items=labelsAndDataDict,dealsList = dealsList, upt = updatedTime) #, revenueList = revenueList

#Deals page 
@app.route('/companies')
def companies():
    #Find customers and rest 
    toWebpage = []
    comps = getCompanies(True)[0:4]

    #print(comps)

    for group in comps: 
        print(len(group))
        companiesString = []
        for company in group: 
            #print(company)
            companiesString.append(company['name'])
        toWebpage.append({'Title':"Customers",'companies': companiesString})

    print(len(toWebpage))
    for i in toWebpage:
        print(i)
    toWebpage[1]['Title'] = "Prospects"
    toWebpage[2]['Title'] = "Inactives"
    toWebpage[3]['Title'] = "Others/Not interested"

    return render_template('companies.html',items=toWebpage,test= {"test":"Funkar"}, upt = updatedTime) #,dealsList = dealsList


# Example page
@app.route('/example')
def example():

	# Example of API call to get deals
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    params = "?_limit=50"
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/company/"
    params = "?_limit=50&name=Abba ab"
    url = base_url + params
    #url = "https://api-test.lime-crm.com/client/"
    response_deals = get_api_data(headers=headers, url=url)

    """
    [YOUR CODE HERE]
    In this exmaple, this is where you can do something with the data in
    'response_deals' before you return it.
    """

    if len(response_deals) > 0:
	    return render_template('example.html', deals=response_deals)
    else:
	    msg = 'No deals found'
	    return render_template('example.html', msg=msg)


# You can add more pages to your app, like this:
@app.route('/myroute')
def myroute():
	mydata = [{'name': 'apple','fame':'Not Fruit'}, {'name': 'mango'}, {'name': 'banana'}]
	return render_template('mytemplate.html', items=mydata)

"""
You also have to create the mytemplate.html page inside the 'templates'
-folder to be rendered. And then add a link to your page in the 
_navbar.html-file, located in templates/includes/
"""

# DEBUGGING
"""
If you want to debug your app, one of the ways you can do that is to use:
import pdb; pdb.set_trace()
Add that line of code anywhere, and it will act as a breakpoint and halt 
your application
"""

if __name__ == '__main__':
	app.secret_key = 'somethingsecret'
	app.run(debug=True)
