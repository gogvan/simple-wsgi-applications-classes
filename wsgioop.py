from urllib.parse import parse_qs
from json import dumps as json_dumps
from PIL import Image
from re import sub as re_sub
#from time import sleep
import pymupdf, base64

class Out_Data():
    def __init__(self):
        self.__status = '200 OK'
        self.__data = {}
    
    @property
    def get_status(self) -> str:
        return self.__status
    
    @property
    def get_data(self) -> dict:
        return self.__data
    
    def _set_status(self, status = '200 OK'):
        self.__status = status
    
    def _set_data(self, key = 'key', value = 'value'):
        key, value = str(key), str(value)
        if key in self.__data:
            self.__data[key].append(value)
        else:
            self.__data[key] = [value]
        
class In_Data(Out_Data):
    __array_name_action = ('get_pic', 'get_text', 'get_environ')
    __array_name_method = ('get', 'post')
    
    def _check_int(self, num) -> int:
        num = re_sub(r'[^0-9]', '', num)
        if num == '':
            return 0
        else:
            return int(num)
    
    def _get_pic(self, page, search_text = ''):
        if search_text != '':
            page = self._search_text(page, search_text)
        pix = page.get_pixmap(dpi=120)
        
        img_bytes = pix.pil_tobytes(format='webp', optimize=True, quality = 92)
        img_encoded = base64.b64encode(img_bytes).decode()
        
        del page, pix, img_bytes
        return img_encoded
    
    def _search_text(self, page, search_text):
        self._set_data('search_text', search_text)
        text_instances = page.search_for(search_text)
        if len(text_instances) > 0:
            for inst in text_instances:
                highlight = page.add_highlight_annot(inst)
            highlight.update()
        return page
    
    def _open_doc(self, name_action, num_page = 0, search_text = ''):
        doc = pymupdf.open('book.pdf')
        page_count = doc.page_count
        self._set_data('page_count', page_count)
        
        if (num_page > page_count - 1):
            num_page = 0
        if (num_page < 0):
            num_page = page_count - 1
        self._set_data('num_page', num_page)
        
        if name_action == 'get_pic':
            page = doc[num_page]
            img_encoded = self._get_pic(page, search_text)
            self._set_data('img_encoded', img_encoded)
        elif name_action == 'get_text':
            text = doc.get_page_text(num_page)
            self._set_data('text', text)
        
        doc.close()
        
    def get_input(self, environ = {}):
        #sleep(.1)
        query_string = ''
        method = environ.get('REQUEST_METHOD', '').lower()
        if method in self.__array_name_method:
            if method == 'get':
                query_string = environ.get('QUERY_STRING', '')
            elif method == 'post':
                request_post_size = int(environ.get('CONTENT_LENGTH', 0))
                if request_data_size > 0:
                    query_string = environ['wsgi.input'].read(request_post_size).decode('utf-8')
            if query_string != '':
                query_dict = parse_qs(query_string)
                name_action = query_dict.get('name_action', [''])[0]
                if name_action in self.__array_name_action:
                    if name_action == 'get_environ':
                        for key, value in environ.items():
                            self._set_data(key, value)
                    else:
                        page = self._check_int(query_dict.get('page', ['0'])[0])
                        search_text = query_dict.get('search_text', [''])[0]
                        self._open_doc(name_action, page, search_text)
                else:
                    self._set_data('error', 'Ошибка, переменная name_action не определена')
            else:
                self._set_data('error', f'Ошибка, нет данных {method.upper()}!')
        else:
            self._set_data('error', f'Ошибка, {method.upper()}!')

class application(object):
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start = start_response
            
    def __iter__(self):
        self.dataout = In_Data()
        self.dataout.get_input(self.environ)
        
        status = self.dataout.get_status
        output = json_dumps(self.dataout.get_data).encode()
        response_headers = [('Content-type', 'text/json'),
                            ('Content-Length', str(len(output)))]
        self.start(status, response_headers)
        yield output

