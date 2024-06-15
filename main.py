from flask import Flask, render_template, request, redirect, url_for  #url_for is used to build a URL for a specific view function

#It marks a string as safe for rendering in HTML templates(otherwise Jinjia might ignore it)
from markupsafe import Markup

#For accessing the .env file
import os
from dotenv import load_dotenv
import requests

#Helps convert string to datetime object
from datetime import datetime as dt

#Implements in memory file like object(When you dont want to create files on disk)
from io import StringIO

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

matplotlib.use('Agg')  #Non interactive backend(for non GUI stuff since we are not displaying the graph but saving the picture)

#loading .env(from current working directory) and getting the api key
load_dotenv()
AV_KEY = os.getenv("AV_KEY")

function_mapping = {
   "TIME_SERIES_DAILY": "Time Series (Daily)",
   "TIME_SERIES_WEEKLY": "Weekly Time Series",
   "TIME_SERIES_MONTHLY": "Monthly Time Series"
}

app = Flask(__name__)   #Flask uses __name__ to set up paths relative to the current module (whether it's run directly or imported).

@app.route('/')  #Calls function when root page is visited(Decorator)
def index():
    if "error" in request.args:
        return render_template('index.html', error=request.args['error'])
    return render_template("index.html")

@app.route('/info', methods=['GET','POST'])
def info():
    if request.method == 'GET':
        return redirect('/')
    
    form_data = request.form     #Gives it as a dictionary
    symbol = form_data["symbol"]
    function = form_data["interval"]
    print(symbol, function)

    overview_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={AV_KEY}"   #f string is used so as the replace vals in {}
    company_overview = requests.get(overview_url).json()   #.json() converts from json to dictionary

    if 'Name' not in company_overview:
        return redirect(url_for('index', error="Invalid ticker symbol"))  #Format - url_for(name of view function,parameters to be sent)
    company_name = company_overview["Name"]

    url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={AV_KEY}"
    stock_data = requests.get(url).json()

    func_key = function_mapping[function]
    time_series = stock_data[func_key]

    dates = []
    prices = []
   
    for k, v in time_series.items():       #.items() helps us access key value pair as tuples
        formatted_date = dt.strptime(k, "%Y-%m-%d").date()
        dates.append(formatted_date)
        prices.append(float(v['2. high']))
 
    dates.reverse()
    prices.reverse()

    graph = get_graph(dates, prices, company_name)

    return render_template("info.html", info={
    "company_name": company_name,
    "symbol": symbol,
    "graph": Markup(graph)
    })

def get_graph(dates, prices, company_name):
    fig, ax = plt.subplots(figsize=(8, 6))   #figure and axes objects
 
    ax.xaxis.set_tick_params(rotation=45)
    ax.set_title(f"Stock Price of {company_name}")
    ax.set_xlabel("Year")
    ax.set_ylabel("Price (USD)")
    ax.plot(dates, prices)
 
    buf = StringIO()
    fig.savefig(buf, format="svg")
    plt.close(fig)
 
    return buf.getvalue()    #returns svg content of buffer as a string

if __name__ == '__main__':   #If we run this module __name__ will be set to __main__
    app.run(debug=True)      #Provides info in case of error and automatically reloads if code changes

#Flask uses the jinjia templating engine which goes through our html and and replaces the block with the respective data and produces a final output
#__name__ changes depending on if you are running this module or if the code is importing the module for another module
