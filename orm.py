from peewee import *
from properties import DEFAULT
import logging


logger = logging.getLogger(__name__)


database = SqliteDatabase('data/data.db')


class _Model(Model):
    class Meta:
        database = database


class _DiscordModel(_Model):
    @classmethod
    def from_discord_model(cls, discord_model):
        model, created = cls.get_or_create(id=discord_model.id)

        if created:
            logger.debug(f"'{cls.__name__}' ({model.id}) added to database")

        return model


class Guild(_DiscordModel):
    id = IntegerField(unique=True)
    prefix = CharField(default=DEFAULT['prefix'])


class User(_DiscordModel):
    id = IntegerField(unique=True)


class Vote(_Model):
    id = IntegerField(unique=True, primary_key=True)

    guild = ForeignKeyField(Guild, backref='votes')
    author = ForeignKeyField(User, backref='votes')

    title = TextField(null=True)
