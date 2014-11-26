import copy
from rest_framework.compat import get_concrete_model
from rest_framework.fields import Field
from rest_framework.pagination import BasePaginationSerializer, NextPageField, PreviousPageField
from rest_framework.relations import RelatedField, HyperlinkedIdentityField
from rest_framework.serializers import Serializer, HyperlinkedModelSerializer, \
    HyperlinkedModelSerializerOptions, ModelSerializer


class NestedHalSerializerMixin():
    def __init__(self, parentMeta, *args, **kwargs):
        self._parentMeta = parentMeta
        super(NestedHalSerializerMixin, self).__init__(*args, **kwargs)

    def _options_class(self, meta):
        return self.getOptions(meta)

    def getOptions(self, meta):
        options = HyperlinkedModelSerializerOptions(self._parentMeta)
        options.nestedFields = getattr(self._parentMeta, 'nested_fields', dict())
        return options


class NestedHalLinksSerializer(NestedHalSerializerMixin, HyperlinkedModelSerializer):
    def getOptions(self, meta):
        options = super(NestedHalLinksSerializer, self).getOptions(meta)
        if options.depth > 0:
            options.fields = ('self',)
        return options

    def get_default_fields(self):
        fields = super(NestedHalLinksSerializer, self).get_default_fields()
        resultingFields = {key: field for key, field in fields.items() if
                           (isinstance(field, RelatedField) and key not in self.opts.nestedFields)
                           or isinstance(field, HyperlinkedIdentityField)}
        self.opts.fields = [field for field in self.opts.fields if field in resultingFields.keys()]
        return resultingFields


class NestedHalEmbeddedSerializer(NestedHalSerializerMixin, ModelSerializer):
    _model_serializer_class = None  # we cannot set a default because it's a circular dependency

    def getOptions(self, meta):
        options = super(NestedHalEmbeddedSerializer, self).getOptions(meta)
        if options.nestedFields:
            options.depth = 1
        return options

    def get_default_fields(self):
        fields = super(NestedHalEmbeddedSerializer, self).get_default_fields()
        resultingFields = {key: field for key, field in fields.items() if isinstance(field, Serializer)}
        self.opts.fields = [field for field in self.opts.fields if field in resultingFields.keys()]
        return resultingFields

    def get_nested_field(self, model_field, related_model, to_many):
        class NestedModelSerializer(self._model_serializer_class):
            class Meta:
                model = related_model
                depth = self.opts.depth - 1

        if not self.opts.nestedFields:
            return NestedModelSerializer(many=to_many)

        fieldName = None
        if model_field:
            fieldName = model_field.name
        else:  # else means it is a reverse relationship so the accessor_name must be retrieved
            cls = self.opts.model
            opts = get_concrete_model(cls)._meta
            reverse_rels = opts.get_all_related_objects()
            reverse_rels += opts.get_all_related_many_to_many_objects()
            for relation in reverse_rels:
                if relation.model == related_model:
                    fieldName = relation.get_accessor_name()

        customFields = self.opts.nestedFields.get(fieldName)
        if customFields is not None:
            class CustomFieldSerializer(self._model_serializer_class):
                class Meta:
                    model = related_model
                    fields = ['self'] + customFields[0] + list(customFields[1].keys())
                    nested_fields = customFields[1]
                    exclude = None

            return CustomFieldSerializer(many=to_many)
        return self.get_related_field(model_field, related_model, to_many)


class HalModelSerializerOptions(HyperlinkedModelSerializerOptions):
    def __init__(self, meta):
        super(HalModelSerializerOptions, self).__init__(None)
        self.exclude = getattr(meta, 'exclude', ())
        self.model = getattr(meta, 'model', None)
        self.nestedFields = getattr(meta, 'nested_fields', None)
        self.read_only_fields = getattr(meta, 'read_only_fields', ())
        self.write_only_fields = getattr(meta, 'write_only_fields', ())
        self.fields = getattr(meta, 'fields', ())


