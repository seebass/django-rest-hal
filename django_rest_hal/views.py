import re
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet

from django_rest_hal.serializers import HalModelSerializer


class HalModelViewSet(ModelViewSet):
    __GET_FIELDS_PATTERN = re.compile(r"([a-zA-Z0-9_-]+?)\.fields\((.*?)\)\Z")

    def get_success_headers(self, data):
        linksData = data.get('_links')
        if not linksData:
            return {}
        urlFieldData = linksData.get(api_settings.URL_FIELD_NAME)
        if not urlFieldData:
            return {}
        return {'Location': urlFieldData}

    def get_serializer_class(self):
        serializer_class = self.serializer_class
        if serializer_class is None:
            class DefaultSerializer(self.model_serializer_class):
                class Meta:
                    model = self.model

            serializer_class = DefaultSerializer

        customFieldSerializerClass = self.__getCustomFieldSerializerClass(serializer_class)
        if customFieldSerializerClass:
            return customFieldSerializerClass

        return serializer_class

    def __getCustomFieldSerializerClass(self, baseSerializerClass):
        if not issubclass(baseSerializerClass, HalModelSerializer):
            return None

        request = self.get_serializer_context().get('request')
        if request:
            customFieldsStr = request.QUERY_PARAMS.get('fields')
            if customFieldsStr:
                customFields, customNestedFields = self.__getCustomFields(customFieldsStr)

                class CustomFieldSerializer(baseSerializerClass):
                    class Meta:
                        model = self.model
                        fields = customFields + list(customNestedFields.keys())
                        nested_fields = customNestedFields
                        exclude = None

                return CustomFieldSerializer
        return None

    def __getCustomFields(self, customFieldsStr):
        customNestedFields = dict()
        customFields = []
        splittedCustomFieldStrs = self.__splitCustomFields(customFieldsStr)
        for customFieldStr in splittedCustomFieldStrs:
            subFieldsMatch = self.__GET_FIELDS_PATTERN.search(customFieldStr)
            if subFieldsMatch:
                fieldName = subFieldsMatch.group(1)
                customNestedFields[fieldName] = self.__getCustomFields(subFieldsMatch.group(2))
            else:
                customFields.append(customFieldStr)
        return customFields, customNestedFields

    @staticmethod
    def __splitCustomFields(customFieldsStr):
        parenthesisCounter = 0
        splittedCustomFieldStrs = []
        foundCustomField = ""

        for char in customFieldsStr:
            if char == "(":
                parenthesisCounter += 1
            if char == ")":
                parenthesisCounter -= 1
            if char == "," and parenthesisCounter == 0:
                splittedCustomFieldStrs.append(foundCustomField)
                foundCustomField = ""
                continue
            foundCustomField += char
        splittedCustomFieldStrs.append(foundCustomField)
        return splittedCustomFieldStrs
