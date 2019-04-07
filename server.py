
import BaseHTTPServer
import SimpleHTTPServer
import urllib
import json
import re

import model

# List of supported operations:
#     GET http://localhost:8080/api/external-books?name=:nameOfABook
#     Create: POST http://localhost:8080/api/v1/books                with data in request body
#     Read: GET http://localhost:8080/api/v1/books
#     Update: PATCH http://localhost:8080/api/v1/books/:id           with data in request body
#     Update: POST http://localhost:8080/api/v1/books/:id/update     with data in request body
#     Delete: DELETE http://localhost:8080/api/v1/books/:id
#     Delete: POST http://localhost:8080/api/v1/books/:id/delete
#     Show:   GET http://localhost:8080/api/v1/books/:id


# Kinds of HTTP queries after regexp parsed, see method check_url()
GETEXTERNAL = 1     # get data from external source
POSTCREATE_GETALL = 2   # POST query without ID, GET query without ID
POSTUPDATE = 4
POSTDELETE = 5
PATCH_DELETE_GET = 6   # queries with ID in URL: POST query for update , POST query for DELETE, GET query of one book  

DBNAME = 'adevatest.db'

class RequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler, object):
    def __init__(self, *args, **kwargs):
        super(RequestHandler, self).__init__(*args, **kwargs)

    def do_POST(self):
        url_data = self.check_url()
        if not url_data:
            self.send_status(404)
            return
        
        if url_data['command'] not in (POSTCREATE_GETALL, POSTUPDATE, POSTDELETE):
            self.send_status(400)
            return
        
        length = self.headers.getheader('content-length')
        nbytes = int(length)
        data = self.rfile.read(nbytes)

        conn = model.db_connect(DBNAME)
        
        if url_data['command'] == POSTCREATE_GETALL:    # create
            self._create(conn, data)
        elif url_data['command'] == POSTUPDATE:         # update
            id = int(url_data['data'])
            self._update(conn, id, data)
        else:                                           # POSTDELETE - delete
            id = int(url_data['data'])                  # the ID obtained from URL
            self._delete(conn, id)
            
    def do_GET(self):
        """GETEXTERNAL, PATCH_DELETE_GET allowed"""
        url_data = self.check_url()
        if not url_data:
            self.send_status(404)
            return
        
        # allowed 3 kind of operations for GET request: get from external source, get of one row by ID, get all rows
        if url_data['command'] not in (GETEXTERNAL, PATCH_DELETE_GET, POSTCREATE_GETALL):
            self.send_status(400)
            return
                
        if url_data['command'] == GETEXTERNAL:
            result = model.get_external_data(url_data['data'])
            self.send_status(200)
            self.send_result(200, result)
        elif url_data['command'] == PATCH_DELETE_GET:
            # get data from database and url_data['data'] will be an id in our database
            conn = model.db_connect(DBNAME)
            
            id = int(url_data['data'])
            self._get_books(conn, id)
        else: # POSTCREATE_GETALL case, here it will return all records from DB
            conn = model.db_connect(DBNAME)
            
            self._get_books(conn)
            
    def do_PATCH(self):
        url_data = self.check_url()
        if not url_data:
            self.send_status(404)
            return

        if url_data['command'] != PATCH_DELETE_GET:
            self.send_status(400)
            return

        length = self.headers.getheader('content-length')
        nbytes = int(length)
        data = self.rfile.read(nbytes)
            
        conn = model.db_connect(DBNAME)

        id = int(url_data['data'])
        self._update(conn, id, data)

    def do_DELETE(self):
        url_data = self.check_url()
        if not url_data:
            self.send_status(404)
            return
        if url_data['command'] != PATCH_DELETE_GET:
            self.send_status(400)
            return
        conn = model.db_connect(DBNAME)
        id = int(url_data['data'])                  # the ID obtained from URL
        self._delete(conn, id)
    
    def _create(self, conn, data):
        obj = model.make_book_from_input(data)
        if not obj:
            self.send_status(400)
            return

        id = model.create_book(conn, obj)
        if id:
            obj = model.get_books(conn, int(id))
            self.send_status(200)
            self.send_result(200, obj)
        else:
            self.send_status(500)

    def _update(self, conn, id, data):
        obj = model.make_book_from_input(data)
        if not obj:
            self.send_status(400)
            return
        if obj:                     # the data obtained from the HTTP body, see above
            id = model.update_book(conn, id, obj)
            if id:                                      # updated successfully
                obj = model.get_books(conn, int(id))    # get updated data for response
            self.send_status(200)
            self.send_result(200, obj)
        else:
            self.send_status(500)

    def _delete(self, conn, id):
            obj = model.get_books(conn, int(id))        # got book before deleting to know its name for the message (requirement)
            if obj:
                id = model.delete_book(conn, id)
                self.send_status(200)
                self.send_result(204, obj[0]['name'])
            else:
                self.send_status(500)

    def _get_books(self, conn, id=None):
            result = model.get_books(conn, id)
            if result is not None:
                self.send_status(200)
                self.send_result(200, result)
            else:
                self.send_status(500)

    def check_url(self):
        regex_templ = {r'\/api\/external-books[?]name=(.*)': GETEXTERNAL,   # GET from external
                       r'\/api\/v1\/books[\/]?$': POSTCREATE_GETALL,        # POST for create new, GET all (without id in URL)
                       r'\/api\/v1\/books\/([\d]+)[\/]?$': PATCH_DELETE_GET,      # PATCH, DELETE, GET with id
                       r'\/api\/v1\/books\/([\d]+)\/update[\/]?$': POSTUPDATE,     # POST request with id
                       r'\/api\/v1\/books\/([\d]+)\/delete[\/]?$': POSTDELETE}     # POST request with id
        for pattern, cmd in regex_templ.items():
            match = re.search(pattern, self.path)
            if match:
                return {'data': urllib.unquote(match.group(1) if match.groups() else '').strip('"\''), 'command': cmd}
        return dict()

    def send_status(self, code=200, msg=None):
        self.send_response(code, msg)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def send_result(self, code, result):
        if code == 204:
            self.wfile.write(json.dumps({"status_code": code, "status": "success", 
                                         "message": "The book %s was deleted successfully" % result, 
                                         "data": []}))
        else:
            self.wfile.write(json.dumps({"status_code": code, "status": "success", "data": result}))


def main():
    import argparse

    parser = argparse.ArgumentParser(description="""This is a Server that emulates behavior of the real Catalog Server.""")
    parser.add_argument('--host', action='store', dest='host', default='localhost',
                                    help='''Network address which the server should listen to. Default: localhost''')
    parser.add_argument('--port', action='store', dest='port', default=8080, type=int,
                                    help='''Network port which the server should listen to. Default: 8080''')

    args = vars(parser.parse_args())

    server = BaseHTTPServer.HTTPServer
    handler = RequestHandler
    server_address = (args['host'], args['port'])
    print('INFO. Server is listening to %(host)s:%(port)s.' % args)

    conn = model.db_connect(DBNAME)
    if model.check_db_schema(conn):
        print('DB exists and tables created.')
    conn.close()

    srv = server(server_address, handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    srv.server_close()


if __name__ == "__main__":

    main()