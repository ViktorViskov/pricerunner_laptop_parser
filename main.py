#!/usr/bin/python3
import core.page

# filter one only laptops from tilbud list
# core.page.Page("index.html", "https://www.pricerunner.dk/deals?attr_category=27&price_min=1&price_max=7500&man_id=7227,11563,571&sorting=pricedrop_asc", "div", "_2Vdwcz_zWR _1bgVr-M90D")
# core.page.Page("https://www.pricerunner.dk/public/search/deals/products/v2/dk?size=1000&af_PRICE_DROP=-90_-10&categoryIds=27",True, False)

# all laptops with ryzen 7
# core.page.Page("ryzen7.html", "https://www.pricerunner.dk/cl/27/Baerbar?attr_60535860=60535878", "div", "_2Vdwcz_zWR _1bgVr-M90D",True)

# filter 13-14.5 screen 16 20 32GB RAM 1000-9000DKK LENOVO HP DELL 
# core.page.Page("https://www.pricerunner.dk/cl/27/Baerbar?man_id=7227,11563,571&attr_60382316=60382329,60382332,60382330#price_min=1000&price_max=9000&s_54120131=13_14.5")
link = "https://www.pricerunner.dk/cl/27/Baerbar?price_min=1000&price_max=9000&s_54120131=13_15.7"
core.page.Page(link)

# filter 13-14.5 screen 16 20 32GB RAM 1000-9000DKK LENOVO HP DELL RYZEN 7
# core.page.Page("https://www.pricerunner.dk/cl/27/Baerbar?man_id=7227,11563,571&attr_60382316=60382329,60382332,60382330&attr_60535860=60535878#price_min=1000&price_max=9000&s_54120131=13_14.5")