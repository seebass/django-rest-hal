from rest_framework.renderers import UnicodeJSONRenderer


class JsonHalRenderer(UnicodeJSONRenderer):
    media_type = "application/hal+json"
