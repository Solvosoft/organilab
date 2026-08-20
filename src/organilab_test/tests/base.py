import glob
import os
import re
import shutil
import sys
import threading
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
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    MoveTargetOutOfBoundsException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.support.ui import WebDriverWait


class SeleniumBase(StaticLiveServerTestCase):
    # Retardo entre capturas. Sólo aplica al generar el GIF: le da al navegador
    # tiempo de pintar la transición para que la animación no salte.
    screenshot_delay = 3

    # Las esperas fijas de los path_list existen sobre todo para que el GIF
    # tenga fluidez. Cuando no se generan capturas basta con esperar a que el
    # elemento esté presente, y de eso se encarga find_element_waiting(), así
    # que se escalan a una fracción en vez de dormir el tiempo completo.
    # Ajustable con SELENIUM_SLEEP_FACTOR (1 = comportamiento original).
    sleep_factor = None
    element_timeout = 10

    # Segunda espera, corta y best-effort: si el elemento nunca llega a ser
    # clicable se sigue con el localizado por presencia y do_action aplica el
    # fallback por JS. Sólo acota cuánto se espera de más.
    interactable_timeout = int(os.getenv("SELENIUM_INTERACTABLE_TIMEOUT", "5"))

    # extra_actions que manipulan el WebElement localizado. El resto ("script",
    # "hover", "drag_and_drop", "move_cursor_end") actúan por JS o sobre otros
    # XPath, así que no requieren que el elemento sea clicable.
    ELEMENT_DRIVEN_ACTIONS = frozenset({"setvalue", "clearinput", "sweetalert_comfirm"})

    # Excepciones que indican que el DOM cambió bajo los pies o que el elemento
    # aún no estaba listo: merecen relocalizar y reintentar una vez.
    RETRY_EXCEPTIONS = (
        StaleElementReferenceException,
        ElementNotInteractableException,
        MoveTargetOutOfBoundsException,
    )

    _server_exceptions = []
    _server_exceptions_lock = threading.Lock()

    @classmethod
    def get_sleep_factor(cls):
        if cls.sleep_factor is not None:
            return cls.sleep_factor
        default = "1" if getattr(settings, "GENERATE_SCREENSHOTS", True) else "0.1"
        try:
            return float(os.getenv("SELENIUM_SLEEP_FACTOR", default))
        except ValueError:
            return float(default)

    def scaled_sleep(self, seconds):
        """Duerme `seconds` escalados por el factor configurado."""
        delay = seconds * self.get_sleep_factor()
        if delay > 0:
            sleep(delay)

    def diagnose_page(self, tag=""):
        """Vuelca el estado del navegador cuando una página no termina de cargar.

        Un `TimeoutException` en `get()` no dice nada por sí solo. Esto responde
        a las tres preguntas que lo explican: si hay un diálogo abierto (que
        impide el evento `load`), en qué punto se quedó el documento y qué
        peticiones siguen sin respuesta.
        """
        prefix = "[diag %s]" % tag
        try:
            print(prefix, "url:", self.selenium.current_url)
            print(
                prefix,
                "readyState:",
                self.selenium.execute_script("return document.readyState"),
            )
        except Exception as exc:  # noqa: BLE001
            print(prefix, "no se pudo interrogar la página:", type(exc).__name__)
            return

        try:
            print(prefix, "ALERTA:", repr(self.selenium.switch_to.alert.text))
        except Exception as exc:  # noqa: BLE001
            print(prefix, "sin alerta abierta (%s)" % type(exc).__name__)

        try:
            pending = self.selenium.execute_script(
                "return (performance.getEntriesByType('resource') || [])"
                ".filter(r => r.responseEnd === 0).map(r => r.name);"
            )
            print(prefix, "peticiones sin respuesta:", pending)
        except Exception:  # noqa: BLE001
            pass

        if getattr(self, "collect_browser_logs", False):
            try:
                for entry in self.selenium.get_log("browser"):
                    print(prefix, "consola:", entry.get("level"), entry.get("message"))
            except Exception as exc:  # noqa: BLE001
                print(prefix, "sin log de consola:", type(exc).__name__)
            self._dump_network_log(prefix)

    def _dump_network_log(self, prefix):
        """Resume el log de red de Chrome: qué se pidió y qué se respondió.

        `performance.getEntriesByType` sólo ve los recursos del documento ya
        cargado, así que no muestra la navegación que no llegó a completarse.
        El log de red del navegador sí la registra, y es lo que distingue
        "el navegador nunca emitió la petición" de "la emitió y no obtuvo
        respuesta".
        """
        import json as json_module

        try:
            entries = self.selenium.get_log("performance")
        except Exception as exc:  # noqa: BLE001
            print(prefix, "sin log de red:", type(exc).__name__)
            return

        sent, answered, failed = {}, set(), []
        for entry in entries:
            try:
                message = json_module.loads(entry["message"])["message"]
            except (KeyError, ValueError):
                continue
            method = message.get("method", "")
            params = message.get("params", {})
            request_id = params.get("requestId")
            if method == "Network.requestWillBeSent":
                sent[request_id] = params.get("request", {}).get("url", "")
            elif method in ("Network.responseReceived", "Network.loadingFinished"):
                answered.add(request_id)
            elif method == "Network.loadingFailed":
                answered.add(request_id)
                failed.append(
                    (
                        sent.get(request_id, "?"),
                        params.get("errorText"),
                        params.get("blockedReason"),
                    )
                )

        pending = [url for rid, url in sent.items() if rid not in answered]
        print(
            prefix,
            "red: %d peticiones emitidas, %d sin respuesta, %d fallidas"
            % (len(sent), len(pending), len(failed)),
        )
        for url in pending[:10]:
            print(prefix, "  emitida SIN respuesta:", url[:160])
        for url, error, blocked in failed[:10]:
            print(prefix, "  FALLÓ:", error, blocked or "", url[:120])

    def open_url(self, url, tag=""):
        """Navega a `url`, dejando un diagnóstico si la carga no termina."""
        from selenium.common.exceptions import TimeoutException

        try:
            self.selenium.get(url)
        except TimeoutException:
            self.diagnose_page(tag or url)
            raise

    def step_needs_interaction(self, obj):
        """Indica si el paso va a manipular el WebElement que se localice.

        Los pasos que actúan por JS o sobre otros XPath no necesitan que el
        elemento sea clicable, así que esperarlo sólo les costaría tiempo.
        """
        if obj.get("presence_only"):
            return False
        extra = obj.get("extra_action")
        if extra is None:
            return True  # sin extra_action el paso hace click
        return extra in self.ELEMENT_DRIVEN_ACTIONS

    def find_element_waiting(self, xpath, obj=None):
        """Busca por XPath esperando a que aparezca.

        Sustituye la espera fija por una condicional: el test avanza en cuanto
        el elemento existe, en vez de dormir un tiempo fijo estimado a ojo.

        Si el paso va a interactuar con el elemento se espera además a que sea
        clicable. Esa segunda espera es best-effort: si vence se devuelve el
        elemento localizado por presencia y do_action se encarga del fallback,
        de modo que este método nunca falla por algo que antes pasaba.
        """
        from selenium.webdriver.support import expected_conditions as EC

        # Sin esto el TimeoutException llega con el mensaje vacío y no se sabe
        # qué selector falló ni en qué página.
        message = "no apareció %s en %s s (url: %s)" % (
            xpath,
            self.element_timeout,
            self.selenium.current_url,
        )
        try:
            element = WebDriverWait(self.selenium, self.element_timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath)),
                message=message,
            )
        except TimeoutException:
            # El respaldo cubre el caso de que el nodo aparezca justo al vencer
            # la espera. Si tampoco está, se conserva el mensaje con XPath y URL:
            # es el único dato que permite clasificar el fallo después.
            try:
                return self.selenium.find_element(By.XPATH, xpath)
            except NoSuchElementException as exc:
                raise NoSuchElementException(message) from exc

        if obj is not None and self.step_needs_interaction(obj):
            try:
                # element_to_be_clickable re-localiza por XPath, así que además
                # de esperar visibilidad devuelve una referencia fresca: evita
                # el StaleElementReference del caso común.
                element = WebDriverWait(self.selenium, self.interactable_timeout).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
            except Exception:
                pass  # nunca llegó a ser clicable: sigue el de presencia
        return element

    @classmethod
    def _on_request_exception(cls, sender, request, **kwargs):
        exc_type, exc_value, exc_tb = sys.exc_info()
        import traceback as tb_module
        entry = {
            'url': request.path if request else 'unknown',
            'method': request.method if request else 'unknown',
            'exception_type': exc_type.__name__ if exc_type else 'unknown',
            'exception_value': str(exc_value) if exc_value else '',
            'traceback': tb_module.format_exception(exc_type, exc_value, exc_tb),
        }
        with cls._server_exceptions_lock:
            cls._server_exceptions.append(entry)

    @classmethod
    def setUpClass(cls):
        super(SeleniumBase, cls).setUpClass()

        cls.timeout = 5
        cls.options = webdriver.FirefoxOptions()
        is_docker = os.getenv("DOCKER_ACTIVE", "false").lower() == "true"

        # Un test que deja abierta una alerta JS bloquea el driver: todos los
        # comandos siguientes esperan hasta agotar el timeout del cliente (120 s
        # por defecto), y esa espera se paga en cada paso restante del test.
        # Descartarlas automáticamente evita que un aviso de DataTables
        # convierta un fallo instantáneo en dos minutos de bloqueo.
        prompt_behavior = os.getenv("SELENIUM_PROMPT_BEHAVIOR", "dismiss")
        # SELENIUM_BROWSER_LOGS=1 vuelca consola y red en el diagnóstico. Las
        # capacidades de logging, en cambio, se piden SIEMPRE: pedirlas hace que
        # chromedriver habilite el dominio Network de DevTools, y con él las
        # navegaciones dejan de colgarse.
        #
        # Medido sobre Cap5ManageReservationsTest, dos corridas de cada caso:
        #   sin las capacidades -> 310 s, 6 errores
        #   con las capacidades ->  91 s, todo en verde
        # Sin ellas, el navegador se quedaba sin respuesta en la segunda prueba
        # de cada clase mientras el servidor contestaba a curl en milisegundos.
        # No está claro por qué lo arregla, así que se deja documentado y con
        # una salida para desactivarlo si alguna vez estorba.
        cls.collect_browser_logs = os.getenv("SELENIUM_BROWSER_LOGS") == "1"
        enable_devtools_logging = os.getenv("SELENIUM_DEVTOOLS_LOGGING", "1") == "1"

        # "normal" espera al evento `load`; "eager" devuelve el control en
        # DOMContentLoaded. Se deja configurable porque es lo primero que se
        # prueba cuando una página no termina de cargar, aunque para el cuelgue
        # de las pruebas de reservaciones se comprobó que no cambia nada.
        page_load_strategy = os.getenv("SELENIUM_PAGE_LOAD_STRATEGY", "normal")

        if is_docker:
            driverpath = os.getenv("CHROMEDRIVER_DIR", "/usr/bin/chromedriver")
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--headless")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--remote-debugging-port=9222")
            options.unhandled_prompt_behavior = prompt_behavior
            options.page_load_strategy = page_load_strategy
            if enable_devtools_logging:
                options.set_capability(
                    "goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"}
                )
            service = Service(executable_path=driverpath)
            cls.selenium = webdriver.Chrome(options=options, service=service)
        else:
            options = webdriver.ChromeOptions()
            options.unhandled_prompt_behavior = prompt_behavior
            options.page_load_strategy = page_load_strategy
            if enable_devtools_logging:
                options.set_capability(
                    "goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"}
                )
            cls.selenium = webdriver.Chrome(options=options)

        # El cliente HTTP contra el chromedriver espera 120 s por respuesta: un
        # test bloqueado no falla, se queda dos minutos esperando en cada paso.
        # Se recorta para que el fallo llegue pronto y con su error real.
        client_config = getattr(cls.selenium.command_executor, "_client_config", None)
        if client_config is not None:
            client_config.timeout = int(os.getenv("SELENIUM_COMMAND_TIMEOUT", "60"))

        cls.selenium.set_page_load_timeout(
            int(os.getenv("SELENIUM_PAGE_LOAD_TIMEOUT", "45"))
        )
        cls.selenium.set_script_timeout(
            int(os.getenv("SELENIUM_SCRIPT_TIMEOUT", "30"))
        )
        cls.ob = Screenshot(cls.selenium)
        cls.selenium.set_window_size(1280, 720)

        cls.tmp = Path(getattr(settings, 'SELENIUM_SCREENSHOTS_DIR', Path(settings.BASE_DIR) / "tmp"))
        cls.screenshot_size = "1280x720"
        cls.folder = "%s/%s" % (cls.tmp, cls.screenshot_size)
        cls.dir = Path(cls.folder)
        cls.static_save_path = Path(settings.DOCS_SOURCE_DIR) / "_static"
        cls.save_path_gif = cls.static_save_path / "gif"

        cls.tmp.mkdir(exist_ok=True)
        cls.save_path_gif.mkdir(parents=True, exist_ok=True)

        cls.cursor_script = """
            var cursor = document.createElement('i');
            cursor.style.position = 'absolute';
            cursor.style.zIndex = '9999';
            cursor.classList.add("fa", "fa-mouse-pointer", "text-danger", "fa-1x", "cursor_pointer");
            document.body.appendChild(cursor);
        """

        cls.hide_cursor_script = """
        var cursor = document.querySelector(".cursor_pointer");
        if (cursor) { cursor.style.zIndex = '-1'; }
        """

        cls.show_cursor_script = """
            if(!$('.cursor_pointer').length > 0){
            """
        cls.show_cursor_script += cls.cursor_script
        cls.show_cursor_script += """
            }
            var cursor = document.querySelector(".cursor_pointer");
            if (cursor) { cursor.style.zIndex = '9999'; }
            """

        cls.action = ActionChains(cls.selenium)

    def setUp(self):
        super().setUp()
        # Pasos que necesitaron el click por JS. No hacen fallar el test, pero
        # se avisan: cada uno es una interacción que el usuario real no podría
        # completar tal cual.
        self.js_click_fallbacks = []
        with self._server_exceptions_lock:
            self._server_exceptions.clear()
        from django.core.signals import got_request_exception
        got_request_exception.connect(
            self._on_request_exception,
            dispatch_uid='selenium_test_exception_handler'
        )

    def tearDown(self):
        from django.core.signals import got_request_exception
        got_request_exception.disconnect(
            dispatch_uid='selenium_test_exception_handler'
        )
        if getattr(self, 'js_click_fallbacks', None):
            print(
                "\n[selenium] %s usó click por JS en: %s"
                % (self.id(), ', '.join(self.js_click_fallbacks))
            )
        with self._server_exceptions_lock:
            exceptions = list(self._server_exceptions)
            self._server_exceptions.clear()
        if exceptions:
            messages = []
            for exc in exceptions:
                tb_str = ''.join(exc['traceback'])
                messages.append(
                    "Server error on %s %s: %s: %s\n%s"
                    % (exc['method'], exc['url'], exc['exception_type'],
                       exc['exception_value'], tb_str)
                )
            self.fail(
                "Server returned %d unhandled exception(s) during test:\n\n%s"
                % (len(exceptions), '\n---\n'.join(messages))
            )
        super().tearDown()

    def change_focus_tab(self, window_name):
        self.selenium.switch_to.window(window_name)

    def get_format_increase_decrease_date(
        self, date, days, increase=True, format="%m/%d/%Y"
    ):
        new_date = date + relativedelta(days=days)
        if not increase:
            new_date = date - relativedelta(days=days)
        return new_date, new_date.strftime(format)

    def move_cursor_script(self, x, y):
        """
        Move the div that simulate a cursor
        """
        return """
        var cursor = document.querySelector('.cursor_pointer');
        if (cursor) {{
                cursor.style.left= '{}px';
                cursor.style.top= '{}px';
        }}
                """.format(
            x, y
        )

    def get_element_js_by_xpath(self, path):
        return (
            """
            function getElementByXpath(path) {
              return document.evaluate(path, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            }
            var element = getElementByXpath("%s");
            """
            % path
        )

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
        try:
            self.action.move_to_element(element).perform()
        except ElementNotInteractableException:
            from selenium.webdriver.support import expected_conditions as EC
            WebDriverWait(self.selenium, 5).until(EC.visibility_of(element))
            self.action = ActionChains(self.selenium)
            self.action.move_to_element(element).perform()

    def create_directory_path(self, url=None, folder_name=""):
        """
        Folder name is a specific name by action, for example 'create_org',
        'view_org_users', etc
        """

        if url:
            self.selenium.get(url)

        if not getattr(settings, 'GENERATE_SCREENSHOTS', True):
            return

        self.folder = "%s/%s" % (self.tmp, self.screenshot_size)
        self.dir = Path(self.folder)

        path_with_folder_name = self.dir / folder_name

        self.dir.mkdir(exist_ok=True)
        path_with_folder_name.mkdir(exist_ok=True)

        self.dir = path_with_folder_name

    def create_screenshot(self, order=1, time_out=None, name="", save_screenshot=False):
        if not getattr(settings, 'GENERATE_SCREENSHOTS', True):
            return order + 1

        if time_out is None:
            time_out = self.screenshot_delay
        extension_name = "%s.png" % name
        order_name = "%r.png" % order
        sleep(time_out)
        self.selenium.save_screenshot(
            str(Path(self.dir / order_name).absolute().resolve())
        )

        if save_screenshot:
            self.selenium.save_screenshot(
                str(Path(self.static_save_path / extension_name).absolute().resolve())
            )

        order += 1
        return order

    def get_gif_images(self, file_url):
        gif_images = []
        folder_images = glob.glob("{}/*.png".format(file_url))
        tuple_images = [
            (int(image.split("/").pop().split(".")[0]), image)
            for image in folder_images
        ]
        sorted_images_list = [x[1] for x in sorted(tuple_images)]

        for filename in sorted_images_list:  # loop through all png files in the folder
            im = Image.open(filename)  # open the image
            gif_images.append(im)  # add the image to the list

        return gif_images

    def create_gif(self, file_url, folder):
        if not getattr(settings, 'GENERATE_SCREENSHOTS', True):
            return

        gif_images = self.get_gif_images(file_url)

        # save as a gif
        gif_name = "/%s%s" % (folder, ".gif")
        gif_images[0].save(
            str(self.save_path_gif) + gif_name,
            save_all=True,
            append_images=gif_images[1:],
            optimize=False,
            duration=500,
            loop=0,
        )

    def get_x_y_element(self, element):
        return (
            element.location["x"] + element.size["width"] / 4,
            element.location["y"] + element.size["height"] / 4,
        )

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
        if "screenshot_name" in obj and obj["screenshot_name"]:
            order = self.create_screenshot(
                order=order, name=obj["screenshot_name"], save_screenshot=True
            )
        else:
            order = self.create_screenshot(order=order)

        return order

    def set_value_action(self, obj, element):
        """
        This is an action responsible to set value in an element.
        Value can be quotation marks this is equal to clear an input.

        No se limpia por defecto: hay flujos que escriben el valor por partes
        (move_cursor_end, máscaras con reduce_length) y se romperían. Para
        limpiar antes, usar "clear": True.
        """
        if "value" not in obj:
            return

        if obj.get("clear"):
            element.clear()

        try:
            element.send_keys(obj["value"])
        except self.RETRY_EXCEPTIONS:
            fresh = self.relocate(obj)
            if fresh is None:
                raise
            try:
                fresh.send_keys(obj["value"])
            except ElementNotInteractableException:
                # Input tapado por un widget (select2, iCheck, editores): se
                # asigna el valor por JS y se notifican los eventos, que es lo
                # que escucha jQuery.
                self.selenium.execute_script(
                    "arguments[0].value = arguments[1];"
                    "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                    "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                    fresh,
                    obj["value"],
                )

    def move_cursor_end(self, obj):
        """
        It moves cursor to the end input value length.
        reduce_length variable is for special cases like email mask input where it is
        necessary reduce input value length.
        """
        reduce_length = 0

        if "reduce_length" in obj and obj["reduce_length"]:
            reduce_length = obj["reduce_length"]

        move_cursor_end = (
            self.get_element_js_by_xpath(obj["path"])
            + """
            const end = element.value.length - %d;
            element.setSelectionRange(end, end);
            element.focus();
        """
            % (reduce_length)
        )
        self.selenium.execute_script(move_cursor_end)

    def set_css_element(self, target):
        return """
            $(".component-btn-group").first().css("display", "block");
            """

    def wait_for_page_ready(self, timeout=10):
        try:
            WebDriverWait(self.selenium, timeout).until(
                lambda driver: driver.find_element(
                    By.TAG_NAME, 'body'
                ).get_attribute('data-organilab-ready') == 'true'
            )
        except Exception:
            sleep(2)
        self.selenium.execute_script(
            "document.body.removeAttribute('data-organilab-ready');"
        )

    def wait_for_datatables_idle(self, timeout=10):
        """Espera a que no queden peticiones AJAX de DataTables en vuelo.

        Complementa a wait_for_page_ready(), que sólo cubre la carga inicial:
        tras un ajax.reload() el <tbody> se reemplaza entero y el elemento que
        ya se había localizado queda obsoleto. Best-effort: en páginas sin
        DataTables la variable es undefined y retorna de inmediato.
        """
        try:
            WebDriverWait(self.selenium, timeout).until(
                lambda driver: driver.execute_script(
                    "return window.__organilabPendingDT === undefined"
                    " || window.__organilabPendingDT === 0;"
                )
            )
        except Exception:
            pass

    def active_hidden_elements(self, obj):
        """
        Display hidden elements, for example in dropdowns or elements that are hidden.
        """
        move_cursor = (
            self.get_element_js_by_xpath(obj["active_hidden_elements"])
            + """
        element.click();
        """
        )
        self.scaled_sleep(obj.get("active_hidden_timeout", 5))
        self.selenium.execute_script(move_cursor)

    def extra_action(self, obj, element):
        """
        This function will list all required actions in selenium tests.
        """
        if obj["extra_action"] == "setvalue":
            self.set_value_action(obj, element)
        elif obj["extra_action"] == "script":
            self.selenium.execute_script(obj["value"])
        elif obj["extra_action"] == "sweetalert_comfirm":
            self.do_sweetaler_comfirm_action(obj, element)
        elif obj["extra_action"] == "clearinput":
            element.clear()
        elif obj["extra_action"] == "move_cursor_end":
            self.move_cursor_end(obj)
        elif obj["extra_action"] == "hover":
            self.selenium.execute_script(self.set_css_element(".component-btn-group"))
        elif obj["extra_action"] == "drag_and_drop":
            self.drag_and_drop_action(obj)

    def drag_and_drop_action(self, obj, attempts=3):
        """Arrastra obj["x"] hasta obj["y"] simulando el gesto paso a paso.

        ActionChains.drag_and_drop() emite mousedown y mouseup casi seguidos y
        sin mousemove intermedios. Las librerías de arrastre basadas en eventos
        de ratón (dragula, que es la que usa el constructor de formularios de
        formio) nunca llegan a considerar iniciado el arrastre y el elemento se
        queda donde estaba, así que el diálogo del componente no se abre y el
        paso siguiente falla como si su selector fuese incorrecto.

        Aun con los movimientos intermedios el gesto es sensible al ritmo del
        navegador, así que se reintenta: `expect` (si se indica) es el XPath de
        lo que debe aparecer al soltar, y sirve para saber si hizo efecto.
        """
        expect = obj.get("expect")

        for attempt in range(attempts):
            source = self.selenium.find_element(By.XPATH, obj["x"])
            target = self.selenium.find_element(By.XPATH, obj["y"])

            self.action.move_to_element(source).click_and_hold().perform()
            self.scaled_sleep(0.2)
            # El primer desplazamiento es el que marca el inicio del arrastre.
            self.action.move_by_offset(10, 10).perform()
            self.scaled_sleep(0.2)
            self.action.move_to_element(target).perform()
            self.scaled_sleep(0.2)
            # Un segundo movimiento sobre el destino asegura que se calcule la
            # posición de inserción antes de soltar.
            self.action.move_by_offset(0, 5).perform()
            self.scaled_sleep(0.2)
            self.action.release().perform()

            if not expect:
                return
            try:
                WebDriverWait(self.selenium, self.interactable_timeout).until(
                    lambda driver: driver.find_elements(By.XPATH, expect)
                )
                return
            except Exception:
                if attempt == attempts - 1:
                    raise
                self.scaled_sleep(1)

    def do_sweetaler_comfirm_action(self, obj, element):
        """
        This is an action responsible to press yes/no buttons of sweetalert.
        """
        self.action.move_to_element(element).perform()
        element.click()
        self.scaled_sleep(1)
        self.selenium.execute_script(obj["comfirm"])
        self.scaled_sleep(1)
        self.selenium.execute_script(obj["comfirm"])

    def relocate(self, obj):
        """Vuelve a localizar el elemento del paso tras un cambio del DOM."""
        from selenium.webdriver.support import expected_conditions as EC

        try:
            return WebDriverWait(self.selenium, self.interactable_timeout).until(
                EC.element_to_be_clickable((By.XPATH, obj["path"]))
            )
        except Exception:
            try:
                return self.selenium.find_element(By.XPATH, obj["path"])
            except NoSuchElementException:
                return None

    def js_click(self, obj, element):
        """Click por JS. Último recurso, sólo sobre elementos visibles.

        Un click por JS sobre un nodo oculto dejaría el test en verde ejecutando
        una acción que el usuario no podría realizar: eso es un falso verde, no
        una reparación.
        """
        if not (element.is_displayed() or obj.get("force_click")):
            raise ElementNotInteractableException(
                "el elemento de %s existe pero no es visible; si es intencional "
                "usa force_click=True o extra_action='script'" % obj["path"]
            )
        self.js_click_fallbacks.append(obj["path"])
        self.selenium.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});arguments[0].click();",
            element,
        )

    def click_element(self, obj, element, retried=False):
        try:
            self.action.move_to_element(element).perform()
            element.click()
        except ElementClickInterceptedException:
            self.js_click(obj, element)
        except self.RETRY_EXCEPTIONS:
            # El DOM cambió bajo los pies (típicamente una recarga de DataTable)
            # o el elemento todavía no estaba pintado: se relocaliza y se
            # reintenta una sola vez antes de caer al click por JS.
            if not retried:
                fresh = self.relocate(obj)
                if fresh is not None:
                    return self.click_element(obj, fresh, retried=True)
            self.js_click(obj, element)

    def do_action(self, obj, element):
        """
        This function applies the respective action by obj path.
        """
        if "extra_action" not in obj:
            return self.click_element(obj, element)

        try:
            self.extra_action(obj, element)
        except self.RETRY_EXCEPTIONS:
            if not self.step_needs_interaction(obj):
                raise  # actúa por JS: el fallo es real, no de sincronía
            fresh = self.relocate(obj)
            if fresh is None:
                raise
            self.extra_action(obj, fresh)

    def apply_utils(self, obj):

        if "scroll" in obj:
            self.selenium.execute_script(obj["scroll"])

        if "modalscroll" in obj:
            self.selenium.execute_script(obj["modalscroll"])

        if "active_hidden_elements" in obj:
            self.active_hidden_elements(obj)

        if "hover" in obj:
            self.selenium.execute_script(self.set_css_element(obj["element"]))

        if "wait_dt" in obj:
            self.wait_for_datatables_idle(
                obj["wait_dt"] if isinstance(obj["wait_dt"], int) else 10
            )

        if "wait_ready" in obj:
            timeout = obj["wait_ready"] if isinstance(obj["wait_ready"], int) else 10
            self.wait_for_page_ready(timeout=timeout)
        elif "sleep" in obj:
            self.scaled_sleep(obj["sleep"] if isinstance(obj["sleep"], int) else 15)

    def assert_no_server_error(self, context_msg=''):
        try:
            page_source = self.selenium.page_source
        except Exception:
            return

        if not page_source:
            return

        is_debug_500 = (
            '<div id="traceback">' in page_source
            or ('<header id="summary">' in page_source and 'Exception Type:' in page_source)
        )
        is_production_500 = '<title>Server Error (500)</title>' in page_source

        if is_debug_500 or is_production_500:
            current_url = self.selenium.current_url
            error_detail = ''
            if is_debug_500:
                title_match = re.search(r'<title>([^<]+)</title>', page_source)
                value_match = re.search(r'<pre class="exception_value">([^<]+)</pre>', page_source)
                if title_match:
                    error_detail += 'Exception: %s' % title_match.group(1)
                if value_match:
                    error_detail += '\nValue: %s' % value_match.group(1)

            with self._server_exceptions_lock:
                signal_exceptions = list(self._server_exceptions)
                self._server_exceptions.clear()

            signal_detail = ''
            if signal_exceptions:
                for exc in signal_exceptions:
                    tb_str = ''.join(exc['traceback'])
                    signal_detail += '\n--- Server traceback ---\n%s' % tb_str

            msg = 'Server Error (500) at: %s' % current_url
            if context_msg:
                msg += '\nDuring: %s' % context_msg
            if error_detail:
                msg += '\n%s' % error_detail
            if signal_detail:
                msg += signal_detail

            self.fail(msg)

    def take_screenshot_list(
        self, path_list, folder_name, cursor=True, hover=True, order=1
    ):
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

        When GENERATE_SCREENSHOTS is False, all test actions (find_element, do_action,
        apply_utils, assert_no_server_error) still execute, but screenshot capture,
        cursor animation, and sleep delays are skipped for faster test execution.
        """
        generate = getattr(settings, 'GENERATE_SCREENSHOTS', True)
        if generate:
            self.create_directory_path(folder_name=folder_name)
            self.create_screenshot(order=order)
        for index, obj in enumerate(path_list, start=1):
            step_error = None
            try:
                self.apply_utils(obj)
                self.assert_no_server_error(
                    context_msg='before finding element: %s' % obj.get('path', '?')
                )
                element = self.find_element_waiting(obj["path"], obj)
                if generate:
                    order = self.create_screenshot(order=order)
                    x, y = self.get_x_y_element(element)
                    self.activate_move_cursor(element, cursor, hover)
                    order = self.take_screenshot_by_obj(obj, order)
                    self.hide_show_cursor(cursor, show_cursor=False)
                self.do_action(obj, element)
                if generate:
                    self.hide_show_cursor(cursor, x=x, y=y)
                    order = self.create_screenshot(order=order)
                self.assert_no_server_error(
                    context_msg='after action on: %s' % obj.get('path', '?')
                )
            except Exception as exc:
                # Sin saber qué paso del path_list falló, clasificar el error
                # obliga a releer el test entero. El tipo de excepción se
                # conserva porque es lo que distingue un selector roto de un
                # problema de sincronía.
                context = "paso %d/%d de '%s' | xpath=%s | url=%s" % (
                    index,
                    len(path_list),
                    folder_name,
                    obj.get("path"),
                    self.selenium.current_url,
                )
                if getattr(exc, "msg", None) is not None:
                    exc.msg = "%s\n%s" % (context, exc.msg)
                    raise
                step_error = "%s\n%s: %s" % (context, type(exc).__name__, exc)
            # Fuera del except a propósito: encadenar la excepción deja un
            # __cause__ con su traceback, y con --parallel Django tiene que
            # serializar el fallo entre procesos (falla con "cannot pickle
            # 'traceback' object" salvo que tblib esté instalado).
            if step_error is not None:
                raise AssertionError(step_error)
        return order

    def create_gif_process(
        self, path_list, folder_name, cursor=True, hover=True, order=1
    ):
        self.take_screenshot_list(path_list, folder_name, cursor, hover, order)
        self.create_gif(self.dir, folder_name)

    def create_gif_by_change_focus_tab(
        self, general_path_list, tab_name_list, folder_name
    ):
        order = 0
        screenshot_order = 1

        for path_list in general_path_list:
            screenshot_order = self.take_screenshot_list(
                path_list, folder_name, order=screenshot_order
            )

            if len(tab_name_list) > 0 and order + 1 <= len(tab_name_list):
                self.change_focus_tab(tab_name_list[order])
                order += 1

        self.create_gif(self.dir, folder_name)

    # --- Permission helpers ---

    @classmethod
    def create_user_with_profile(
        cls, username, email, password='testpass123',
        first_name='', last_name='',
        id_card='000000000', phone_number='',
        job_position='', language='es'
    ):
        from django.contrib.auth.models import User
        from auth_and_perms.models import Profile
        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name
        )
        Profile.objects.create(
            user=user, id_card=id_card, phone_number=phone_number,
            job_position=job_position, language=language
        )
        return user

    @classmethod
    def create_role(cls, name, permission_codenames):
        from auth_and_perms.models import Rol
        from django.contrib.auth.models import Permission
        rol = Rol.objects.create(name=name)
        if permission_codenames:
            perms = Permission.objects.filter(codename__in=permission_codenames)
            rol.permissions.set(perms)
        return rol

    @classmethod
    def assign_roles_to_user(cls, user, target_object, roles):
        from auth_and_perms.models import ProfilePermission
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(target_object)
        pp, _ = ProfilePermission.objects.get_or_create(
            profile=user.profile,
            content_type=ct,
            object_id=target_object.pk,
        )
        pp.rol.add(*roles)
        return pp

    @classmethod
    def grant_all_roles(cls, user, organization):
        from auth_and_perms.models import Rol
        return cls.assign_roles_to_user(user, organization, list(Rol.objects.all()))

    @classmethod
    def add_user_to_organization(cls, user, organization, user_type=3):
        from laboratory.models import UserOrganization
        UserOrganization.objects.get_or_create(
            user=user, organization=organization,
            defaults={'type_in_organization': user_type, 'status': True}
        )

    def force_login(self, user, driver, base_url):
        from django.conf import settings

        SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
        # Sólo hace falta estar en el dominio para poder dejar la cookie.
        self.open_url(base_url, tag="force_login.get")

        session = SessionStore()
        session[SESSION_KEY] = user._meta.pk.value_to_string(user)
        session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session.save()

        cookie = {
            "name": settings.SESSION_COOKIE_NAME,
            "value": session.session_key,
            "path": "/",
        }
        driver.add_cookie(cookie)
        from selenium.common.exceptions import TimeoutException

        try:
            driver.refresh()
        except TimeoutException:
            self.diagnose_page("force_login.refresh")
            raise

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        # Do not remove tmp/ or its subdirectories here.
        # In parallel mode, multiple workers share the same tmp/ tree
        # and removing it would break other workers' screenshot writes.
        # The tmp/ directory is ephemeral and can be cleaned up by CI
        # or manually after a test run.
        if getattr(settings, 'GENERATE_SCREENSHOTS', True) and cls.tmp.exists():
            print("\nScreenshots saved to: %s" % cls.tmp)
        super(SeleniumBase, cls).tearDownClass()


def modifies_db(test_method):
    """Marca un test que modifica la base de datos.
    El siguiente test en la clase recibirá un reload completo de fixtures."""
    test_method._modifies_db = True
    return test_method


class OptimizedSeleniumBase(SeleniumBase):
    """SeleniumBase con carga de fixtures optimizada.

    - Carga fixtures UNA VEZ en el primer test de la clase
    - NO hace flush entre tests a menos que el test anterior esté marcado con @modifies_db
    - Fallback: always_reload_fixtures = True restaura el comportamiento original
    """

    always_reload_fixtures = False
    _class_fixtures_loaded = False
    _needs_reload = False

    @classmethod
    def setUpClass(cls):
        cls._class_fixtures_loaded = False
        cls._needs_reload = False
        super().setUpClass()

    @classmethod
    def _fixture_setup(cls):
        if cls._class_fixtures_loaded and not cls._needs_reload and not cls.always_reload_fixtures:
            return

        from django.core.management import call_command
        from django.db import connections
        for db_name in cls._databases_names(include_mirrors=False):
            if cls.reset_sequences:
                cls._reset_sequences(db_name)
            if cls.serialized_rollback and hasattr(
                connections[db_name], "_test_serialized_contents"
            ):
                from django.apps import apps
                if cls.available_apps is not None:
                    apps.unset_available_apps()
                connections[db_name].creation.deserialize_db_from_string(
                    connections[db_name]._test_serialized_contents
                )
                if cls.available_apps is not None:
                    apps.set_available_apps(cls.available_apps)
            if cls.fixtures:
                call_command("loaddata", *cls.fixtures, verbosity=0, database=db_name)

        cls._class_fixtures_loaded = True
        cls._needs_reload = False

    def _fixture_teardown(self):
        test_method = getattr(self, self._testMethodName, None)
        did_modify = (
            self.always_reload_fixtures
            or getattr(test_method, '_modifies_db', False)
        )

        if did_modify:
            from django.core.management import call_command
            from django.db import connections
            for db_name in self._databases_names(include_mirrors=False):
                inhibit_post_migrate = (
                    self.available_apps is not None
                    or (
                        self.serialized_rollback
                        and hasattr(connections[db_name], "_test_serialized_contents")
                    )
                )
                call_command(
                    "flush", verbosity=0, interactive=False,
                    database=db_name, reset_sequences=False,
                    allow_cascade=self.available_apps is not None,
                    inhibit_post_migrate=inhibit_post_migrate,
                )
            self.__class__._needs_reload = True
