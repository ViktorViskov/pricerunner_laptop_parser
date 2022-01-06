#
# Class for build new index page
#

# libs
import json
import multiprocessing
import time
import psutil
import core.lib_bs4 as lib_bs4
from core.lib_request import Browser
import core.mysql as mysql
from hashlib import md5
from core.models import Laptop

# main class page


class Page:

    # constructor
    def __init__(self, link: str):

        # link
        self.link = link

        # init mysql connection
        # self.mysql = mysql.Mysql_Connect("db", "root", "dbnmjr031193", "pricerunner")

        # variable for define pages (1000 per 1 page)
        json_page = 0

        # items array for processing
        self.items = []

        # Selecting all items
        while True:

            # process link
            self.Url_Processing(link, json_page * 1000)

            # load page and decoding json
            self.json_data = json.loads(Browser(self.link).data)

            # check for page is available
            if int(self.json_data['totalHits']) - json_page * 1000 < 0:
                break

            # Pring page number
            print("Page nr. %d" % (json_page + 1))

            # add items to array
            self.items += self.json_data['products']

            # next page
            json_page += 1

        # create items
        self.Search_All_Items()

    # function for string processing (create link to request and get json)
    def Url_Processing(self, link, offset=0):

        # get attributes from current link
        old_link_attributs = link.split("?")[1].split("&")
        # new link base
        new_link = "https://www.pricerunner.dk/public/search/category/products/v2/dk/27?size=1000&offset=%d" % offset

        # variables for prices
        price_min = 0
        price_max = 0

        # add attributs to link
        for attribut in old_link_attributs:

            if "attr_" in attribut:
                value = attribut[5:].split("#")[0]
                new_link += "&af_%s" % value

            # laptop producent
            elif "man_id=" in attribut:
                value = attribut.split("=")[1]
                new_link += "&af_BRAND=%s" % value

            # screen size
            elif "s_" in attribut:
                value = attribut[2:]
                new_link += "&af_%s" % value
            # min price
            elif "price_min=" in attribut:
                price_min = attribut.split("=")[1]

            # max price
            elif "price_max=" in attribut:
                price_max = attribut.split("=")[1]

        # add prices
        if price_max != 0:
            new_link += "&af_PRICE=%s_%s" % (price_min, price_max)

        # set new link
        self.link = new_link

    # update data in db
    def Send_To_Db(self, data_dict):

        # write all records to db
        for key in data_dict:
            print(key)

    # search all items and create new list
    def Search_All_Items(self):
        # create multiprocessing manages
        manager = multiprocessing.Manager()

        # threads
        threads = []
        max_threads = 1

        # multiprocess data variables
        data_buffer = manager.list()

        # element number for log
        item_number = 1

        # loop for iterate laptops from list
        for item in self.items:

            # create and start task
            task = multiprocessing.Process(target=self.Make_Json_List_Item, args=(
                item, 
                data_buffer))
            task.start()

            # add task to quene
            threads.append(task)

            # increment number of task
            item_number += 1

            # status message
            if (item_number % 100 == 0):
                print("Loading... %d from %d. Amount of threads is %d. Max threads is %d" % (
                    item_number, len(self.items), len(threads), max_threads))

            # check all tasks and delete if is ready
            while len(threads) >= max_threads or len(threads) >= 490:

                # delete task from quene
                for task in threads:
                    if (task.is_alive() == False):
                        threads.remove(task)

                # getting info about cpu usage and wait
                cpu_usage = psutil.cpu_percent(2)

                # check for ram and cpu usage
                if psutil.virtual_memory()[2] < 65 and cpu_usage < 90 and max_threads < 490:
                    max_threads += 10

                elif max_threads > 10 and psutil.virtual_memory()[2] > 85 or max_threads > 10 and cpu_usage > 99:
                    max_threads -= 10

        # wait for threads
        # counter for await 10 minuts for all request
        await_counter = 60
        while len(threads) > 0 or await_counter > 0:

            # delete task from quene
            for task in threads:
                if await_counter <= 0:
                    task.kill()
                    threads.remove(task)

                elif task.is_alive() == False:
                    threads.remove(task)

                if len(threads) == 0:
                    await_counter = 0

            # wait
            time.sleep(10)

            # print status message
            print("%d0 seconds to terminate %d tasks from quene" %
                  (await_counter, len(threads)))

            # minus counter for awaiting tasks
            await_counter -= 1

        # send data to db
        self.Send_To_Db(data_buffer)
        # print(data_buffer)

    # make JSON list item
    def Make_Json_List_Item(self, item, data_buffer:list):

        # getting info
        item_desc = item['description']
        item_link = "https://www.pricerunner.dk" + item['url']
        item_price = item['lowestPrice']['amount']
        item_image = "https://www.pricerunner.dk" + item['image']['path']

        # get old price
        try:
            item_price_old = item['priceDrop']['oldPrice']['amount']
        except:
            item_price_old = item_price

        # open link and parse data
        item_link_root = lib_bs4.Selector_Serch(Browser(item_link).data)

        # get json data
        try:

            #
            # If parsing error, LOOK HERE FIRST
            #

            product_json = json.loads(self.Get_Content(item_link_root.Search_By_Id("initial_payload")))[
                '__INITIAL_PROPS__']['__DEHYDRATED_QUERY_STATE__']['queries'][5]['state']['data']

            #
            # If parsing error, LOOK HERE FIRST
            #
        except:
            product_json = ""
            print("Parsing error!!!")

        # get if present json
        if product_json != "":

            # dict for description
            product_specification = {}

            # read product description
            # loop in sections
            for section in product_json['specification']['sections']:
                # loop in attributes
                for atribut in section['attributes']:
                    # set data in dict
                    product_specification[atribut['name']] = atribut['values'][0]['name']

            # # uncomment to show description
            # for key in product_specification:
            #     print("%s -> %s" % (key, product_specification[key]))

            # info about item
            item_title = self.Get_Dict_Value('Produktnavn', product_specification).strip().upper()

            # CPU
            item_cpu = "%s %s" % (self.Get_Dict_Value('Processor-serie', product_specification), self.Get_Dict_Value('Processor-model', product_specification))
            
            # Battery
            item_battery_time = float(self.Get_Dict_Value('Batteritid', product_specification).split(" ")[0]) if self.Get_Dict_Value('Batteritid', product_specification) != '' else 0

            # Resolution
            item_resolution = self.Get_Dict_Value('Skærmopløsning', product_specification)

            # create hash string
            data_to_hash = "%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
                item_title,
                item_desc,
                item_link,
                item_price,
                item_price_old,
                item_image,
                item_cpu,
                item_battery_time,
                item_resolution)
            data_stamp = md5(data_to_hash.encode("utf-8")).hexdigest()

            # add data to threads buffer
            data_buffer.append(Laptop(
                data_stamp=data_stamp,
                title=item_title,
                description=item_desc,
                link=item_link,
                discout_price=item_price,
                price=item_price_old,
                image_link=item_image,
                cpu=item_cpu,
                battery=item_battery_time,
                resolution=item_resolution))

    # get text content
    def Get_Content(self, item):
        # desc
        try:
            return item.contents[0]
        except:
            return ""

    # Load geekbench points
    def Get_Geekbench_Points(self, cpu_buffer_single, cpu_buffer_multy, cpu_model: str, geekbench_status, pages=1):

        # preprocess cpu model
        cpu_model = cpu_model.strip().upper()

        try:
            while True:
                # check for result. If 0 await for other process some parse info
                single, multi = cpu_buffer_single[cpu_model], cpu_buffer_multy[cpu_model]

                # check result is awailable
                if single == "" or multi == "":
                    time.sleep(1)
                    # print("Await for %s data" % cpu_model)

                # return result
                else:
                    return single, multi

        except:

            # add to library for starting search
            cpu_buffer_single[cpu_model] = ""
            cpu_buffer_multy[cpu_model] = ""

            # check for process status
            while True:
                # check status
                if len(geekbench_status) < 2:
                    break

                else:
                    time.sleep(3)

            # change status
            geekbench_status[cpu_model] = True

            # varible for results
            single = 0
            multi = 0
            trying = 5

            # loop for trying 3 times
            while trying > 0:

                # main loop
                for page in range(pages):

                    # link root
                    root = lib_bs4.Selector_Serch(Browser(
                        "https://browser.geekbench.com/v5/cpu/search?page=%d&q=%s" % (page + 1, cpu_model)).data)

                    # search list items
                    list_items = root.Search_Tags("div", "col-12 list-col")

                    # loop for processing data
                    for item in list_items:

                        # item root
                        item_root = lib_bs4.Selector_Serch(item, True)

                        # add to result
                        search_result = item_root.Search_Tags(
                            "span", "list-col-text-score")

                        # logick
                        if int(self.Get_Content(search_result[0])) > single:
                            single = int(self.Get_Content(search_result[0]))

                        if int(self.Get_Content(search_result[1])) > multi:
                            multi = int(self.Get_Content(search_result[1]))

                    # add to main
                    single = 0 if len(list_items) < 0 else single
                    multi = 0 if len(list_items) < 0 else multi

                    # stop if is result
                    if single != 0 or multi != 0 or trying == 0:
                        trying = 0

                    # minus one time
                    else:
                        trying -= 1

            # add to library
            cpu_buffer_single[cpu_model] = single
            cpu_buffer_multy[cpu_model] = multi

            # change status
            geekbench_status.pop(cpu_model)

            # return result
            return cpu_buffer_single[cpu_model], cpu_buffer_multy[cpu_model]

    # Getting value from dict
    def Get_Dict_Value(self, key, checked_dict):

        # result (CPU model)
        result = ""

        # check for key
        if key in checked_dict:
            result = checked_dict[key]

        # result
        return result
