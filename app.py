from flask import Flask
import requests
from datetime import datetime, timedelta
import time


app = Flask(__name__)

logs=[]
prices=[]
last_scan=0


# =====================
# EMA
# =====================

def ema(data,p):

    v=data[0]

    k=2/(p+1)

    for x in data[1:]:

        v=x*k+v*(1-k)

    return v



# =====================
# RSI
# =====================

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
# PRICE
# =====================

def get_price():

    data=requests.get(
        "https://api.gold-api.com/price/XAU",
        timeout=10
    ).json()

    return float(data["price"])




# =====================
# STRATEGY ENGINE
# =====================

def analyse(price):


    if len(prices)<25:


        return (
            "Collecting",
            0,
            0,
            "-",
            "-",
            "Building data"
        )



    e9=ema(prices[-20:],9)

    e21=ema(prices[-40:],21)


    rr=rsi(prices)


    recent_high=max(prices[-10:])

    recent_low=min(prices[-10:])


    movement=recent_high-recent_low


    score=0

    reason=[]



    # avoid flat market

    if movement<1.5:


        return (

        "⚪ WAIT",

        40,

        rr,

        "-",

        "-",

        "Low movement"

        )




    # BUY checks


    if e9>e21:


        score+=30

        reason.append("Trend")


    if price>recent_high-0.5:


        score+=20

        reason.append("Breakout")


    if 45<rr<65:


        score+=25

        reason.append("RSI")



    if price>prices[-3]:


        score+=25

        reason.append("Momentum")



    if score>=75:


        if score>=90:

            signal="🔥 STRONG BUY"


        else:

            signal="🟢 BUY"



        return (

        signal,

        score,

        rr,

        round(price-2,2),

        round(price+5,2),

        ",".join(reason)

        )




    # SELL checks


    score=0

    reason=[]


    if e9<e21:


        score+=30

        reason.append("Trend")



    if price<recent_low+0.5:


        score+=20

        reason.append("Breakdown")



    if 35<rr<55:


        score+=25

        reason.append("RSI")



    if price<prices[-3]:


        score+=25

        reason.append("Momentum")



    if score>=75:


        if score>=90:

            signal="🔥 STRONG SELL"

        else:

            signal="🔴 SELL"



        return (

        signal,

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
# SCAN
# =====================

def scan():

    global last_scan


    if time.time()-last_scan<60:

        return


    last_scan=time.time()


    price=get_price()


    prices.append(price)


    prices[:] = prices[-200:]


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





@app.route("/")

def home():

    scan()


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


<h2>🥇 XAU PRO SCALPER V3</h2>


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

<td>{x['confidence']}%</td>

<td>{x['price']}</td>

<td>{x['rsi']}</td>

<td>{x['sl']}</td>

<td>{x['tp']}</td>

<td>{x['reason']}</td>

</tr>

"""



    return html+"</table></body></html>"
