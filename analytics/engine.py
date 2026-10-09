import re
from collections import Counter, defaultdict
import math

POSITIVE = {
    "amazing": 2.0, "excellent": 2.0, "great": 1.5, "good": 1.0, "friendly": 1.0,
    "fresh": 1.2, "beautiful": 1.0, "quick": 1.0, "fast": 1.0, "clean": 1.0,
    "love": 1.5, "loved": 1.5, "helpful": 1.0, "perfect": 2.0, "best": 2.0
}
NEGATIVE = {
    "bad": -1.5, "slow": -1.5, "long": -1.2, "disappointing": -2.0, "cold": -1.2,
    "frustrating": -1.5, "poor": -1.5, "dirty": -1.5, "rude": -1.5, "terrible": -2.0,
    "waiting": -1.0, "wait": -1.0, "improvement": -0.5
}

def sentiment(text):
    words = re.findall(r"[a-z']+", (text or "").lower())
    score = sum(POSITIVE.get(w,0) + NEGATIVE.get(w,0) for w in words)
    normalized = max(-1,min(1,score/5))
    if normalized > 0.15: label="Positive"
    elif normalized < -0.15: label="Negative"
    else: label="Neutral"
    return label, round(normalized,3)

def _get(r, name):
    return getattr(r,name) if hasattr(r,name) else r.get(name,0)

def analyze_reviews(reviews):
    n=len(reviews)
    if n==0:
        return {
            "total_reviews":0,"average_rating":0,"satisfaction_score":0,
            "dimensions":{"food":0,"service":0,"ambience":0,"cleanliness":0,"speed":0},
            "sentiment":{"Positive":0,"Negative":0,"Neutral":0},
            "sentiment_percent":{"Positive":0,"Negative":0,"Neutral":0},
            "monthly":[],"branches":[],"correlations":{}
        }
    dims = {}
    for key in ["food_rating","service_rating","ambience_rating","cleanliness_rating","speed_rating"]:
        dims[key.replace("_rating","")] = round(sum(float(_get(r,key)) for r in reviews)/n,2)
    avg = round(sum(float(_get(r,"overall_rating")) for r in reviews)/n,2)
    sat = round(avg/5*100,1)
    sent = Counter()
    for r in reviews:
        label = _get(r,"sentiment") or sentiment(_get(r,"comment"))[0]
        sent[label]+=1
    for x in ["Positive","Negative","Neutral"]: sent.setdefault(x,0)

    monthly=defaultdict(list)
    for r in reviews:
        dt=_get(r,"created_at")
        key=dt.strftime("%b %Y") if dt else "Unknown"
        monthly[key].append(float(_get(r,"overall_rating")))
    monthly_out=[{"month":k,"rating":round(sum(v)/len(v),2)} for k,v in sorted(monthly.items())][-12:]

    branches=defaultdict(list)
    for r in reviews:
        branches[_get(r,"restaurant_id")].append(float(_get(r,"overall_rating")))
    branch_out=[{"restaurant_id":k,"rating":round(sum(v)/len(v),2),"reviews":len(v)} for k,v in branches.items()]
    branch_out.sort(key=lambda x:x["rating"], reverse=True)

    # Pearson-like correlations with overall rating
    correlations={}
    overall=[float(_get(r,"overall_rating")) for r in reviews]
    for key in ["food_rating","service_rating","ambience_rating","cleanliness_rating","speed_rating"]:
        x=[float(_get(r,key)) for r in reviews]
        correlations[key.replace("_rating","")] = round(pearson(x,overall),3)

    single = sentiment(_get(reviews[0],"comment")) if n else ("Neutral",0)
    return {
        "total_reviews":n, "average_rating":avg, "satisfaction_score":sat,
        "dimensions":dims, "sentiment":dict(sent),
        "sentiment_percent":{k:round(v/n*100,1) for k,v in sent.items()},
        "monthly":monthly_out, "branches":branch_out, "correlations":correlations,
        "single_sentiment":single
    }

def pearson(x,y):
    if len(x)<2:return 0
    mx=sum(x)/len(x); my=sum(y)/len(y)
    num=sum((a-mx)*(b-my) for a,b in zip(x,y))
    den=math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
    return num/den if den else 0

def build_recommendations(stats):
    d=stats["dimensions"]
    rec=[]
    if d.get("service",5)<3.5: rec.append("Service rating is below 3.5. Conduct staff training and monitor service response time.")
    if d.get("speed",5)<3.5: rec.append("Speed is a weak area. Review queue management, staffing and peak-hour workflow.")
    if d.get("cleanliness",5)<3.7: rec.append("Cleanliness needs attention. Increase inspection frequency and assign shift-level accountability.")
    if d.get("food",5)>=4.2: rec.append("Food quality is a strength. Protect recipe consistency and highlight popular dishes.")
    if stats["sentiment_percent"].get("Negative",0)>25: rec.append("Negative feedback exceeds 25%. Launch a complaint-resolution and root-cause review.")
    if not rec: rec.append("Overall performance is healthy. Continue monitoring weekly KPIs and customer sentiment.")
    return rec
