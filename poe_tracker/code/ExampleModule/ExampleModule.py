
from ..Log import Log
from ..Client import Client


class ExampleModule:


    def __init__(self):
        self.log = Log()
        self.client = Client()
        pass


    async def on_channel_create(self, channel):
        pass


    async def on_channel_delete(self, channel):
        pass


    async def on_channel_update(self, before, after):
        pass


    async def on_error(self, event, *args, **kwargs):
        pass


    async def on_group_join(self, channel, user):
        pass


    async def on_group_remove(self, channel, user):
        pass


    async def on_member_ban(self, member):
        pass


    async def on_member_join(self, member):
        pass


    async def on_member_remove(self, member):
        pass


    async def on_member_unban(self, server, user):
        pass


    async def on_member_update(self, before, after):
        pass


    async def on_message(self, message):
        pass


    async def on_message_delete(self, message):
        pass


    async def on_message_edit(self, before, after):
        pass


    async def on_reaction_add(self, reaction, user):
        pass


    async def on_reaction_clear(self, message, reactions):
        pass


    async def on_reaction_remove(self, reaction, user):
        pass


    async def on_ready(self):
        pass


    async def on_resumed(self, ):
        pass


    async def on_server_available(self, server):
        pass


    async def on_server_emojis_update(self, before, after):
        pass


    async def on_server_join(self, server):
        pass


    async def on_server_remove(self, server):
        pass


    async def on_server_role_create(self, role):
        pass


    async def on_server_role_delete(self, role):
        pass


    async def on_server_role_update(self, before, after):
        pass


    async def on_server_unavailable(self, server):
        pass


    async def on_server_update(self, before, after):
        pass


    async def on_socket_raw_receive(self, msg):
        pass


    async def on_socket_raw_send(self, payload):
        pass


    async def on_typing(self, channel, user, when):
        pass


    async def on_voice_state_update(self, before, after):
        pass
