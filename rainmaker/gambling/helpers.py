from django.shortcuts import render
from django.core.paginator import Paginator

from .models import User, Pool, Bet, Following

def sortAndProcess(request, pools, TIME_SLOTS):
    pools = sorted(pools, key=lambda pool: pool.timestamp, reverse=True)
    if pools:
        for pool in pools:
            if pool.hour > 0:
                pool.timeslot = TIME_SLOTS[pool.hour-1][1]
            else:
                pool.timeslot = TIME_SLOTS[23][1]

    if request.user.is_authenticated:
        request.user.watchings = Following.objects.filter(user=request.user).count()
        for pool in pools:
            # a pool may carry a bool to tell if it was created by the user
            if pool.house == request.user:
                pool.createdByUser = True
            else:
                # a pool may also carry a bool to tell if the user already bet on it
                bet_record = Bet.objects.filter(pool=pool, punter=request.user)
                if bet_record:
                    pool.bettedByUser = True
                    pool.wager = bet_record[0].wager

            # a pool may carry a bool to tell if the user is following it
            watchRecord = Following.objects.filter(pool=pool, user=request.user)
            if watchRecord:
                pool.watched = True
    
    return pools

def renderIndex(request, pools, TIME_SLOTS):
    pools = sortAndProcess(request, pools, TIME_SLOTS)
        
    # pagination stuff
    paginator = Paginator(pools, 5)
    page_number = request.GET.get('page')
    if page_number is None:
        page_number = 1
    pools = paginator.get_page(page_number)

    return render(request, "gambling/index.html", {
        "pools": pools,
    })