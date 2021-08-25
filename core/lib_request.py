# 
# class for load page
# 

# libs
import dryscrape, time, webkit_server, requests

# async class for load data
class Browser:
    
    # constructor
    def __init__(self, url, fast = False, pause = 0, images = False) -> None:

        # data init

        # pause
        self.pause = pause

        # load page

        # fast load
        if fast:
            self.data = self.Fast_Load(url)
        
        # init web session and load (slow)
        else:
            # load images
            self.load_images = images
    
            # init
            self.Init()

            # load attributes
            self.Add_Attribures()

            # load page
            self.data = self.Load(url)

            # reset session
            self.Reset()

    # load page
    def Load(self, url):
        # load link
        self.session.visit(url)

        # check for pause
        if self.pause > 0:
            self.Pause(self.pause)

        # add data to variable
        return self.session.body()
    
    # fast load using requests
    def Fast_Load(self, url):
        return requests.request("GET", url).content.decode()
    
    # Pause
    def Pause(self,seconds):
        # start waiting
        current_time = 0
        print("Waiting ...")
        while current_time != seconds:
            current_time += 1
            print("%ds. from %ds." % (current_time, seconds))
            time.sleep(1)
    # attributes
    def Add_Attribures(self):
        # load images attribut
        if not self.load_images:
            self.session.driver.set_attribute('auto_load_images', False)        

    # init 
    def Init(self):
        self.server = webkit_server.Server()
        server_conn = webkit_server.ServerConnection(server=self.server)
        driver = dryscrape.driver.webkit.Driver(connection=server_conn)
        self.session = dryscrape.Session(driver=driver)

    # exit
    def Reset(self):
        self.session.reset()
        self.server.kill()
        