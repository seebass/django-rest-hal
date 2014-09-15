from rest_framework.parsers import JSONParser
from django_rest_hal.renderers import JsonHalRenderer


class JsonHalParser(JSONParser):
    media_type = "application/hal+json"
    renderer_class = JsonHalRenderer
