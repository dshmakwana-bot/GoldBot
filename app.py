from flask import Flask
import requests
import threading
import time
from datetime import datetime, timedelta


app = Flask(__name__)


logs=[]
prices=[]


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



# =====================
# PRICE
# =====================

def gold_price():

    data=requests.get(
        "https://api.gold-api.com/price/XAU",
        timeout=10
    ).json()


    return float(data["price"])



# =====================
# BOT LOOP
# =====================

def bot():

    while True:


        try:


            price=gold_price()


            prices.append(price)

            prices[:] = prices[-200:]


            if len(prices)<8:


                signal="Collecting"

                conf=0

                rr=0

                sl="-"

                tp="-"



            else:


                fast=ema(prices[-5:],3)

                slow=ema(prices[-10:],8)


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



            logs.insert(0,{

            "time":ist.strftime("%H:%M:%S"),

            "signal":signal,

            "price":round(price,2),

            "confidence":conf,

            "rsi":round(rr,2),

            "sl":sl,

            "tp":tp

            })


            logs[:] = logs[:100]


        except Exception as e:

            print(e)



        time.sleep(60)



threading.Thread(
    target=bot,
    daemon=True
).start()



# =====================
# WEBSITE
# =====================

@app.route("/")

def home():

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
}

td,th{
padding:8px;
text-align:center;
border-bottom:1px solid #444;
}

th{
background:#333;
}

</style>

</head>

<body>


<h2>⚡ XAU SCALPER LIVE</h2>


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


    return html+"</table></body></html>"
