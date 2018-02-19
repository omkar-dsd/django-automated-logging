"""
This file contains the custom database based django ORM handler. This is just a bit hacky.
Some might even say this is just sorcery and magic.

Hopefully it is not.
"""
from logging import Handler


class DatabaseHandler(Handler):

    """Handler for logging into any database"""

    def __init__(self):
        super(DatabaseHandler, self).__init__()

    def emit(self, record):
        # add to database
        # try - except -> preventing circular import
        # http://stackoverflow.com/questions/4379042/django-circular-model-import-issue

        try:
            from .models import Model, Application, ModelObject
            from django.contrib.contenttypes.models import ContentType

            if not hasattr(record, 'action'):
                from .settings import AUTOMATED_LOGGING

                signal = True
                for excluded in AUTOMATED_LOGGING['exclude']:
                    if record.module.startswith(excluded):
                        signal = False
                        break

                if 'unspecified' not in AUTOMATED_LOGGING['modules']:
                    signal = False

                if signal:
                    from .models import Unspecified

                    entry = Unspecified()

                    if hasattr(record, 'message'):
                        entry.message = record.message

                    entry.level = record.levelno
                    entry.file = record.pathname
                    entry.line = record.lineno

                    entry.save()

                return

            if record.action == 'model':
                if 'al_evt' in record.data['instance'].__dict__.keys():
                    entry = record.data['instance'].al_evt
                else:
                    entry = Model()
                    entry.user = record.data['user']
                    entry.application = Application.objects.get_or_create(name=record.data['instance']._meta.app_label)[0]

                    entry.message = record.message

                    if record.data['status'] == 'add':
                        status = 1
                    elif record.data['status'] == 'change':
                        status = 2
                    elif record.data['status'] == 'delete':
                        status = 3
                    else:
                        status = 0

                    entry.action = status
                    entry.information = ModelObject()
                    entry.information.value = repr(record.data['instance'])
                    ct = ContentType.objects.get_for_model(record.data['instance'])

                    try:
                        # check if the ContentType actually exists.
                        ContentType.objects.get(pk=ct.pk)
                        ct_exists = True
                    except ContentType.DoesNotExist:
                        ct_exists = False

                    if ct_exists:
                        entry.information.type = ct

                    entry.information.save()

                    record.data['instance'].al_evt = entry

                if record.data['status'] == 'modified' and 'al_chl' in record.data['instance'].__dict__.keys():
                    entry.modification = record.data['instance'].al_chl

                entry.save()

            elif record.action == 'request':
                from .models import Request

                entry = Request()
                entry.application = record.data['application']
                entry.uri = record.data['uri']
                entry.user = record.data['user']
                entry.method = record.data['method']
                entry.save()

        except Exception as e:
            print(e)
