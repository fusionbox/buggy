from django.contrib.auth import get_user_model

import graphene
from graphene import relay, AbstractType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from . import verhoeff
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
            'number',
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

    number = graphene.String()


class Query(AbstractType):
    bug = graphene.Field(BugNode, number=graphene.String())
    all_bugs = DjangoFilterConnectionField(BugNode)

    user = relay.Node.Field(UserNode)
    all_users = DjangoFilterConnectionField(UserNode)

    def resolve_bug(self, args, context, info):
        bug_number = args.get('number', None)
        if bug_number is None:
            return
        if not verhoeff.validate_verhoeff(bug_number):
            return
        bug_pk = bug_number[:-1]
        return Bug.objects.get(pk=bug_pk)
