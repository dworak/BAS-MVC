# Created by Lukasz Dworakowski on 1.05.2014.
# Copyright (c) 2014 Lukasz Dworakowski. All rights reserved.


__author__ = 'dworak'

# Uzytkowe
from cgi import escape
from urlparse import parse_qs
from random import randint


def http_status(code):
    return "200 OK" if code == 200 else "404 -  Not Found"


# Model
import shelve
import unicodedata


class TextModel(object):
    DB_FILE = 'main.db'

    def __init__(self):
        self._db = shelve.open(self.DB_FILE,writeback=True)
        self._db['users']       = []
        self._db['orders']      = {}
        self._db['products']    = []

    def getUser(self, name, default_value):
        return self._db['users'].get(name, default_value)

    def setUser(self, key):
        self._db['users'].append(key)
        self._db.sync()
    
    def deleteUser(self, key):
        index = self._db['users'].index(key)
        if index >= 0:
            del self._db['users'][index]
            self._db.sync()
        else:
            return

    def getOrder(self, name, default_value):
        return self._db['orders'].get(name, default_value)
    
    def setOrder(self, key, value, quantity, id):
        if value not in self._db['orders']:
            self._db['orders'][value] = {}
        
        self._db['orders'][value][key] = quantity
        self._db.sync()
    
    def deleteOrder(self, owner, key):
        del self._db['orders'][owner][key]
        self._db.sync()

    def allUsers(self):
        return self._db['users']

    def allOrders(self):
        print self._db['orders'].keys()
        return self._db['orders']

    def addProduct(self, product):
        self._db['products'].append(product)
    
    def deleteProduct(self,product):
        index = self._db['products'].index(product)
        
        if index >=0:
            del self._db['products'][index]
            self._db.sync()
        else:
            return
    

    def allProducts(self):
        return self._db['products']



# Kontroler, przekierowanie
class Router(object):
    def __init__(self):
        self._paths = {}

    def route(self, environ, start_response):
        path = environ['PATH_INFO']
        query_dict = parse_qs(environ['QUERY_STRING'])

        if path in self._paths:
            res = self._paths[path](query_dict)
        else:
            res = self.default_response(query_dict)

        return res

    def register(self, path, callback):
        self._paths[path] = callback

    def default_response(self, *args):
        return 404, "Taki plik nie istnieje"


class TextController(object):
    @staticmethod
    def index(query_dict):

        orders = model.allOrders()
        users = model.allUsers()
        products = model.allProducts()
        
        context = {
            'users'    : users,
            'orders'   : orders,
            'products' : products
        }

        return 200, view_text.render(context)

    @staticmethod
    def addOrder(query_dict):
        key = query_dict.get('k', [''])[0]
        value = query_dict.get('v', [''])[0]
        quantity = query_dict.get('q', [''])[0]
        id = randint(0,1000)
        model.setOrder(key, value, quantity, id)
        context = {'url': "/text"}
        return 200, view_redirect.render(context)
    
    @staticmethod
    def addProduct(query_dict):
        product = query_dict.get('product', [''])[0]
        model.addProduct(product)
        context = {'url': "/text"}
        return 200, view_redirect.render(context)
    
    @staticmethod
    def addClient(query_dict):
        key = query_dict.get('k', [''])[0]
        model.setUser(key)
        context = {'url': "/text"}
        return 200, view_redirect.render(context)
    
    @staticmethod
    def deleteClient(query_dict):
        key = query_dict.get('k', [''])[0]
        model.deleteUser(key)
        context = {'url': "/text"}
        return 200, view_redirect.render(context)
    
    @staticmethod
    def deleteOrder(query_dict):
        id = query_dict.get('id', [''])[0]
        owner = query_dict.get('owner', [''])[0]
        model.deleteOrder(owner,id)
        context = {'url': "/text"}
        return 200, view_redirect.render(context)

    @staticmethod
    def deleteProduct(query_dict):
        product = query_dict.get('product', [''])[0]
        model.deleteProduct(product)
        context = {'url': "/text"}
        return 200, view_redirect.render(context)



