#
# Class for build new index page
#

# libs
import json
import multiprocessing
from operator import le
import time
from datetime import datetime
import psutil
import core.lib_bs4 as lib_bs4
from core.lib_request import Browser
import core.mysql as mysql
from hashlib import md5
from core.models import CPU, Laptop
import keys as k

# main class page


class Bot:

    # constructor
    def __init__(self):


        # init mysql connection
        self.mysql = mysql.Mysql_Connect(k.db_host, k.db_user, k.db_password, k.db_name)

        # link
        self.link = self.Link_From_Db()

        # variable for define pages (1000 per 1 page)
        json_page = 0

        # items array for processing
        self.items = []

        # check for existing link
        if self.link != "":

            # Selecting all items
            while True:

                try:
                    # process link
                    link_to_download = self.Url_Processing(self.link, json_page * 1000)

                    # load page and decoding json
                    self.json_data = json.loads(Browser(link_to_download).data)

                    # check for page is available
                    if int(self.json_data['totalHits']) - json_page * 1000 < 0:
                        break

                    # add items to array
                    self.items += self.json_data['products']

                    # next page
                    json_page += 1
                
                except:
                    self.json_data = None
                    print("Loading error! Check loading link or net connection")
                    

            # create items
            if self.json_data != None:
                self.Process_All_Items()

        # print error becouse link in db is not active or db dont have configs
        else:
            print("Check for active link in db configs table")

        # show last execution script datetime
        print("Last execution time > %s" % (datetime.now()))

    # function for string processing (create link to request and get json)
    def Url_Processing(self, link, offset=0):

        # preprocess for link with out parameters
        if "?" not in link:
            link += "?"

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
        return new_link

    # search all items and create new list
    def Process_All_Items(self):
        # variables

        # Loaded laptop list
        self.loaded_laptops = self.List_Processing(self.items)

        # check for emergency stop
        if len(self.loaded_laptops) < len(self.items) - int(len(self.items) * 0.01):
            print("Emergency stop. Check Parse_Laptop_From_Json. loaded > %d items > %d" %(len(self.loaded_laptops), len(self.items)))
            return 1
        # check for emergency stop
        
        
        # Register cpues in db
        self.Register_Cpu_List(self.loaded_laptops)

        # Register Laptops in db
        self.Register_Laptop_List(self.loaded_laptops)

    # make JSON list item
    def List_Processing(self, laptops_obj):

        # create multiprocessing manages
        manager = multiprocessing.Manager()

        # threads
        threads = []
        max_threads = 1

        # special list for multiprocessing
        laptops_list = manager.list()

        for number in range(len(laptops_obj)):

            # create and start task
            task = multiprocessing.Process(target=self.Parse_Laptop_From_Json, args=(laptops_obj[number], laptops_list))
            task.start()

            # add task to quene
            threads.append(task)

            # time to kill all tasks if its freeze
            expire_time = 60

            # loop for controlling tasks amount
            while len(threads) > max_threads or number == len(laptops_obj) - 1 and len(threads) != 0:

                # delete task from quene
                for task in threads:
                    if task.is_alive() == False:
                        threads.remove(task)

                    # kill and remove task if time is expired
                    if expire_time < 1:
                        task.kill()
                        threads.remove(task)

                # if is not last task update allowed threads number
                if number != len(laptops_obj) - 1:
                    max_threads = self.Check_Cpu_Ram_Load(max_threads)

                # timer to delete frezze tasks
                expire_time -= 1

                # make pause
                time.sleep(1)
            
        # return created list with laptops
        return laptops_list

    # Method for parsing laptop from json
    def Parse_Laptop_From_Json(self, laptop_obj:object, multiprocess_buffer:list):
        # getting info
        laptop_desc = laptop_obj['description'] if laptop_obj['description'] != None else ""
        laptop_link = "https://www.pricerunner.dk" + laptop_obj['url']
        laptop_price = laptop_obj['lowestPrice']['amount']
        laptop_image = "https://www.pricerunner.dk" + laptop_obj['image']['path']

        # get old price
        try:
            laptop_price_old = laptop_obj['priceDrop']['oldPrice']['amount']
        except:
            laptop_price_old = laptop_price

        # open link and parse data
        laptop_link_root = lib_bs4.Selector_Serch(Browser(laptop_link).data)

        # get json data
        try:

            #
            # If parsing error, LOOK HERE FIRST
            #

            # Here is serching data to current product
            mixed_data = json.loads(self.Get_Content(laptop_link_root.Search_By_Id("initial_payload")))['__INITIAL_PROPS__']['__DEHYDRATED_QUERY_STATE__']['queries']

            laptop_json = ""

            # loop for search product in data arrays
            for data_querry in mixed_data:
                if 'state' in data_querry:
                    if 'data' in data_querry['state']:
                        if 'specification' in data_querry['state']['data']:
                            laptop_json = data_querry['state']['data']
            
            #
            # If parsing error, LOOK HERE FIRST
            #
        except Exception:

            # data to parse
            # self.Get_Content(laptop_link_root.Search_By_Id("initial_payload"))

            laptop_json = ""
            print("Parsing error!!!") 

        # get if present json
        if laptop_json != "":

            # dict for description
            laptop_specification = {}

            # read laptop description
            # loop in sections
            for section in laptop_json['specification']['sections']:
                # loop in attributes
                for attribute in section['attributes']:
                    # set data in dict
                    laptop_specification[attribute['name']] = attribute['values'][0]['name']

            # # uncomment to show description
            # for key in laptop_specification:
            #     print("%s -> %s" % (key, laptop_specification[key]))

            # info about item
            laptop_title = self.Get_Dict_Value('Produktnavn', laptop_specification).upper()

            # CPU
            laptop_cpu = "%s %s" % (self.Get_Dict_Value('Processor', laptop_specification), self.Get_Dict_Value('Processor-model', laptop_specification))
            laptop_cpu = laptop_cpu.strip().lower()
            
            # Battery
            laptop_battery_time = float(self.Get_Dict_Value('Batteritid', laptop_specification).split(" ")[0]) if self.Get_Dict_Value('Batteritid', laptop_specification) != '' else 0

            # Resolution
            laptop_resolution = self.Get_Dict_Value('Skærmopløsning', laptop_specification)

            # create hash string
            data_to_hash = "%s,%s,%s,%s,%s,%s,%s,%s,%s" % (
                laptop_title,
                laptop_desc,
                laptop_link,
                laptop_price,
                laptop_price_old,
                laptop_image,
                laptop_cpu,
                laptop_battery_time,
                laptop_resolution)
            data_stamp = md5(data_to_hash.encode("utf-8")).hexdigest()

            multiprocess_buffer.append(Laptop(
                data_stamp=data_stamp,
                title=laptop_title,
                description=laptop_desc,
                link=laptop_link,
                discount_price=laptop_price,
                price=laptop_price_old,
                image_link=laptop_image,
                cpu=laptop_cpu,
                battery=laptop_battery_time,
                resolution=laptop_resolution))

        # else:
            # make nothing

    # method for define which is a new cpu's, then parse data about this cpu and send cpu's list to db  
    def Register_Cpu_List(self, loaded_laptops):
        loaded_cpu_names = list(map(lambda laptop: laptop.cpu, loaded_laptops))
        db_cpu_names = list(map(lambda cpu: cpu.title, self.Cpu_From_Db()))

        new_cpu_names = []

        # main loop for iterate items and define new cpu's
        for cpu in loaded_cpu_names:
            if cpu not in db_cpu_names and cpu not in new_cpu_names:
                new_cpu_names.append(cpu)

        # load info about cpu

        # create multiprocessing manages
        manager = multiprocessing.Manager()

        # threads
        threads = []
        max_threads = 4

        # special list for multiprocessing
        cpues_to_db = manager.list()

        for number in range(len(new_cpu_names)):
            # create and start task
            task = multiprocessing.Process(target=self.Get_Geekbench_Points, args=(new_cpu_names[number], cpues_to_db))
            task.start()

            # add task to quene
            threads.append(task)

            # time to kill all tasks if its freeze
            expire_time = 60

            # loop for controlling tasks amount
            while len(threads) > max_threads or number == len(new_cpu_names) - 1 and len(threads) != 0:

                # delete task from quene
                for task in threads:
                    if task.is_alive() == False or expire_time < 1:
                        threads.remove(task)
                
                # pause
                time.sleep(1)
                expire_time -= 1


        # Send cpu's to db
        for cpu_to_db in cpues_to_db:
            self.mysql.I("INSERT INTO cpu_list VALUES ('%s','%s','%s')" % (cpu_to_db.title, cpu_to_db.single, cpu_to_db.multi)) 

    # method for define which is a new cpu's, then parse data about this cpu and send cpu's list to db  
    def Register_Laptop_List(self, loaded_laptops):
        loaded_laptop_names = list(map(lambda laptop: laptop.title, loaded_laptops))

        # load laptops from db
        db_laptops = self.Laptops_From_Db()

        # variable with exist data hash
        db_laptop_names = list(map(lambda laptop: laptop.title, db_laptops))
        db_laptop_hashes = list(map(lambda laptop: laptop.data_stamp, db_laptops))
        laptops_to_db = []
        laptops_to_delete = []

        # Iterate loaded laptops and check data via hash
        # If hash not like in db, overide record with new data

        # search laptops which must added/updated
        for loaded_laptop in loaded_laptops:
            if loaded_laptop.data_stamp not in db_laptop_hashes:
                laptops_to_db.append(loaded_laptop)

                # check for laptop in db. If is it, laptop must be deleted befor update data
                if loaded_laptop.title in db_laptop_names:
                    
                    # adding laptop to delete
                    laptops_to_delete.append(loaded_laptop)
        
        # search laptops which not available
        for db_laptop in db_laptops:
            if db_laptop.title not in loaded_laptop_names:
                laptops_to_delete.append(db_laptop)
        
        # delete all laptops from list
        for laptop_to_delete in laptops_to_delete:
            # error handling
            try:
                self.mysql.I("DELETE FROM laptops WHERE title = '%s'" % (laptop_to_delete.title))
            except:
                print("Delete error!")
                print("DELETE FROM laptops WHERE title = '%s'" % (laptop_to_delete.title))


        # send laptops to db
        for laptop_to_db in laptops_to_db:
            # error handling
            try:
                self.mysql.I("INSERT INTO laptops VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s' )" % (laptop_to_db.data_stamp, laptop_to_db.title, laptop_to_db.description, laptop_to_db.link, laptop_to_db.discount_price, laptop_to_db.price, laptop_to_db.image_link, laptop_to_db.cpu, laptop_to_db.battery, laptop_to_db.resolution))
            except:
                print("Inser error!")
                print("INSERT INTO laptops VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s' )" % (laptop_to_db.data_stamp, laptop_to_db.title, laptop_to_db.description, laptop_to_db.link, laptop_to_db.discount_price, laptop_to_db.price, laptop_to_db.image_link, laptop_to_db.cpu, laptop_to_db.battery, laptop_to_db.resolution))
    

    # get text content
    def Get_Content(self, item):
        # desc
        try:
            return item.contents[0]
        except:
            return ""

    # Load geekbench points
    def Get_Geekbench_Points(self, cpu_model: str, buffer: list):

        # configs
        pages = 2
        trying = 5

        # varible for results
        single = 0
        multi = 0

        try:
                
            # loop for trying n times
            while trying > 0:

                # main loop
                for page in range(pages):

                    # link root
                    root = lib_bs4.Selector_Serch(Browser(
                        "https://browser.geekbench.com/v5/cpu/search?page=%d&q=%s" % (page + 1, cpu_model.replace(" ","+"))).data)

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
        except:
            print("CPU {%s} score parsing error" % (cpu_model))

        # return result
        buffer.append(CPU(title=cpu_model, single=single, multi=multi))


    # Getting value from dict
    def Get_Dict_Value(self, key, checked_dict):

        # result (CPU model)
        result = ""

        # check for key
        if key in checked_dict:
            result = checked_dict[key].replace("'","").replace('"',"").replace('`',"").strip()

        # result
        return result

    # Load CPU infos
    def Get_CPU_Info(self, cpu_list_from_db, cpu_list_from_laptops):
        # variables
        new_cpues = dict()

        for cpu in cpu_list_from_laptops:
            if cpu not in cpu_list_from_db:
                new_cpues[cpu] = [] 
        
    # Method for load CPU's list
    def Cpu_From_Db(self):
        return list(map(lambda from_db: CPU(title=from_db[0],single=from_db[1], multi=from_db[2]), self.mysql.IO("SELECT * FROM cpu_list")))
    
    # Method for load current link from db
    def Link_From_Db(self):
        try:
            return self.mysql.IO("SELECT link FROM configs WHERE is_active = true")[0][0]
        except:
            return ""
            

    # Method for load laptops list
    def Laptops_From_Db(self):
        return list(map(lambda record: Laptop(
            data_stamp=record[0],
            title=record[1],
            description=record[2],
            link=record[3],
            discount_price=record[4],
            price=record[5],
            image_link=record[6],
            cpu=record[7],
            battery=record[8],
            resolution=record[9]),
            self.mysql.IO("select * from laptops;")))

    # method for check cpu and ram usage
    def Check_Cpu_Ram_Load(self, max_threads):
        # configs
        max_open_threads = 200

        # getting info about cpu usage on 2 sec period
        cpu_usage = psutil.cpu_percent(2)
        ram_usage = psutil.virtual_memory()[2]

        # check for ram and cpu usage

        # incrementing
        if ram_usage < 65 and cpu_usage < 90 and max_threads < max_open_threads:
            max_threads += 10

        # decrementing
        elif max_threads > 10 and ram_usage > 85 or max_threads > 10 and cpu_usage > 80:
            max_threads -= 10
        
        return max_threads
