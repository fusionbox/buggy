from django.conf import settings

import graphene
from graphene_django.debug import DjangoDebug

import buggy.schema


class Query(buggy.schema.Query, graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    if settings.DEBUG:
        debug = graphene.Field(DjangoDebug, name='__debug')

schema = graphene.Schema(query=Query)
