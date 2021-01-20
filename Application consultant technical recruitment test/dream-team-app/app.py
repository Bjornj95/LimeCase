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

updateFreq = 60*60 #In seconds 
updateFreqNews = 4 #In seconds 

#Disable warning to clean up cmd 
requests.packages.urllib3.disable_warnings()

#My functions 
def _getDeals(): 
    '''
    Returns all deals from server 
    '''
    global timeSinceDealsRequest
    global Deals
    global updatedTime

    newRequestMade = False 

    startTime = time.time() 
    if timeSinceDealsRequest == None:
        timeSinceDealsRequest = -updateFreq

    if time.time() - timeSinceDealsRequest > updateFreq: 
        newRequestMade = True 
        base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
        params = "?_limit=50" #Någonsting blir konstigt med sorteringen... 
        url = base_url + params
        Deals = get_api_data(headers=headers, url=url)
        
        timeSinceDealsRequest = time.time()
        updatedTime = str(datetime.today())

    print("**In _getDeals** Deals found: ", len(Deals), ". Took ", time.time()-startTime, " seconds. New request: ", newRequestMade)

    return Deals

def _getCompanies(): 
    '''
    Returns all deals from server 
    '''
    global timeSinceCompaniesRequest
    global Companies
    global updatedTime

    newRequestMade = False 

    startTime = time.time() 
    if timeSinceCompaniesRequest == None:
        timeSinceCompaniesRequest = -updateFreq

    if time.time() - timeSinceCompaniesRequest > updateFreq: 
        newRequestMade = True 
        base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/company/"
        params = "?_limit=50"
        url = base_url + params
        Companies = get_api_data(headers=headers, url=url)
        timeSinceCompaniesRequest = time.time() 
        updatedTime = str(datetime.today())

    print("**In _getCompanies** Deals found: ", len(Companies), ". Took ", time.time()-startTime, " seconds. New request: ", newRequestMade)

    return Companies

def getDeals(fromDate = False, nbrOfYears = 1, splitMonths = False):
    '''
    Used to get deals since date provided (if fromDate is not set all deals are returned). 

    Total value and average value of the deals are also returned.  

    fromYear determins a specific year to get deals from. If only year is provided deals from that year is returned, if full date (20xx-xx-xx) is used deals from one year period (specified by nbrOfYears) is returned
    
    If splitMonth is set to True a list containing number of deals each month will be returned where indices correspond to month

    Returns List of deals, Total value, Average value, Number of deals
    '''

    startTime = time.time() 

    deals = _getDeals() 
    returnedDeals = []

    totalValueFromDeals = 0 
    averageValue = 0

    if fromDate != False: #If not all deals 
        for deal in deals: 
            #If the deal belongs to the year requested 
            if len(fromDate.split("-")) == 1:
                if deal['closeddate'] != None and deal['dealstatus']['key'] == 'agreement':
                    dealYear = deal['closeddate'].split("-")[0]
                    fromYear = fromDate.split("-")[0]
                    if dealYear == fromYear: 
                        returnedDeals.append(deal)

            #If the deal belongs to the time period requested 
            else:
                if deal['closeddate'] != None and deal['dealstatus']['key'] == 'agreement':
                    dealYear = datetime.strptime(deal['closeddate'].split("T")[0],"%Y-%m-%d")
                    fromYear = datetime.strptime(fromDate,"%Y-%m-%d")
                    if dealYear > fromYear and dealYear < (fromYear + relativedelta(years=nbrOfYears)): 
                        returnedDeals.append(deal)

    #If all deals are requested 
    else: 
        returnedDeals = []
        tempList = deals 
        #Removes deals that are not agreements 
        for deal in tempList: 
            if deal['dealstatus']['key'] != 'agreement': 
                returnedDeals.append(deal)
                


    #Calculate total and average deal value if time period is chosen 
    for deal in returnedDeals:
        """If one want insight in deals gathered 
        print(deal['name'])
        print(int(deal['value']))
        print(deal['dealstatus']['id'])
        print("-------------------------")
        """

        totalValueFromDeals += int(deal['value']) 

    if len(returnedDeals) > 0: 
        averageValue = str(totalValueFromDeals/len(returnedDeals))

    if splitMonths != False: 
        deals = returnedDeals
        returnedDeals = [0,0,0,0,0,0,0,0,0,0,0,0]
        for deal in deals: 
            if deal['dealstatus']['key'] == 'agreement':
                month = int(deal['closeddate'].split("-")[1])
                returnedDeals[month-1] += 1


    print("**In getDealsFromDate** Deals found: ", len(returnedDeals), ". Took ", time.time()-startTime, " seconds.")


    return returnedDeals, totalValueFromDeals, averageValue, len(returnedDeals)

