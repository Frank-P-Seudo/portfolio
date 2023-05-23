from .models import Bid, Watchlist

def sortBids(listings):
  # a function for sorting bids by the amount of bid, in descending order
  def Fn(dict):
      return -int(dict.bid)
  
  # for each listing, sort the bids; if the listing has no bid, give it a price of zero
  for listing in listings:
      bids = Bid.objects.filter(listing=listing)
      if bids:
          print(bids)
          bids = sorted(bids, key=Fn)
          print(bids)
          listing.price = int(bids[0].bid)
      else:
          listing.price = 0
  
  return listings 

# count the number of items in watchlist
def countWatchlist(request):
    watchedNum = 0
    if request.user.is_authenticated:
        watchlist = Watchlist.objects.filter(bidder=request.user)
        if watchlist:
            watchedNum = len(watchlist)
    return watchedNum