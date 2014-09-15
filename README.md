django-rest-hal
===============

HAL Implementation for Django REST Framework

Includes:

* HAL Implemenentation without 'curies'
* Defining fields through url-parameter 'fields'


## Setup ##

Include the following settings in your django settings.py
	
	'DEFAULT_MODEL_SERIALIZER_CLASS': 'django_rest_hal.serializers.HalModelSerializer',
    'DEFAULT_PAGINATION_SERIALIZER_CLASS': 'django_rest_hal.serializers.HalPaginationSerializer',
    'DEFAULT_PARSER_CLASSES': ('django_rest_hal.parsers.JsonHalParser',),
    'DEFAULT_RENDERER_CLASSES': (
        'django_rest_hal.renderers.JsonHalRenderer'
    )
    
## Usage ##

Performing REST-Requests results in following HTTP-Responses:

	GET http://localhost/api/resources/1/ HTTP/1.1
	Content-Type  application/hal+json	

	{
    	"_links": {
        	"self": "http://localhost/api/resources/1/",
			"relatedResource": "http://localhost/api/related-resources/1/"
    	},
    	"id": 1,
    	"_embedded": {
        	"subResource": {
            	"_links": {
                	"self": "http://localhost/resources/1/sub-resources/26/"
                	"subSubResource": "http://localhost/resources/1/sub-resources/26/sub-sub-resources/3"
            	},
            	"id": 26,
            	"name": "Sub Resource 26"
        	}
    	}
	}
	
Field customization can be declared using the URL-Query-Parameter 'fields':

	GET http://localhost/api/resources/1/?fields=id,subResource.fields(name,subSubResource.fields(id) HTTP/1.1
	Content-Type  application/hal+json	

	{
    	"_links": {
        	"self": "http://localhost/api/resources/1/",
    	},
    	"id": 1,
    	"_embedded": {
        	"subResource": {
            	"_links": {
                	"self": "http://localhost/resources/1/sub-resources/26/"
                	
            	},
            	"name": "Sub Resource 26"
            	"_embedded": {
            		"subSubResource": {
            			"_links": {
            				"self": "http://localhost/resources/1/sub-resources/26/sub-sub-resources/3"
            			}
            			"id": 3
            		}
            		
            	}
        	}
    	}
	}