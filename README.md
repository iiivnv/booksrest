# booksrest
REST server for getting/creating/updating some data via HTTP

# How to run the Server
In the current directory run command and verify two messages below:
>$ python server.py
INFO. Server is listening to localhost:8080.
DB exists and tables created.

This command will run server on localhost:8080
The SQLite database file adevatest.db will be created in the current folder.

This Server uses standard SimpleHTTPServer which is part of Python 2.7 so it is not needed to install any other Python packages except one which is part of requirements. Thi
s package is anapioficeandfire-python. To install it to Python 2.7 use:
> sudo pip2 anapioficeandfire

For testing use queries from task description.

List of supported commands in accordance with sections in task description:
* Get books from external storage: GET http://localhost:8080/api/external-books?name=:nameOfABook
* Create: POST http://localhost:8080/api/v1/books                with data in request body
* Read: GET http://localhost:8080/api/v1/books
* Update: PATCH http://localhost:8080/api/v1/books/:id           with data in request body
* Update: POST http://localhost:8080/api/v1/books/:id/update     with data in request body
* Delete: DELETE http://localhost:8080/api/v1/books/:id
* Delete: POST http://localhost:8080/api/v1/books/:id/delete
* Show:   GET http://localhost:8080/api/v1/books/:id
Where values like :id or :nameOfABook are placeholders for real id and name of book accordingly.
The first command may be run with empty name of book (name=) and in such case it will return all existing books in the original storage.

