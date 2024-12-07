#!/usr/bin/env python3
import json
from collections import namedtuple
from dataclasses import dataclass
from typing import Optional,List

Endpoint = namedtuple('Endpoint', ['path', 'method'])
FieldCmpResult = namedtuple('Field', ['name', 'effect']) # effect = + | - | / (add, remove, change)

@dataclass
class ChangedParameter:
    name: str
    old_type: str = ""
    new_type: str = ""
    old_in: str = ""
    new_in: str = ""
    old_description: str = ""
    new_description: str = ""
    old_required: bool = False
    new_required: bool = False
    def has_changes(self):
        return self.old_type != self.new_type or \
            self.old_in != self.new_in or \
            self.old_description != self.new_description or \
            self.old_required != self.new_required

class Swg:
    def __init__(self, content):
        self.tree = json.loads(content)
        self.eps = []
        for pp,v in self.tree["paths"].items():
            for met in v.keys():
                self.eps.append(Endpoint(path=pp,method=met))
    def endpoints(self):
        # return list of pairs (path, method)
        return self.eps
    def definition(self, name):
        return self.tree["definitions"].get(name)
    def endpoint_query_params(self, ep: Endpoint):
        # return list of params excluding body
        obj = self.tree["paths"][ep.path][ep.method]
        result = []
        ps = obj.get("parameters")
        if ps == None: return []
        for p in ps:
            if p["in"].lower() == "body": continue
            result.append(p)
        return result
    def endpoint_request_body_id(self, ep: Endpoint):
        # return definition name
        obj = self.tree["paths"][ep.path][ep.method]
        if "parameters" in obj:
            for p in obj["parameters"]:
                if p["in"] != "body": continue
                return extract_ref(p)
        return ""
    # return definition name
    def endpoint_response_200_id(self, ep):
        obj = self.tree["paths"][ep.path][ep.method]
        if "responses" in obj:
            for k, p in obj["responses"].items():
                if k != "200": continue
                return extract_ref(p)
        return ""

def extract_ref(obj):
    ref = obj.get("$ref")
    if ref != None:
        return ref.replace("#/definitions/", "")
    sch = obj.get("schema")                    
    if sch == None:
        return ""
    ref = sch.get("$ref")
    if ref != None:
        return ref.replace("#/definitions/", "")
    prop = sch.get("additionalProperties")
    if prop == None:
        prop = sch.get("items")
    if prop == None:
        return ""
    ref = prop.get("$ref")
    if ref == None:
        return ""
    return ref.replace("#/definitions/", "")

