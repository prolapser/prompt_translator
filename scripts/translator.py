import modules.scripts as scripts
from modules import script_callbacks
import gradio as gr

import gzip, json, os, re, requests, sys, time, urllib.parse as urllibparse, urllib.request as urllibrequest, urllib.error as urlliberror

class YandexFreeTranslateError(Exception):
    pass

class YandexFreeTranslate:
    siteurl = "https://translate.yandex.ru/"
    apibaseurl = "https://translate.yandex.net/api/v1/tr.json/"
    api = "ios"
    ua = r"Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 YaBrowser/23.9.0.1660 Mobile/15E148 Safari/604.1"
    keysuffix = "-0-0"
    keyfilename = os.path.join(os.path.expanduser("~"), ".YandexFreeTranslate.key")
    expiretime = 60 * 60 * 24 * 4
    backfilename = keyfilename + ".back"

    def __init__(self, api="ios"):
        self.api = api.lower()
        if not os.path.isfile(self.keyfilename) and os.path.isfile(self.backfilename):
            os.rename(self.backfilename, self.keyfilename)

    def _getparams(self, **p):
        params={'ios':{'srv':'ios','ucid':'9676696D-0B56-4F13-B4D5-4A3DA2A3344D','sid':'1A5A10A952AB4A3B82533F44B87EE696','id':'1A5A10A952AB4A3B82533F44B87EE696-0-0'}}
        params[self.api].update(p)
        return params[self.api]

    @staticmethod
    def decode_response(response):
        try:
            res = response.decode("UTF8")
        except UnicodeDecodeError:
            res = gzip.decompress(response).decode("UTF8")
        return res

    @staticmethod
    def _create_request(url, *ar, **kw):
        rq = urllibrequest.Request(url, *ar, **kw)
        return rq

    def _sid_to_key(self, sid):
        splitter = "."
        l = [item[::-1] for item in sid.split(splitter)]
        return splitter.join(l) + self.keysuffix

    @staticmethod
    def _create_opener():
        opener = urllibrequest.build_opener()
        return opener

    def _parse_sid(self):
        req = self._create_request(self.siteurl)
        req.add_header("User-Agent", self.ua)
        req.add_header("Accept", r"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8 ")
        req.add_header("Accept-Language", r"ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3")
        req.add_header("DNT", "1")
        req.add_header("Accept-Encoding", "gzip")
        response = self._create_opener().open(req).read()
        page = self.decode_response(response)
        try:
            return re.search(r'''SID[\s]?[:][\s]?['"]([^'"]+)['"]''', page).group(1)
        except AttributeError:
            raise YandexFreeTranslateError("SID заблокирован или не найден")

    def _save_key(self, key):
        with open(self.keyfilename, "w", encoding="utf8") as f:
            f.write(key)

    def _get_key(self):
        if os.path.isfile(self.keyfilename) and (time.time() - os.path.getmtime(self.keyfilename)) < self.expiretime:
            with open(self.keyfilename, "r", encoding="utf8") as f:
                return f.read()
        else:
            sid = self._parse_sid()
            key = self._sid_to_key(sid)
            self._save_key(key)
            return key

    def regenerate_key(self):
        if os.path.isfile(self.backfilename):
            os.remove(self.backfilename)
        if os.path.isfile(self.keyfilename):
            os.rename(self.keyfilename, self.backfilename)
        return self._get_key()

    @staticmethod
    def smartsplit(t, s, e):
        t = t.replace("\r\n", "\n").replace("\r", "\n")
        if e >= len(t):
            return [t]
        l = []
        tmp = ""
        for i, sim in enumerate(t, start=1):
            tmp += sim
            if i < s:
                continue
            if i == e:
                l.append(tmp)
                tmp = ""
                continue
            if i > s and i < e and sim in [chr(160), chr(9), chr(10), chr(32)]:
                l.append(tmp)
                tmp = ""
        if len(tmp) > 0:
            l.append(tmp)
        return l

    def translate(self, source="auto", target="", text=""):
        error_count = 0
        key = self._get_key()
        if source == "auto":
            source = ""
        if len(source) != 0 and len(source) != 2:
            raise ValueError("source")
        if len(target) == 0 or len(target) > 2:
            raise ValueError("target")
        if text == "":
            raise ValueError("text")
        if source == target:
            return text
        lang = source + "-" + target if source else target
        p = []
        for part in self.smartsplit(text, 500, 550):
            req = self._create_request(self.apibaseurl + "translate?" + urllibparse.urlencode(self._getparams(lang=lang)))
            req.add_header("User-Agent", self.ua)
            req.add_header("Accept", r"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8 ")
            req.add_header("Accept-Language", r"ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3")
            req.add_header("DNT", "1")
            req.add_header("Accept-Encoding", "gzip, deflate, br")
            try:
                response = self._create_opener().open(req, data=urllibparse.urlencode({
                    "text": part
                }).encode("UTF8")).read()
                content = self.decode_response(response)
                resp = json.loads(content)
            except (urlliberror.HTTPError, json.JSONDecodeError):
                if error_count >= 2:
                    if sys.exc_info()[0] == json.JSONDecodeError:
                        raise YandexFreeTranslateError(content)
                    else:
                        raise
                else:
                    error_count += 1
                    key = self.regenerate_key()
                    continue
            if "text" not in resp:
                raise YandexFreeTranslateError(content)
            p.append(resp["text"][0])
        return "\n".join(p)

def run(promt):
    try:
        return re.sub(r'\s+(:)', r'\1', re.sub(r'\s+', ' ', YandexFreeTranslate().translate("ru", "en", f"""{promt}""").replace('\n', ' ').replace(' :', ':').replace(': ', ':')))
    except:
        try:
            return re.sub(r'\s+(:)', r'\1', re.sub(r'\s+', ' ', ''.join([d[0] for d in requests.get("https://translate.google.com/translate_a/single", {"client": "gtx","sl": "ru","tl": "en","dt": "t","q": f"""{promt}"""}).json()[0]]).replace('\n', ' ').replace(' :', ':').replace(': ', ':')))
        except:
            return "какие-то неполадки: яндекс и гугл оба отказались перводить, возможно с этого ip нужно вводить уже капчу\n\n" + promt
def success():
    return "translated_ok"
class ExtensionTemplateScript(scripts.Script):
    def title(self):
        return "переводчик"
    def show(self, is_img2img):
        if not is_img2img:
            return scripts.AlwaysVisible
        else:
            return False
    def ui(self, is_img2img):
        with gr.Row(elem_id="hidden_translator", visible=False):
            prompt = gr.Textbox(label=None, lines=5, elem_id="text2translate")
            button = gr.Button("перевести", elem_id="translate_button")
            ok = gr.HTML("""<div id="ok"></div>""")
            button.click(fn=run, inputs=prompt, outputs=prompt).success(fn=success, _js="translate_ok", outputs=ok)

        return [prompt, button]