# Widok
class TextView(object):
    
    @staticmethod
    def remove_diacritic(input):
        return unicodedata.normalize('NFKD', input).encode('ASCII', 'ignore')
    
    @staticmethod
    def render(context):
        output = []
        
        for x in context['users']:
            output.append('<li>{0}</li>'.format(x))
            for y in context['orders']:
                output.append('<ul>')
                print y, context['orders'][y]
                if x == y:
                    for z in context['orders'][y]:
                        output.append('<li>{0}, ilosc {1}</li>'.format(z,context['orders'][y][z]))
                output.append('</ul>')
    
        context['users'] = [
                               '<option>{0}</option>'.format(x) for x in context['users']
                               ]
        context['users_list'] = '\n'.join(context['users'])
    
    
        context['users'] = '\n'.join(output)
        
        context['products'] = [
                             '<option>{0}</option>'.format(x) for x in context['products']
                             ]
        context['products'] = '\n'.join(context['products'])
        

        t = """
        <b>Dodawanie uzytkownika</b>
        <form method="GET" action="/text/addClient" >
            <input type=text name=k placeholder="Tutaj wpisz nazwe" />
            <input type=submit value="dodaj uzytkownika" />
        </form>
        
        <b>Usuwanie uzytkownika</b>
        <form method="GET" action="/text/deleteClient">
        <select name=k>{users_list}</select>
        <input type=submit value="usun uzytkownika" />
        </form>
        
        <b>Dodawanie zamowienia</b>
        <form method="GET" action="/text/addOrder" >
        <select name=k>{products}</select>
        <select name=v>{users_list}</select>
        <input type=text name=q placeholder="Ilosc"/>
        <input type=submit value="dodaj lub edytuj zamowienie"/>
        </form>
        
        <b>Usuwanie zamowienia</b>
        <form method="GET" action="/text/deleteOrder" >
        <select name=id>{products}</select>
        <select name=owner>{users_list}</select>
        <input type=submit value="usun zamowienie" />
        </form>
        
        <b>Dodawanie produktow</b>
        <form method="GET" action="/text/addProduct" >
        <input type=text name=product placeholder="Nazwa towaru"/>
        <input type=submit value="dodaj produkt" />
        </form>
        
        <b>Usuwanie produktow</b>
        <form method="GET" action="/text/deleteProduct" >
        <select name=product>{products}</select>
        <input type=submit value="usun produkt" />
        </form>
        
        <b>Lista produktow</b>
        <select>{products}</select>
        
        <br />
        
        <b>Lista zamowien i uzytkownikow</b>
        <ul>{users}<ul>

        """
        return t.format(**context)


class RedirectView(object):
    @staticmethod
    def render(context):
        return '<meta http-equiv="refresh" content="0; url={url}" />' \
            .format(**context)

# Main
rout = Router()
model = TextModel()
view_text = TextView()
view_redirect = RedirectView()
controller = TextController()

rout.register('/', lambda x: (200, "Wszystko dziala w porzadku."))
rout.register('/text', controller.index)
rout.register('/text/addOrder', controller.addOrder)
rout.register('/text/deleteOrder', controller.deleteOrder)
rout.register('/text/addClient', controller.addClient)
rout.register('/text/deleteClient', controller.deleteClient)
rout.register('/text/addProduct', controller.addProduct)
rout.register('/text/deleteProduct', controller.deleteProduct)


# WSGI
def application(environ, start_response):
    http_status_code, response_body = rout.route(environ, start_response)
    #response_body += '<br><br> The request ENV: {0}'.format(repr(environ))
    http_status_code_and_msg = http_status(http_status_code)
    response_headers = [('Content-Type', 'text/html')]

    start_response(http_status_code_and_msg, response_headers)
    return [response_body]  # it could be any iterable.
