import shutil
from importlib import import_module
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from PIL import Image
import glob
from selenium import webdriver
from pathlib import Path
from Screenshot import Screenshot
from django.conf import settings
from time import sleep
from django.contrib.staticfiles.testing import StaticLiveServerTestCase


class SeleniumBase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(SeleniumBase, cls).setUpClass()

        cls.timeout = 30

        cls.ob = Screenshot.Screenshot()
        cls.options = webdriver.FirefoxOptions()

        cls.selenium = webdriver.Chrome()
        cls.selenium.maximize_window()

        cls.tmp = Path(settings.BASE_DIR) / 'tmp'
        cls.folder = '%s/%dx%d' % (cls.tmp, 120, 200)
        cls.dir = Path(settings.BASE_DIR) / cls.folder
        cls.static_save_path = Path(settings.DOCS_SOURCE_DIR) / '_static'
        cls.save_path_gif = cls.static_save_path / 'gif'

        if not cls.tmp.exists():
            cls.tmp.mkdir()


    def create_directory_path(self, time_out=10, url=None, folder_name=""):
        # Folder name is an specific name by action, for example 'create_org', 'view_org_users', etc

        if url:
            self.selenium.get(url)

        self.folder = '%s/%dx%d' % (
                self.tmp, 120, 100)
        self.dir = Path(settings.BASE_DIR) / self.folder

        if not self.dir.exists():
            self.dir.mkdir()

            self.dir = self.dir / folder_name

            if not self.dir.exists():
                self.dir.mkdir()



    def screenShots(self, name, time_out, save_screenshot=False):
        x_Full_Page = '%s.png' % name
        sleep(time_out)
        self.selenium.save_screenshot(
                str(Path(self.dir / x_Full_Page).absolute().resolve()))

        if save_screenshot:
            self.selenium.save_screenshot(
                str(Path(self.static_save_path / x_Full_Page).absolute().resolve()))

    def create_gifs(self, file_url, folder):
        images = []
        import time
        # get the current time to use in the filename
        timestr = time.strftime("%Y%m%d-%H%M%S")

        # get all the images in the 'images for gif' folder
        for filename in sorted(glob.glob(
            '{}/*.png'.format(file_url))):  # loop through all png files in the folder
            im = Image.open(filename)  # open the image
            im_small = im.resize((1440, 700),
                                 resample=0)  # resize them to make them a bit smaller
            images.append(im_small)  # add the image to the list

        # calculate the frame number of the last frame (ie the number of images)
        last_frame = (len(images))

        # create 10 extra copies of the last frame (to make the gif spend longer on the most recent data)
        for x in range(0, 9):
            im = images[last_frame - 1]
            images.append(im)

        # save as a gif
        gif_name = '/%s%s' %(folder, '.gif')
        images[0].save(str(self.save_path_gif) + gif_name,
                       save_all=True, append_images=images[1:], optimize=False,
                       duration=1500, loop=0)

    def force_login(self, user, driver, base_url):
        from django.conf import settings
        SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
        driver.get(base_url)

        session = SessionStore()
        session[SESSION_KEY] = user._meta.pk.value_to_string(user)
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()

        cookie = {
            'name': settings.SESSION_COOKIE_NAME,
            'value': session.session_key,
            'path': '/'
        }
        driver.add_cookie(cookie)
        driver.refresh()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()

        #Removing tmp directory
        try:
            shutil.rmtree(cls.tmp)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))

        super(SeleniumBase, cls).tearDownClass()