class HalModelSerializer(ModelSerializer):
    _options_class = HalModelSerializerOptions
    _nested_links_serializer_class = NestedHalLinksSerializer
    _nested_embedded_serializer_class = NestedHalEmbeddedSerializer

    def __init__(self, instance=None, data=None, files=None, context=None, partial=False, many=False,
                 allow_add_remove=False, **kwargs):
        self._nested_embedded_serializer_class._model_serializer_class = self.__class__
        if data and '_links' not in data:
            data['_links'] = {}  # put links in data, so that field validation does not fail
        super(HalModelSerializer, self).__init__(instance, data, files, context, partial, many, allow_add_remove, **kwargs)

    def get_fields(self):
        fields = self._dict_class()

        nested = bool(getattr(self.Meta, 'depth', 0))
        if self.init_data:  # if init_data is set, a post/put request is handled and nested fields are ignored
            setattr(self.Meta, 'nestedFields', {})
            self.opts.nestedFields = {}

        declared_fields = self.__get_declared_fields()
        setattr(self.Meta, 'fields', declared_fields)

        fields['_links'] = self._nested_links_serializer_class(self.Meta, source="*")

        self.__add_fields_if_absent(fields, copy.deepcopy(self.base_fields), declared_fields)
        self.__add_fields_if_absent(fields, self.get_default_fields(), declared_fields)

        if nested or self.opts.nestedFields:
            fields['_embedded'] = self._nested_embedded_serializer_class(self.Meta, source="*")

        for key, field in fields.items():
            field.initialize(parent=self, field_name=key)

        return fields

    # def get_default_fields(self):
    #     fields = self._dict_class()
    #     nested = bool(getattr(self.Meta, 'depth', 0))
    #     if self.init_data:  # if init_data is set, a post/put request is handled and nested fields are ignored
    #         setattr(self.Meta, 'nestedFields', {})
    #         self.opts.nestedFields = {}
    #
    #     declaredFields = list(getattr(self.Meta, 'fields', []))
    #     if declaredFields:
    #         if 'self' not in declaredFields:
    #             declaredFields.insert(0, 'self')
    #         if 'id' not in declaredFields:
    #             declaredFields.insert(0, 'id')
    #         setattr(self.Meta, 'fields', declaredFields)
    #     fields['_links'] = self._nested_links_serializer_class(self.Meta, source="*")
    #
    #     defaultFields = super(HalModelSerializer, self).get_default_fields()
    #     fields.update({key: field for key, field in defaultFields.items() if not isinstance(field, RelatedField)
    #                    and not isinstance(field, HyperlinkedIdentityField) and not isinstance(field, Serializer)
    #                    and not (declaredFields and key not in declaredFields)})
    #     if nested or self.opts.nestedFields:
    #         fields['_embedded'] = self._nested_embedded_serializer_class(self.Meta, source="*")
    #     self.opts.fields = [key for key in fields.keys()]
    #     return fields

    def get_pk_field(self, model_field):
        # always include id even it is not set in serializer fields definition
        return self.get_field(model_field)

    def __handle_excludes(self, fields):
        if self.opts.exclude:
            assert isinstance(self.opts.exclude, (list, tuple)), '`exclude` must be a list or tuple'
            for key in self.opts.exclude:
                fields.pop(key, None)

    def __get_declared_fields(self):
        declared_fields = list(getattr(self.Meta, 'fields', []))
        if declared_fields:
            if 'self' not in declared_fields:
                declared_fields.insert(0, 'self')
            if 'id' not in declared_fields:
                declared_fields.insert(0, 'id')
        return declared_fields

    @staticmethod
    def __add_fields_if_absent(fields, add_fields, declared_fields):
        fields.update({key: field for key, field in add_fields.items() if not isinstance(field, RelatedField)
                       and not isinstance(field, HyperlinkedIdentityField) and not isinstance(field, Serializer)
                       and not (declared_fields and key not in declared_fields) and not key in fields})


class HalPaginationSerializer(BasePaginationSerializer):
    count = Field(source='paginator.count')
    page_size = Field(source='paginator.per_page')
    results_field = '_embedded'

    def __init__(self, *args, **kwargs):
        super(HalPaginationSerializer, self).__init__(*args, **kwargs)

        class NestedLinksSerializer(Serializer):
            class NestedSelfLinkField(Field):
                def to_native(self, value):
                    request = self.context.get('request')
                    return request and request.build_absolute_uri() or ''

            self = NestedSelfLinkField(source='*')
            next = NextPageField(source='*')
            previous = PreviousPageField(source='*')

        oldFields = self.fields
        self.fields = self._dict_class()
        self.fields['_links'] = NestedLinksSerializer(source="*")
        self.fields.update(oldFields)
