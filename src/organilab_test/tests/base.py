import glob
import shutil
from importlib import import_module
from pathlib import Path
from time import sleep

from PIL import Image
from Screenshot import Screenshot
from django.conf import settings
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils.timezone import now
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from dateutil.relativedelta import relativedelta


class SeleniumBase(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(SeleniumBase, cls).setUpClass()

        cls.timeout = 30

        cls.ob = Screenshot.Screenshot()
        cls.options = webdriver.FirefoxOptions()

        cls.selenium = webdriver.Chrome()
        cls.selenium.set_window_size(1280, 720)

        cls.tmp = Path(settings.BASE_DIR) / 'tmp'
        cls.folder = '%s/%dx%d' % (cls.tmp, 120, 200)
        cls.dir = Path(settings.BASE_DIR) / cls.folder
        cls.static_save_path = Path(settings.DOCS_SOURCE_DIR) / '_static'
        cls.save_path_gif = cls.static_save_path / 'gif'

        if not cls.tmp.exists():
            cls.tmp.mkdir()

        cls.cursor_script = '''
            var cursor = document.createElement('i');
            cursor.style.position = 'absolute';
            cursor.style.zIndex = '9999';
            cursor.classList.add("fa", "fa-mouse-pointer", "text-danger", "fa-1x", "cursor_pointer");
            document.body.appendChild(cursor);
        '''

        cls.hide_cursor_script = '''
        var cursor = document.querySelector(".cursor_pointer");
        cursor.style.zIndex = '-1';
        '''

        cls.show_cursor_script = '''
            if(!$('.cursor_pointer').length > 0){
            '''
        cls.show_cursor_script += cls.cursor_script
        cls.show_cursor_script += '''
            }
            var cursor = document.querySelector(".cursor_pointer");
            cursor.style.zIndex = '9999';
            '''

        cls.action = ActionChains(cls.selenium)

    def change_focus_tab(self, window_name):
        self.selenium.switch_to.window(window_name)

    def get_format_increase_decrease_date(self, date, days, increase=True, format="%m/%d/%Y"):
        new_date = date + relativedelta(days=days)
        if not increase:
            new_date = date - relativedelta(days=days)
        return new_date, new_date.strftime(format)

    def move_cursor_script(self, x, y):
        """
        Move the div that simulate a cursor
        """
        return '''
        var cursor = document.querySelector('.cursor_pointer');
                cursor.style.left= '{}px';
                cursor.style.top= '{}px';
                '''.format(x, y)


    def get_element_js_by_xpath(self, path):
        return """
            function getElementByXpath(path) {
              return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            }
            var element = getElementByXpath("%s");
            """ % path

    def move_cursor(self, x, y):
        xy_position = self.move_cursor_script(x, y)
        self.selenium.execute_script(xy_position)

    def hide_show_cursor(self, cursor, show_cursor=True, x=0, y=0):
        if cursor:
            z_index_cursor = self.hide_cursor_script

            if show_cursor:
                z_index_cursor = self.show_cursor_script
            self.selenium.execute_script(z_index_cursor)

            if show_cursor:
                self.move_cursor(x, y)

    def hover_effect(self, element):
        self.action.move_to_element(element).perform()

    def create_directory_path(self, url=None, folder_name=""):
        """
        Folder name is a specific name by action, for example 'create_org',
        'view_org_users', etc
        """

        if url:
            self.selenium.get(url)

        self.folder = '%s/%dx%d' % (
                self.tmp, 120, 100)
        self.dir = Path(settings.BASE_DIR) / self.folder

        path_with_folder_name = self.dir / folder_name

        if not self.dir.exists():
            self.dir.mkdir()

        if not path_with_folder_name.exists():
            path_with_folder_name.mkdir()

        self.dir = path_with_folder_name

    def create_screenshot(self, order=1, time_out=3, name="", save_screenshot=False):
        extension_name = '%s.png' % name
        order_name = '%r.png' % order
        sleep(time_out)
        self.selenium.save_screenshot(
                str(Path(self.dir / order_name).absolute().resolve()))

        if save_screenshot:
            self.selenium.save_screenshot(
                str(Path(self.static_save_path / extension_name).absolute().resolve()))

        order += 1
        return order

    def get_gif_images(self, file_url):
        gif_images = []
        folder_images = glob.glob('{}/*.png'.format(file_url))
        tuple_images = [(int(image.split('/').pop().split('.')[0]), image) for image in
                        folder_images]
        sorted_images_list = [x[1] for x in sorted(tuple_images)]

        for filename in sorted_images_list:  # loop through all png files in the folder
            im = Image.open(filename)  # open the image
            gif_images.append(im)  # add the image to the list

        return gif_images

    def create_gif(self, file_url, folder):
        gif_images = self.get_gif_images(file_url)

        # save as a gif
        gif_name = '/%s%s' % (folder, '.gif')
        gif_images[0].save(str(self.save_path_gif) + gif_name,
                           save_all=True, append_images=gif_images[1:], optimize=False,
                           duration=500, loop=0)

    def get_x_y_element(self, element):
        return (element.location['x'] + element.size['width'] / 4,
                element.location['y'] + element.size['height'] / 4)

    def activate_move_cursor(self, element, cursor, hover):
        self.selenium.execute_script(self.cursor_script)

        if cursor:
            x, y = self.get_x_y_element(element)
            self.move_cursor(x, y)

        if hover:
            self.hover_effect(element)

    def take_screenshot_by_obj(self, obj, order):
        """
        This function takes a screenshot to build a gif and save screenshot if it is
        necessary.
        """
        if 'screenshot_name' in obj and obj['screenshot_name']:
            order = self.create_screenshot(order=order, name=obj['screenshot_name'], save_screenshot=True)
        else:
            order = self.create_screenshot(order=order)

        return order

    def set_value_action(self, obj, element):
        """
        This is an action responsible to set value in an element.
        Value can be quotation marks this is equal to clear an input.
        """
        if "value" in obj:
            element.send_keys(obj['value'])

    def move_cursor_end(self, obj):
        """
        It moves cursor to the end input value length.
        reduce_length variable is for special cases like email mask input where it is
        necessary reduce input value length.
        """
        reduce_length = 0

        if "reduce_length" in obj and obj["reduce_length"]:
            reduce_length = obj["reduce_length"]

        move_cursor_end = self.get_element_js_by_xpath(obj["path"])+"""
            const end = element.value.length - %d;
            element.setSelectionRange(end, end);
            element.focus();
        """ % (reduce_length)
        self.selenium.execute_script(move_cursor_end)

    def set_css_element(self, target):
        return """
            $(".component-btn-group").first().css("display", "block");
            """

    def active_hidden_elements(self, obj):
        """
        Display hidden elements, for example in dropdowns or elements that are hidden.
        """
        move_cursor =self.get_element_js_by_xpath(obj["active_hidden_elements"])+"""
        element.click();
        """
        sleep(15)
        self.selenium.execute_script(move_cursor)

    def extra_action(self, obj, element):
        """
        This function will list all required actions in selenium tests.
        """
        if obj["extra_action"] == "setvalue":
            self.set_value_action(obj, element)
        elif obj["extra_action"] == "script":
            self.selenium.execute_script(obj['value'])
        elif obj["extra_action"] == "sweetalert_comfirm":
            self.do_sweetaler_comfirm_action(obj, element)
        elif obj["extra_action"] == "clearinput":
            element.clear()
        elif obj["extra_action"] == "move_cursor_end":
            self.move_cursor_end(obj)
        elif obj["extra_action"] == "hover":
            self.selenium.execute_script(self.set_css_element(".component-btn-group"))
        elif obj['extra_action'] == "drag_and_drop":
            self.action.drag_and_drop(self.selenium.find_element(By.XPATH,obj["x"]),
                                      self.selenium.find_element(By.XPATH,obj["y"])).perform()

    def do_sweetaler_comfirm_action(self, obj, element):
        """
        This is an action responsible to press yes/no buttons of sweetalert.
        """
        self.action.move_to_element(element).perform()
        element.click()
        sleep(1)
        self.selenium.execute_script(obj['comfirm'])
        sleep(1)
        self.selenium.execute_script(obj['comfirm'])



    def do_action(self, obj, element):
        """
        This function applies the respective action by obj path.
        """
        if 'extra_action' in obj:
            self.extra_action(obj, element)
        else:
            self.action.move_to_element(element).perform()
            element.click()

    def apply_utils(self,obj):

        if 'scroll' in obj:
            self.selenium.execute_script(obj['scroll'])

        if 'modalscroll' in obj:
            self.selenium.execute_script(obj['scroll'])

        if "active_hidden_elements" in obj:
            self.active_hidden_elements(obj)

        if "hover" in obj:
            self.selenium.execute_script(self.set_css_element(obj['element']))

        if 'sleep' in obj:
            if isinstance(obj['sleep'], int):
                sleep(obj["sleep"])
            else:
                sleep(15)

    def take_screenshot_list(self, path_list, folder_name, cursor=True, hover=True, order=1):
        """
        This function does following steps:
            1. First, it will take the initial screenshot before any movement or action.
            2. After that, it runs the path loop related to current test.
            3. The current element is found and defined in element variable.
            4. The cursor element is created, and it starts to move on the path element.
            5. The specific action is applied(click by default or any other action like set value in the element).
            6. Cursor will be hidden before of action and show after it.
            7. In every path takes 3 screenshots after any movement or action.(A more complete gif(less skips between screenshots))
            8. In the second screenshot(inside the path loop) it will save the screenshot if it is necessary.(screenshot_name parameter in object path)
            9. Finally, the git result will be created in docs/source/_static/gif/folder_name.gif
        """
        self.create_directory_path(folder_name=folder_name)
        self.create_screenshot(order=order)
        print(folder_name)
        for obj in path_list:
            self.apply_utils(obj)
            element = self.selenium.find_element(By.XPATH, obj['path'])
            order = self.create_screenshot(order=order)
            x, y = self.get_x_y_element(element)
            self.activate_move_cursor(element, cursor, hover)
            order = self.take_screenshot_by_obj(obj, order)
            self.hide_show_cursor(cursor, show_cursor=False)
            self.do_action(obj, element)
            self.hide_show_cursor(cursor, x=x, y=y)
            order = self.create_screenshot(order=order)
        return order

    def create_gif_process(self, path_list, folder_name, cursor=True, hover=True, order=1):
        self.take_screenshot_list(path_list, folder_name, cursor, hover, order)
        self.create_gif(self.dir, folder_name)

    def create_gif_by_change_focus_tab(self, general_path_list, tab_name_list, folder_name):
        order = 0
        screenshot_order = 1

        for path_list in general_path_list:
            screenshot_order = self.take_screenshot_list(path_list, folder_name, order=screenshot_order)

            if len(tab_name_list) > 0 and order + 1 <= len(tab_name_list):
                self.change_focus_tab(tab_name_list[order])
                order += 1

        self.create_gif(self.dir, folder_name)

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