class Comparator:
    def __init__(self, old, new):
        self.old = old
        self.new = new
    def added_endpoints(self):
        eold = set(self.old.endpoints())
        enew = set(self.new.endpoints())
        result = list(enew - eold)
        result.sort()
        return result
    def removed_endpoints(self):
        eold = set(self.old.endpoints())
        enew = set(self.new.endpoints())
        result = list(eold - enew)
        result.sort()
        return result
    def same_endpoints(self):
        eold = set(self.old.endpoints())
        enew = set(self.new.endpoints())
        result = list(eold & enew)
        result.sort()
        return result
    def removed_query_parameters(self, ep: Endpoint):
        q1 = self.old.endpoint_query_params(ep)
        q2 = self.new.endpoint_query_params(ep)
        result = []
        for o in q1:
            removed = True
            for n in q2:
                if o.get("name") == n.get("name"):
                    removed = False
            if removed:
                result.append(o.get("name"))
        return result
    def added_query_parameters(self, ep: Endpoint):
        q1 = self.old.endpoint_query_params(ep)
        q2 = self.new.endpoint_query_params(ep)
        result = []
        for n in q2:
            added = True
            for o in q1:
                if o.get("name") == n.get("name"):
                    added = False
            if added:
                result.append(n.get("name"))
        return result
    def changed_query_parameters(self, ep: Endpoint):
        q1 = self.old.endpoint_query_params(ep)
        q2 = self.new.endpoint_query_params(ep)
        result = []
        for o in q1:
            for n in q2:
                if o.get("name") != n.get("name"): continue
                chng = ChangedParameter(name=o.get("name"))
                if o.get("type") != n.get("type"):
                    chng.old_type = str(o.get("type"))
                    chng.new_type = str(n.get("type"))
                if o.get("in") != n.get("in"):
                    chng.old_in = str(o.get("in"))
                    chng.new_in = str(n.get("in"))
                if o.get("description") != n.get("description"):
                    chng.old_description = str(o.get("description"))
                    chng.new_description = str(n.get("description"))
                if o.get("required") != n.get("required"):
                    chng.old_required = str(o.get("required"))
                    chng.new_required = str(n.get("required"))
                if chng.has_changes():
                    result.append(chng)
        return result
    def compare_requests(self, ep: Endpoint):
        id1 = self.old.endpoint_request_body_id(ep)
        id2 = self.new.endpoint_request_body_id(ep)
        return self.compare_defs(id1, id2)
    def compare_responses(self, ep: Endpoint):
        id1 = self.old.endpoint_response_200_id(ep)
        id2 = self.new.endpoint_response_200_id(ep)
        return self.compare_defs(id1, id2)
    def compare_defs(self, id1, id2):
        if (id1 == "" and id2 != "") or (id1 != "" and id2 == ""):
            return [FieldCmpResult("Definition", "/")]
        if id1 == "" and id2 == "":
            return []
        def1 = self.old.definition(id1)
        def2 = self.new.definition(id2)
        if def1 == None and def2 == None:
            return []
        if def1 == None or def2 == None:
            return [FieldCmpResult("Definition", "/")]
        return self.compare_dict(def1, def2)
    def compare_dict(self, d1, d2):
        result = []
        comm_keys = list(set(d1.keys()) & set(d2.keys()))
        add_keys = list(set(d2.keys()) - set(comm_keys))
        del_keys = list(set(d1.keys()) - set(comm_keys))
        for k in add_keys:
            result.append(FieldCmpResult(k, "+"))
        for k in del_keys:
            result.append(FieldCmpResult(k, "-"))
        for k in comm_keys:
            f1 = d1.get(k)
            f2 = d2.get(k)
            if f1 != f2 and not (isinstance(f1, dict) and isinstance(f2, dict)):
                result.append(FieldCmpResult(k, "/"))
            if isinstance(f1, dict) and isinstance(f2, dict):
                # 1. compare content
                res = self.compare_dict(f1, f2)
                for e in res:
                    result.append(FieldCmpResult(k+">"+e.name, e.effect))
                # 2. compare references 
                res = self.compare_defs(extract_ref(f1), extract_ref(f2))
                for e in res:
                    result.append(FieldCmpResult(k+">"+e.name, e.effect))
        return result

def report_changes(outfile, oldcnt, newcnt):
    report = open(outfile, "w")
    cmp = Comparator(Swg(oldcnt), Swg(newcnt))
    report.write("Added endpoints\n")
    for e in cmp.added_endpoints():
        report.write("{} {}\n".format(e.method, e.path))
    report.write("\n\n")
    report.write("Removed endpoints\n")
    for e in cmp.removed_endpoints():
        report.write("{} {}\n".format(e.method, e.path))
    report.write("\n\n")
    eps = cmp.same_endpoints()
    report.write("Endpoints changes\n")
    for e in eps:
        added = cmp.added_query_parameters(e)
        removed = cmp.removed_query_parameters(e)
        changes = cmp.changed_query_parameters(e)
        same_req_body = cmp.compare_requests(e)
        same_resp_body = cmp.compare_responses(e)
        if len(added) == 0 and len(removed) == 0 and len(changes) == 0 and \
            len(same_req_body) == 0 and len(same_resp_body) == 0:
            continue
        report.write("{} {}\n".format(e.method, e.path))
        if not(len(added) == 0 and len(removed) == 0 and len(changes) == 0):
            for p in added:
                report.write("  ++{}\n".format(p))
            for p in removed:
                report.write("  --{}\n".format(p))
            for p in changes:
                report.write("  <>{}\n".format(p.name))
        if len(same_req_body) > 0:
            report.write("  request body:\n")
            for f in same_req_body:
                report.write("  {}{}\n".format(f.effect, f.name))
        if len(same_resp_body) > 0:
            report.write("  response body:\n")
            for f in same_resp_body:
                report.write("  {}{}\n".format(f.effect, f.name))
    report.close()