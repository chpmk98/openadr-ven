# A hacky way of getting HTTPStatus into oadr30/vtn.py.

class Object(object):
    pass

HTTPStatus = Object()
# Success
HTTPStatus.OK = 200
HTTPStatus.CREATED = 201

# Client error
HTTPStatus.CONFLICT = 409
