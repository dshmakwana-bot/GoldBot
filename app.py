from flask import Flask
import requests
from datetime import datetime, timedelta
import time
import json
import os


app = Flask(__name__)

DATA_FILE="prices.json"

logs=[]
last_scan=0


# =====================
# STORAGE
# =====================

def load_prices():

    if os.path.exists(DATA_FILE):

        try:
            with open(DATA_FILE,"r") as f:
                return json.load(f)

        except:
            return []

    return []



def save_prices(prices):

    with open(DATA_FILE,"w") as f:
        json.dump(prices,f)



prices=load_prices()



# =====================
# INDICATORS
# =====================

def ema(data,p):

    v=data[0]

    k=2/(p+1)

    for x in data[1:]:

        v=x*k+v*(1-k)

    return v



def rsi(data):

    if len(data)<15:

        return 50


    gains=[]
    losses=[]


    for i in range(1,len(data)):

        d=data[i]-data[i-1]

        gains.append(max(d,0))

        losses.append(abs(min(d,0)))


    gain=sum(gains[-14:])/14

    loss=sum(losses[-14:])/14


    if loss==0:

        return 100


    rs=gain/loss


    return 100-(100/(1+rs))




# =====================
# GOLD PRICE
# =====================

def get_price():

    data=requests.get(
        "https://api.gold-api.com/price/XAU",
        timeout=10
    ).json()


    return float(data["price"])




# =====================
# STRATEGY
# =====================

def analyse(price):


    if len(prices)<25:


        return (

        "Collecting",

        len(prices),

        0,

        "-",

        "-",

        "Need 25 points"

        )



    e9=ema(prices[-20:],9)

    e21=ema(prices[-40:],21)


    rr=rsi(prices)


    high=max(prices[-10:])

    low=min(prices[-10:])


    movement=high-low



    if movement<1.5:


        return (

        "⚪ WAIT",

        40,

        rr,

        "-",

        "-",

        "Low volatility"

        )



    # BUY

    score=0

    reason=[]


    if e9>e21:

        score+=30

        reason.append("Trend")


    if price>prices[-3]:

        score+=30

        reason.append("Momentum")


    if 45<rr<70:

        score+=30

        reason.append("RSI")


    if score>=70:


        return (

        "🟢 BUY" if score<90 else "🔥 STRONG BUY",

        score,

        rr,

        round(price-2,2),

        round(price+5,2),

        ",".join(reason)

        )




    # SELL

    score=0

    reason=[]


    if e9<e21:

        score+=30

        reason.append("Trend")


    if price<prices[-3]:

        score+=30

        reason.append("Momentum")


    if 30<rr<55:

        score+=30

        reason.append("RSI")



    if score>=70:


        return (

        "🔴 SELL" if score<90 else "🔥 STRONG SELL",

        score,

        rr,

        round(price+2,2),

        round(price-5,2),

        ",".join(reason)

        )



    return (

    "⚪ WAIT",

    50,

    rr,

    "-",

    "-",

    "No setup"

    )




# =====================
# SCANNER
# =====================

def scan():

    global last_scan


    if time.time()-last_scan<60:

        return


    last_scan=time.time()



    price=get_price()


    prices.append(price)

    prices[:] = prices[-200:]


    save_prices(prices)


    sig,conf,rr,sl,tp,reason=analyse(price)



    ist=datetime.utcnow()+timedelta(
        hours=5,
        minutes=30
    )



    logs.insert(0,{

    "time":ist.strftime("%H:%M:%S"),

    "signal":sig,

    "confidence":conf,

    "price":round(price,2),

    "rsi":round(rr,2),

    "sl":sl,

    "tp":tp,

    "reason":reason

    })


    logs[:] = logs[:100]





# =====================
# WEBSITE
# =====================

@app.route("/")

def home():


    try:

        scan()

    except Exception as e:

        print(e)



    html="""

<html>

<head>

<meta http-equiv="refresh" content="60">

<style>

body{
background:#111;
color:white;
font-family:Arial;
}

table{
width:100%;
border-collapse:collapse;
font-size:12px;
}

td,th{
padding:7px;
border-bottom:1px solid #444;
text-align:center;
}

th{
background:#333;
}

</style>

</head>

<body>


<h2>🥇 XAU CLOUD V4</h2>


<table>

<tr>

<th>Time</th>
<th>Signal</th>
<th>%</th>
<th>XAU</th>
<th>RSI</th>
<th>SL</th>
<th>TP</th>
<th>Reason</th>

</tr>

"""


    for x in logs:


        html+=f"""

<tr>

<td>{x['time']}</td>

<td>{x['signal']}</td>

<td>{x['confidence']}</td>

<td>{x['price']}</td>

<td>{x['rsi']}</td>

<td>{x['sl']}</td>

<td>{x['tp']}</td>

<td>{x['reason']}</td>

</tr>

"""


    return html+"</table></body></html>"
