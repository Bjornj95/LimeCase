# To solve your task you might (or might not) need to import additional libraries
from flask import Flask, render_template, redirect, url_for, request, logging
from dateutil.parser import parse
from datetime import datetime
import requests
import json

#my imports 
from datetime import datetime

app = Flask(__name__, static_url_path='/static')

# Headers for REST API call. 
# Paste the API-key you have been provided as the value for "x-api-key"
headers = {
        "Content-Type": "application/json",
        "Accept": "application/hal+json",
        "x-api-key": "860393E332148661C34F8579297ACB000E15F770AC4BD945D5FD745867F590061CAE9599A99075210572"
        }

#Variables
totalValueFromDealsLastYear = 0 
averageValueFromDealsLastYear = 0
numberOfDealsLastYear = 0
labelsAndDataDict = []

#My functions 
def getDealsFromDate(ownDate = False): 
    '''
    Calculates total value from deals since date provided (default is last year) and average value of the deals. 

    Returns List of deals, Total, Average, Number of deals
    '''
    if not ownDate: 
        today = list(str(datetime.date(datetime.now())))
        today[3] = "0"
        today = "".join(today)
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    params = "?_limit=50&min-closeddate="+str(today)+"T23:59Z"
    url = base_url + params
    response_deals = get_api_data(headers=headers, url=url)

    totalValueFromDealsLastYear = 0 
    for deal in response_deals:
        totalValueFromDealsLastYear += int(deal['value']) 
    averageValue = str(totalValueFromDealsLastYear/len(response_deals))


    return response_deals, totalValueFromDealsLastYear, averageValue,len(response_deals)

def getAllDeals(): 
    '''
    Returns all deals
    '''
    base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/deal/"
    params = "?_limit=50"
    url = base_url + params
    response_deals = get_api_data(headers=headers, url=url)

    print(len(response_deals), " deals found")

    return response_deals

def getCompanyInfo(split = False ): 
    '''
    Get info about companies, if split is set to True Four lists are returned. one with only companies that bought the last year (customers), one with comapnies that never bought (prospects), 
    one with companies that havn't bought last year (inactive) and one with others/notinterested

    Returns list(s) of companies as Limeobjects. Customers, prospects, inactives, others
    '''
    if split: 
        customers = []
        prospects = []
        inactives = []
        others = []
        

        dealsFromLastYear,d1,d2,d3 = getDealsFromDate()
        allDeals = getAllDeals() 
        base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/company/"
        params = "?_limit=50"
        url = base_url + params
        response_companies = get_api_data(headers=headers, url=url)

        for company in response_companies: 
            customerBool = False 
            inactiveBool = False 

            #To find customers 
            for deal in dealsFromLastYear: 
                if deal['company'] == company['_id']:
                    customerBool = True

            if customerBool: 
                customers.append(company)
            else: 
                #To find inactives 
                for deal in allDeals: 
                    if deal['company'] == company['_id']:
                        inactiveBool = True 
                if inactiveBool: 
                    inactives.append(company)
                else: 
                    #To find comapnies that have never bought. Can be both proscpects and notinterested 
                    if company['buyingstatus']['key'] == "notinterested":
                        others.append(company)
                    else: 
                        prospects.append(company)

        
                
        
        print("Number of customers: ", len(customers), " number of prospects: ",len(prospects)," number of inactives: ", len(inactives), " number of others: ",len(others)) #Hur kan detta vara 111 när limit är 50? 
        return customers, prospects, inactives,others 



    else: 
        base_url = "https://api-test.lime-crm.com/api-test/api/v1/limeobject/company/"
        params = "?_limit=50"
        url = base_url + params
        response_companies = get_api_data(headers=headers, url=url)

        print("number of companies: ",len(response_companies)) #Hur kan detta vara 111 när limit är 50? 

        return response_companies


# Example of function for REST API call to get data from Lime
def get_api_data(headers, url):
	# First call to get first data page from the API
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

        """
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
	return render_template('home.html')


#Deals page 
@app.route('/deals')
def deals():
    labelsAndDataDict = []
    #Get data about deals last year
    dummy,totalValueFromDealsLastYear, averageValueFromDealsLastYear, numberOfDealsLastYear = getDealsFromDate() 

    #Total value from deals 
    labelsAndDataDict.append({'data': 'Total value of deals','value':str(round(float(totalValueFromDealsLastYear)))})

    #Add average deal value to dict
    labelsAndDataDict.append({'data': 'Average value of deals','value':str(round(float(averageValueFromDealsLastYear)))})

    #Total from deals spread over 12 months 
    numberOfDealsPerMonth = str(numberOfDealsLastYear/12)
    labelsAndDataDict.append({'data': 'Average number of deals won each month','value':str(round(float(numberOfDealsPerMonth),2))})

    #Win / costumer 
    companiesList = getCompanyInfo(True)
    labelsAndDataDict.append({'data': 'Value of won deals per customer','value':str(round(totalValueFromDealsLastYear/len(companiesList[0])))})

    """
    companiesList = getCompanyInfo(True)
    labelsAndDataDict.append({'data': 'Total value of won deals per customer','value':str(round(totalValueFromDealsLastYear/len(companiesList[0])))})
    """

    return render_template('deals.html', deals=companiesList,items=labelsAndDataDict)

#Deals page 
@app.route('/companies')
def companies():
    #Find customers and rest 
    toWebpage = []
    comps = getCompanyInfo(True)

    """
    for group in comps: 
        companiesString = ""
        for company in group: 
            companiesString += company['name'] + "<br>"
        toWebpage.append({'Title':"Customers",'companies': companiesString})
    """

    for group in comps: 
        companiesString = []
        for company in group: 
            companiesString.append(company['name'])
        toWebpage.append({'Title':"Customers",'companies': companiesString})

    toWebpage[1]['Title'] = "Prospects"
    toWebpage[2]['Title'] = "Inactives"
    toWebpage[3]['Title'] = "Others/Not interested"

    return render_template('companies.html',items=toWebpage,test= {"test":"Funkar"})


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
