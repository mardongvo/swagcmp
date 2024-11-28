import unittest
from comparator import Swg, Comparator

OLD_EP_SWG = '''
{
  "swagger": "2.0",
  "paths": {
    "/pet": {
      "post": {},
      "get": {}
    },
    "/pet/{id}": {
      "put": {},
      "get": {}
    }
  }
}
'''

NEW_EP_SWG = '''
{
  "swagger": "2.0",
  "paths": {
    "/pet": {
      "post": {}
    },
    "/pet/{id}": {
      "put": {},
      "get": {},
      "delete": {}
    }
  }
}
'''

OLD_PARAM_SWG = '''
{
  "swagger": "2.0",
  "paths": {
    "/pet/{id}": {
      "get": {
        "parameters": [
          {
            "name": "id",
            "in": "path",
            "description": "ID of pet",
            "required": true,
            "type": "integer"
          },
          {
            "name": "name",
            "in": "query",
            "description": "Updated name of the pet",
            "required": false,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "description": "Some data",
            "required": true
          }
        ]
      }
    }
  }
}
'''

NEW_PARAM_SWG = '''
{
  "swagger": "2.0",
  "paths": {
    "/pet/{id}": {
      "get": {
        "parameters": [
          {
            "name": "id",
            "in": "path",
            "description": "Some description",
            "required": false,
            "type": "string"
          },
          {
            "name": "title",
            "in": "query",
            "description": "Updated name of the pet",
            "required": false,
            "type": "string"
          },
          {
            "name": "body",
            "in": "body",
            "description": "Some data",
            "required": true
          }
        ]
      }
    }
  }
}
'''


OLD_BODY_SWG = '''
{
  "swagger": "2.0",
  "paths": {
    "/pet": {
      "post": {
        "parameters": [{
            "name": "body",
            "in": "body",
            "schema": {
              "$ref": "#/definitions/Pet"
            }
          }]
  }}},
  "definitions": {
    "Pet": {
      "type": "object",
      "properties": {
        "code": {
          "type": "integer",
          "format": "int32"
        },
        "type": {
          "type": "string"
        },
        "message": {
          "type": "string"
        }
      }
    }
  }
}
'''

NEW_BODY_SWG = '''
{
  "swagger": "2.0",
  "paths": {
    "/pet": {
      "post": {
        "parameters": [{
            "name": "body",
            "in": "body",
            "schema": {
              "$ref": "#/definitions/Pet"
            }
          }]
  }}},
  "definitions": {
    "Pet": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "format": "int32"
        },
        "type": {
          "type": "string"
        },
        "msg": {
          "type": "string"
        }
      }
    }
  }
}
'''

class TestEndpoints(unittest.TestCase):
    def test_validity(self):
        for e in [OLD_EP_SWG, NEW_EP_SWG, OLD_PARAM_SWG, NEW_PARAM_SWG,
          OLD_BODY_SWG, NEW_BODY_SWG]:
            s = Swg(e)
    def test_added_endpoints(self):
        s1 = Swg(OLD_EP_SWG)
        s2 = Swg(NEW_EP_SWG)
        cmp = Comparator(s1, s2)
        res = cmp.added_endpoints()
        self.assertEqual(len(res), 1, "Too many added")
        self.assertEqual(res[0].path, "/pet/{id}", "Wrong path")
        self.assertEqual(res[0].method, "delete", "Wrong method")
    def test_removed_endpoints(self):
        s1 = Swg(OLD_EP_SWG)
        s2 = Swg(NEW_EP_SWG)
        cmp = Comparator(s1, s2)
        res = cmp.removed_endpoints()
        self.assertEqual(len(res), 1, "Too many removed")
        self.assertEqual(res[0].path, "/pet", "Wrong path")
        self.assertEqual(res[0].method, "get", "Wrong method")
    def test_existing_endpoints(self):
        s1 = Swg(OLD_EP_SWG)
        s2 = Swg(NEW_EP_SWG)
        cmp = Comparator(s1, s2)
        res = cmp.same_endpoints()
        self.assertEqual(len(res), 3, "Too many existing")
    def test_query_params_count(self):
        s1 = Swg(OLD_PARAM_SWG)
        s2 = Swg(NEW_PARAM_SWG)
        cmp = Comparator(s1, s2)
        eps = cmp.same_endpoints()
        for ep in eps:
            self.assertEqual(len(s1.endpoint_query_params(ep)), 2, "Too many params 1")
            self.assertEqual(len(s2.endpoint_query_params(ep)), 2, "Too many params 2")
    def test_added_query_params(self):
        s1 = Swg(OLD_PARAM_SWG)
        s2 = Swg(NEW_PARAM_SWG)
        cmp = Comparator(s1, s2)
        ep = cmp.same_endpoints()[0]
        added = cmp.added_query_parameters(ep)
        self.assertEqual(len(added), 1, "Added query params")
        self.assertEqual(added[0], "title", "Added wrong params")
    def test_removed_query_params(self):
        s1 = Swg(OLD_PARAM_SWG)
        s2 = Swg(NEW_PARAM_SWG)
        cmp = Comparator(s1, s2)
        ep = cmp.same_endpoints()[0]
        removed = cmp.removed_query_parameters(ep)
        self.assertEqual(len(removed), 1, "Added query params")
        self.assertEqual(removed[0], "name", "Added wrong params")
    def test_changed_query_params(self):
        s1 = Swg(OLD_PARAM_SWG)
        s2 = Swg(NEW_PARAM_SWG)
        cmp = Comparator(s1, s2)
        ep = cmp.same_endpoints()[0]
        changes = cmp.changed_query_parameters(ep)
        self.assertEqual(len(changes), 1, "Changes query params")
        ch = changes[0]
        self.assertEqual(ch.name, "id", "Changes query params")
        self.assertEqual(ch.old_type, "integer", "Changes query params")
        self.assertEqual(ch.new_type, "string", "Changes query params")
        self.assertEqual(ch.old_description, "ID of pet", "Changes query params")
        self.assertEqual(ch.new_description, "Some description", "Changes query params")
        self.assertEqual(ch.old_required, "True", "Changes query params")
        self.assertEqual(ch.new_required, "False", "Changes query params")
    def test_request_ref(self):
        s1 = Swg(OLD_BODY_SWG)
        s2 = Swg(NEW_BODY_SWG)
        cmp = Comparator(s1, s2)
        ep = cmp.same_endpoints()[0]
        self.assertEqual(s1.endpoint_request_body_id(ep), "Pet", "Request def")
        self.assertEqual(s2.endpoint_request_body_id(ep), "Pet", "Request def")

if __name__ == '__main__':
    unittest.main()