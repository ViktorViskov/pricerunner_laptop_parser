# 
# class for load page
# 

# libs
import dryscrape, time

class Page_Request:
    # variables

    # constructor
    def __init__(self, url, seconds = 0, images = False) -> None:
        # set url
        self.url = url

        # set pause
        self.max_time = seconds

        # load images
        self.load_images = images

        # load data
        self.Load()

    # load page
    def Load(self):
        # init session
        # dryscrape.start_xvfb()
        self.session = dryscrape.Session()

        # load images attribut
        if not self.load_images:
            self.session.driver.set_attribute('auto_load_images', False)

        # load link
        self.session.visit(self.url)

        # check for pause
        if self.max_time > 0:
            self.Pause()

        # add data to variable
        self.data = self.session.body()
    
    # Pause
    def Pause(self):
        # start waiting
        current_time = 0
        print("Waiting ...")
        while current_time != self.max_time:
            current_time += 1
            print("%ds. from %ds." % (current_time, self.max_time))
            time.sleep(1)

    # exit
    def Reset(self):
        self.session.driver.reset()