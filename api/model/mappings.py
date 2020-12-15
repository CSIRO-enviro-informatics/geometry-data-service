import json
import sys
from importlib_resources import files

class DatasetMappings:
   DATASET_RESOURCE_BASE_URI_LOOKUP = {}

   def __init__(self):
      dict_lookup = {}
      jsonfile = files('model').joinpath('default_mappings.json').read_text()
      dict_lookup = json.loads(jsonfile)  
      self.DATASET_RESOURCE_BASE_URI_LOOKUP = dict_lookup

   def find_resource_uri(self, dataset_type, dataset_local_id):
        prefix = self.DATASET_RESOURCE_BASE_URI_LOOKUP.get(dataset_type)
        if prefix is None:
            return None
        return "{0}/{1}".format(prefix, dataset_local_id)

   def get_prefix(self, dataset_type):
        return self.DATASET_RESOURCE_BASE_URI_LOOKUP.get(dataset_type)

