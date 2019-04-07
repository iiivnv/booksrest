

import anapioficeandfire
import sqlite3
import json

def get_external_data(name):
    """Get book name from external storage"""
    api = anapioficeandfire.API()
    result = []
    i = 0
    run = True
    while run:
        books = api.get_books(page=i)
        run = (len(books) > 0)
        for book in books:
            if not name:
                result.append(make_output_book(book))
            elif book.name == name:
                result.append(make_output_book(book))
                run = False
                break
        i += 1
    return result

def make_output_book(orig_book):
    return {
            "name": orig_book.name,
            "isbn": orig_book.isbn,
            "authors": orig_book.authors,
            "number_of_pages": orig_book.numberOfPages,
            "publisher": orig_book.publisher,
            "country": orig_book.country,
            "release_date": orig_book.released
        }

def make_book_from_input(data):
    obj = None
    try:
        obj = json.loads(data)
    except:
        try:
            obj = eval(data)
        except:
            raise
    return obj
    
def _store_book(conn, curs, book, id=None):
    if id is not None:  # update
        sql = """UPDATE books SET """
        lst = []
        for key, value in book.items():
            if key == 'authors':
                continue
            if str(value).isdigit():
                lst.append("%(key)s=%(value)s" % {'key': key, 'value': value})
            else:
                lst.append("%(key)s='%(value)s'" % {'key': key, 'value': value})
        if len(lst) == 0: # it means that nothing to update except 'authors'
            return id
        sql += ','.join(lst) + (' WHERE id=%d' % int(id))
    else:
        sql = """INSERT INTO books(name, isbn, number_of_pages, publisher, country, release_date)
            VALUES('%(name)s', '%(isbn)s', %(number_of_pages)s, '%(publisher)s', '%(country)s', '%(release_date)s')""" % book
    try:
        curs.execute(sql)
    except Exception as e:
        raise
    else:
        return curs.lastrowid

def _store_author(conn, curs, author):
    sql = """INSERT INTO authors(id_book, name)
            VALUES(%(id_book)s, '%(name)s')""" % author
    try:
        curs.execute(sql)
    except Exception as e:
        raise
    else:
        return curs.lastrowid

def create_book(conn, book):    
    with conn:
        cursor = conn.cursor()
        id_book = _store_book(conn, cursor, book)
        for name in book['authors']:
            _store_author(conn, cursor, {'id_book': id_book, 'name': name})
        return id_book

def update_book(conn, id, book):
    with conn:
        cursor = conn.cursor()
        id_book = _store_book(conn, cursor, book, id)
        return id_book

def delete_book(conn, id):
    with conn:
        cursor = conn.cursor()
        sql_authors = 'DELETE FROM authors WHERE id_book=?'
        sql_books = 'DELETE FROM books WHERE id=?'
        cursor.execute(sql_authors, (id,))
        cursor.execute(sql_books, (id,))
        return id

def get_books(conn, id=None):
    sql = '''SELECT books.id, books.name, books.isbn, books.number_of_pages, books.publisher, 
            books.country, books.release_date, GROUP_CONCAT(authors.name) as authors 
        FROM books INNER JOIN authors ON books.id=authors.id_book'''
    if id is not None and int(id) > 0:
        sql += ' WHERE books.id=%d' % int(id)
    sql += ' GROUP BY books.id;'
    
    curs = conn.cursor()
    try:
        curs.execute(sql)
    except Exception as e:
        print(e)
        return None

    res = []
    rows = curs.fetchall()
    for row in rows:
        # if there are no raws it returns 1 row with None values for each key 
        if row['id']:
            row_dict = {k: row[k] for k in row.keys()}
            row_dict['authors'] = row_dict['authors'].split(',')
            res.append(row_dict)
    return res
    

def db_connect(dbname):
    try:
        conn = sqlite3.connect(dbname)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(e)
    return None

def check_db_schema(conn):

    sql_books = """CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        isbn VARCHAR(128) NOT NULL,
        number_of_pages INTEGER NOT NULL,
        publisher VARCHAR(255),
        country VARCHAR(64) NOT NULL,
        release_date DATETIME not null
    );"""
    sql_authors = """CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY,
        id_book INTEGER,
        name VARCHAR(255) NOT NULL
    );"""
    sql_tables = [sql_books, sql_authors]
    with conn:
        for sql in sql_tables:
            curs = conn.cursor()
            curs.execute(sql)
    return True
