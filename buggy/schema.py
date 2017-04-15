from django.contrib.auth import get_user_model

from graphene import relay, ObjectType, AbstractType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from .models import Bug


User = get_user_model()


class UserNode(DjangoObjectType):
    class Meta:
        model = User
        only_fields = (
            'id',
            'name',
        )
        interfaces = (
            relay.Node,
        )


class BugNode(DjangoObjectType):
    class Meta:
        model = Bug
        only_fields = (
            'created_at',
            'modified_at',
            'title',
            'state',
            'priority',
            'assigned_to',
            'created_by',
        )
        filter_fields = {
            'title': ['icontains'],
            'state': ['exact'],
            'project__name': ['icontains'],
        }
        interfaces = (
            relay.Node,
        )


class Query(AbstractType):
    bug = relay.Node.Field(BugNode)
    all_bugs = DjangoFilterConnectionField(BugNode)

    user = relay.Node.Field(UserNode)
    all_users = DjangoFilterConnectionField(UserNode)