def getCompanies(split = False, offset = 0): 
    '''
    Get info about companies, if split is set to True Four lists are returned. One with only companies that bought the last year (customers), one with companies that never bought (prospects), 
    one with companies that havn't bought last year (inactive) and one with others/notinterested.

    If split is not set all companies are returned 

    offset can be set to get companies from different timeperiods. Default is to get from last year, offset is in relation to this 

    Returns list(s) of companies as Limeobjects. Customers, prospects, inactives, others and dictionary containing company:dealValue for customers 
    '''
    startTime = time.time() 

    if split: 
        customers = []
        prospects = []
        inactives = []
        others = []

        companyDealsDict = {}
        
        dealsFromOneYearBack,d1,d2,d3 = getDeals(fromDate=(datetime.today()-relativedelta(years=1+offset)).strftime('%Y-%m-%d'))
        dealsFromLastYear = getDeals(fromDate=(datetime.today()-relativedelta(years=1+offset)).strftime('%Y'))[0]
        allDeals = getDeals()[0]
        response_companies = _getCompanies()

        for company in response_companies: 
            customerBool = False 
            inactiveBool = False 

            #To find customers 
            for deal in dealsFromOneYearBack: 
                if deal['company'] == company['_id']:
                    customerBool = True


            #To build dictionary with customers deals from last year 
            for deal in dealsFromLastYear: 
                if deal['company'] == company['_id']:
                    if company['name'] in companyDealsDict:
                        companyDealsDict[company['name']] += deal['value']
                    else: 
                        companyDealsDict[company['name']] = deal['value']


            if customerBool: 
                customers.append(company)
            else: 
                #To find inactives, could remove deals from the last year to speed things up 
                for deal in allDeals: 
                    if deal['company'] == company['_id'] and deal['closeddate'] != None:
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
        response_companies = _getCompanies()

        print("**In getCompanyInfo** Number of companies: ",len(response_companies)) #Hur kan detta vara 111 när limit är 50? 

        return response_companies
    
def getNewsItems(): 

    global timeSinceNewsUpdated
    global NewsItems
    global updatedTime

    startTime = time.time() 
    if timeSinceNewsUpdated == None:
        timeSinceNewsUpdated = -updateFreqNews

    if time.time() - timeSinceNewsUpdated > updateFreqNews: 
        #Get latest deal 
        url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/?_limit=1&_sort=-closeddate"

        deal = requests.get(url=url,
                                headers=headers,
                                data=None,
                                verify=False)

        json_data = json.loads(deal.text)
        deal = json_data.get("_embedded").get("limeobjects")

        #Find seller 
        lastDealBy = requests.get(url=deal[0]['_links']['relation_coworker']['href'],
                                headers=headers,
                                data=None,
                                verify=False)

        lastDealBy = json.loads(lastDealBy.text)
        print("Name is: ",lastDealBy['name'])
        NewsItems = lastDealBy['name']
        
        timeSinceNewsUpdated = time.time()
        updatedTime = str(datetime.today())
    
    return ["Congratulations to " + NewsItems + " for our latest deal: " + deal[0]['name'] + "!"]

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
    
    return render_template('home.html',News = getNewsItems(), upt = updatedTime)


#Deals page 
@app.route('/deals')
def deals():
    labelsAndDataDict = []
    #Get data about deals
    dummy,totalValueFromDealsLastYear, averageValueFromDealsLastYear, numberOfDealsLastYear = getDeals(fromDate=str(datetime.today().year-1))
    previousYearsValues = getDeals(fromDate=str(datetime.today().year-2))

    #Total value from deals 
    comparedToLastYear = str(round(totalValueFromDealsLastYear/previousYearsValues[1]))
    labelsAndDataDict.append({'data': 'Total value of deals','value':str(formatNumber(totalValueFromDealsLastYear)) + " SEK ("+comparedToLastYear +"% compared to " + str(datetime.today().year-2) + ")"})

    #Add average deal value to dict
    comparedToLastYear = str(round(float(averageValueFromDealsLastYear)/float(previousYearsValues[2])))
    labelsAndDataDict.append({'data': 'Average value of deals','value':str(formatNumber(averageValueFromDealsLastYear)) + " SEK ("+comparedToLastYear +"% compared to " + str(datetime.today().year-2) + ")"})

    #Data large for chart 
    dealsList = []
    yearsList = []
    for i in range(6): 
        dealsList.append(getDeals(fromDate=str(datetime.today().year-i),splitMonths=True)[0])
        yearsList.append(datetime.today().year-i)


    #Deal value for each customer last year and building data to small chart 
    smallChart = [] #Contains company names and revenue 
    temp = [] #Used temporarily store the list of costumers and revenues 
    customerRevenueDict = [] #List of dictionaries containing customers and revenue each year 
    for in in range(6): 
    valuePerCompany = getCompanies(True)[4]
    
    for i,entry in enumerate(valuePerCompany): 
        temp.append(entry + ": " +str(formatNumber(valuePerCompany[entry])))
        smallChart.append([])
        smallChart[-1].append(entry)
        smallChart[-1].append(valuePerCompany[entry])
    valuePerCompany = temp

    labelsAndDataDict.append({'data': 'Deal value of all customers','value':valuePerCompany})


    return render_template('deals.html',items=labelsAndDataDict,dealsList = dealsList, upt = updatedTime, yearsList = yearsList,smallChart = smallChart) #, revenueList = revenueList

#Deals page 
@app.route('/companies')
def companies():
    #Find customers and rest 
    toWebpage = []
    comps = getCompanies(True)[0:4]

    #print(comps)

    for group in comps: 
        companiesString = []
        for company in group: 
            #print(company)
            companiesString.append(company['name'])
        toWebpage.append({'Title':"Customers",'companies': companiesString})


    toWebpage[1]['Title'] = "Prospects"
    toWebpage[2]['Title'] = "Inactives"
    toWebpage[3]['Title'] = "Others/Not interested"

    return render_template('companies.html',items=toWebpage, upt = updatedTime) #,dealsList = dealsList


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
