from flask import Flask
import requests
from datetime import datetime, timedelta
import time


app = Flask(__name__)


logs=[]
prices=[]
last_scan=0



# ========= EMA =========

def ema(data,p):

    value=data[0]

    k=2/(p+1)


    for x in data[1:]:

        value=x*k+value*(1-k)


    return value



# ========= RSI =========

def rsi(data):


    if len(data)<8:

        return 50


    gains=[]
    losses=[]


    for i in range(1,len(data)):


        d=data[i]-data[i-1]


        gains.append(max(d,0))

        losses.append(abs(min(d,0)))



    gain=sum(gains[-7:])/7

    loss=sum(losses[-7:])/7



    if loss==0:

        return 100



    rs=gain/loss


    return 100-(100/(1+rs))




# ========= PRICE =========

def gold_price():


    data=requests.get(

        "https://api.gold-api.com/price/XAU",

        timeout=10

    ).json()



    return float(data["price"])





# ========= SCANNER =========

def scan():


    global last_scan



    if time.time()-last_scan < 60:

        return



    last_scan=time.time()



    price=gold_price()



    prices.append(price)



    prices[:] = prices[-100:]



    if len(prices)<5:



        signal="Collecting"

        conf=0

        rr=0

        sl="-"

        tp="-"



    else:



        fast=ema(prices[-5:],3)


        slow=ema(

            prices,

            min(8,len(prices))

        )



        rr=rsi(prices)



        momentum=prices[-1]-prices[-3]



        signal="⚪ WAIT"

        conf=50

        sl="-"

        tp="-"



        if fast>slow and momentum>0:



            signal="🟢 BUY"

            conf=85


            sl=round(price-2,2)

            tp=round(price+4,2)




        elif fast<slow and momentum<0:



            signal="🔴 SELL"

            conf=85


            sl=round(price+2,2)

            tp=round(price-4,2)





    ist=datetime.utcnow()+timedelta(

        hours=5,

        minutes=30

    )



    logs.insert(

        0,

        {


        "time":ist.strftime("%H:%M:%S"),

        "signal":signal,

        "confidence":conf,

        "price":round(price,2),

        "rsi":round(rr,2),

        "sl":sl,

        "tp":tp


        }

    )



    logs[:] = logs[:100]





# ========= WEBSITE =========

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

font-size:13px;

}


td,th{

padding:8px;

border-bottom:1px solid #444;

text-align:center;

}


th{

background:#333;

}

</style>


</head>


<body>


<h2>⚡ XAU SCALPER CLOUD</h2>


<table>


<tr>

<th>Time</th>

<th>Signal</th>

<th>%</th>

<th>XAU</th>

<th>RSI</th>

<th>SL</th>

<th>TP</th>


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

</tr>


"""



    html+="</table></body></html>"



    return html
