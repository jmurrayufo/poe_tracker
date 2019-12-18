
import discord

from ..Log import Log


class Client(discord.Client):

    # No __init__ given, just use the base classes one!

    _shared_state = {}


    def __init__(self, *args, **kwargs):
        self.__dict__ = self._shared_state

        self.log = Log()

        # We only init ONCE
        if not hasattr(self, '_inited'):
            super().__init__(*args, **kwargs)
            self.registry = []
            self._inited = True


    def register(self, cls):
        """Register a class with our client.
        """
        # TODO: Check if this class is here or not!
        self.registry.append(cls)


    async def on_channel_create(self, channel):

        self.log.debug("on_channel_create")
        for module in self.registry:
            if hasattr(module, 'on_channel_create'):
                await module.on_channel_create(channel)


    async def on_channel_delete(self, channel):

        self.log.debug("on_channel_delete")
        for module in self.registry:
            if hasattr(module, 'on_channel_deletechannel'):
                await module.on_channel_deletechannel(channel)



    async def on_channel_update(self, before, after):

        self.log.debug("on_channel_update")
        for module in self.registry:
            if hasattr(module, 'on_channel_update'):
                await module.on_channel_update(before, after)



    async def on_error(self, event, *args, **kwargs):
        self.log.exception("Saw exception")
        for module in self.registry:
            if hasattr(module, 'on_error'):
                await module.on_error(event, *args, **kwargs)



    async def on_group_join(self, channel, user):

        self.log.debug("on_group_join")
        for module in self.registry:
            if hasattr(module, 'on_group_join'):
                await module.on_group_join(channel, user)



    async def on_group_remove(self, channel, user):

        self.log.debug("on_group_remove")
        for module in self.registry:
            if hasattr(module, 'on_group_remove'):
                await module.on_group_remove(channel, user)



    async def on_member_ban(self, member):

        self.log.debug("on_member_ban")
        for module in self.registry:
            if hasattr(module, 'on_member_ban'):
                await module.on_member_ban(member)



    async def on_member_join(self, member):

        self.log.debug("on_member_join")
        for module in self.registry:
            if hasattr(module, 'on_member_join'):
                await module.on_member_join(member)



    async def on_member_remove(self, member):

        self.log.debug("on_member_remove")
        for module in self.registry:
            if hasattr(module, 'on_member_remove'):
                await module.on_member_remove(member)



    async def on_member_unban(self, server, user):

        self.log.debug("on_member_unban")
        for module in self.registry:
            if hasattr(module, 'on_member_unban'):
                await module.on_member_unban(server, user)


    async def on_member_update(self, before, after):

        self.log.debug("on_member_update")
        for module in self.registry:
            if hasattr(module, 'on_member_update'):
                await module.on_member_update(before, after)



    async def on_message(self, message):

        self.log.debug("on_message")
        for module in self.registry:
            if hasattr(module, 'on_message'):
                await module.on_message(message)


    async def on_message_delete(self, message):

        self.log.debug("on_message_delete")
        for module in self.registry:
            if hasattr(module, 'on_message_delete'):
                await module.on_message_delete(message)



    async def on_message_edit(self, before, after):

        self.log.debug("on_message_edit")
        for module in self.registry:
            if hasattr(module, 'on_message_edit'):
                await module.on_message_edit(before, after)



    async def on_reaction_add(self, reaction, user):

        self.log.debug("on_reaction_add")
        for module in self.registry:
            if hasattr(module, 'on_reaction_add'):
                await module.on_reaction_add(reaction, user)



    async def on_reaction_clear(self, message, reactions):

        self.log.debug("on_reaction_clear")
        for module in self.registry:
            if hasattr(module, 'on_reaction_clear'):
                await module.on_reaction_clear(message, reactions)



    async def on_reaction_remove(self, reaction, user):

        self.log.debug("on_reaction_remove")
        for module in self.registry:
            if hasattr(module, 'on_reaction_remove'):
                await module.on_reaction_remove(reaction, user)



    async def on_ready(self):

        self.log.info("Bot ready!")
        for module in self.registry:
            if hasattr(module, 'on_ready'):
                await module.on_ready()



    async def on_resumed(self):

        self.log.debug("on_resumed")
        for module in self.registry:
            if hasattr(module, 'on_resumed'):
                await module.on_resumed()



    async def on_server_available(self, server):

        self.log.debug("on_server_available")
        for module in self.registry:
            if hasattr(module, 'on_server_available'):
                await module.on_server_available(server)



    async def on_server_emojis_update(self, before, after):

        self.log.debug("on_server_emojis_update")
        for module in self.registry:
            if hasattr(module, 'on_server_emojis_update'):
                await module.on_server_emojis_update(before, after)



    async def on_server_join(self, server):

        self.log.debug("on_server_join")
        for module in self.registry:
            if hasattr(module, 'on_server_join'):
                await module.on_server_join(server)



    async def on_server_remove(self, server):

        self.log.debug("on_server_remove")
        for module in self.registry:
            if hasattr(module, 'on_server_remove'):
                await module.on_server_remove(server)



    async def on_server_role_create(self, role):

        self.log.debug("on_server_role_create")
        for module in self.registry:
            if hasattr(module, 'on_server_role_create'):
                await module.on_server_role_create(role)



    async def on_server_role_delete(self, role):

        self.log.debug("on_server_role_delete")
        for module in self.registry:
            if hasattr(module, 'on_server_role_delete'):
                await module.on_server_role_delete(role)



    async def on_server_role_update(self, before, after):

        self.log.debug("on_server_role_update")
        for module in self.registry:
            if hasattr(module, 'on_server_role_update'):
                await module.on_server_role_update(before, after)



    async def on_server_unavailable(self, server):

        self.log.debug("on_server_unavailable")
        for module in self.registry:
            if hasattr(module, 'on_server_unavailable'):
                await module.on_server_unavailable(server)



    async def on_server_update(self, before, after):

        self.log.debug("on_server_update")
        for module in self.registry:
            if hasattr(module, 'on_server_update'):
                await module.on_server_update(before, after)



    async def on_socket_raw_receive(self, msg):

        # self.log.debug("on_socket_raw_receive")
        for module in self.registry:
            if hasattr(module, 'on_socket_raw_receive'):
                await module.on_socket_raw_receive(msg)



    async def on_socket_raw_send(self, payload):

        # self.log.debug("on_socket_raw_send")
        for module in self.registry:
            if hasattr(module, 'on_socket_raw_send'):
                await module.on_socket_raw_send(payload)



    async def on_typing(self, channel, user, when):

        self.log.debug("on_typing")
        for module in self.registry:
            if hasattr(module, 'on_typing'):
                await module.on_typing(channel, user, when)



    async def on_voice_state_update(self, member, before, after):

        self.log.debug("on_voice_state_update")
        for module in self.registry:
            if hasattr(module, 'on_voice_state_update'):
                await module.on_voice_state_update(member, before, after)


    async def confirm_prompt(self, channel, prompt, user=None, timeout=30, prompt_set=0, clean_up=False):
        """ Prompt user with Yes/No reactions
        @param message_target (discord.channel): Channel/DM Object
        @param message (str): Message to post
        @param duration (float): Time to leave message up before deletion
        @param message_type (str): Type of embed to use. See format_embed() for details
        @param embed (discord.embed): Embed object to display

        @returns True on yes, False on no, None if canceled

        @raises TimeoutError if timeout exceeded without a reply.
        """

        prompt_sets = (
            (u'\u2705', u'\u274E', u'\U0001F6AB'),
            # (u"\U0001F44D", u"\U0001F44E"),
            # (u"\U0001F44C",     u"\u274C"),
            # (u"\U0001F1FE", u"\U0001F1F3"),
        )

        yes_emoji = prompt_sets[prompt_set][0]
        no_emoji = prompt_sets[prompt_set][1]
        cancel_emoji = prompt_sets[prompt_set][2]


        # Post prompt
        # embed = await format_embed(prompt, "prompt")
        embed = discord.Embed(description=prompt)
        embed.set_footer(text=f"{yes_emoji}: Yes, {no_emoji}: No, {cancel_emoji}: Cancel")

        try:
            msg_obj = await self.send_message(channel,
                                              "Populating message options... Please wait!"
                                              " Any reactions you post now will be ignored!",
                                              )

        except discord.Forbidden:
            self.log.exception("Failed to send message, Forbidden?")
            raise

        except discord.NotFound:
            self.log.exception("Failed to send message, NotFound?")
            raise


        # Add Reactions for vote
        await self.add_reaction(msg_obj, yes_emoji)
        await self.add_reaction(msg_obj, no_emoji)
        await self.add_reaction(msg_obj, cancel_emoji)

        await self.edit_message(msg_obj, new_content=" ", embed=embed)

        # Wait for reactions
        ret = await self.wait_for_reaction([yes_emoji, no_emoji, cancel_emoji],
                                           user=user,
                                           timeout=timeout,
                                           message=msg_obj,
                                           )

        # This is our own prompt, so we really don't care if we delete here
        if clean_up:
            await self.delete_message(msg_obj)

        # If None, return false
        if ret is None:
            raise TimeoutError("User didn't respond within time limit")

        # If we got reactions, awesome!
        if str(ret.reaction.emoji) == yes_emoji:
            return True
        elif str(ret.reaction.emoji) == no_emoji:
            return False
        elif str(ret.reaction.emoji) == cancel_emoji:
            return None
        self.log.error("Got to an invalid return location!")
        raise RuntimeError("Unsure of how we got here")


    async def select_prompt(self, channel, prompt_question, prompt_list, user=None, timeout=30, clean_up=False):
        """ Ask user to respond and pick from a list of strings.

        @param channel (discord Obj): Channel to send to (This could be a user, and result in a DM!
        @param prompt_list (list/tuple): List of options to give the user
        @param user (discord Obj): Valid responder (Set to None to accept any)
        @param timeout (int/float): Seconds to wait for user response
        @param clean_up: Should we cleanup after

        @throws TimeoutError If no response is given it time.
        """
        digits = [b'1\xe2\x83\xa3',
                  b'2\xe2\x83\xa3',
                  b'3\xe2\x83\xa3',
                  b'4\xe2\x83\xa3',
                  b'5\xe2\x83\xa3',
                  b'6\xe2\x83\xa3',
                  b'7\xe2\x83\xa3',
                  b'8\xe2\x83\xa3',
                  b'9\xe2\x83\xa3',
                  b'\xf0\x9f\x94\x9f',
                  ]

        digits = [x.decode() for x in digits[:len(prompt_list)]]

        embed = discord.Embed(
            color=discord.Color.default(),
            description=prompt_question,
        )

        for idx, question in enumerate(prompt_list):
            embed.add_field(name=f"{digits[idx]}",
                            value=question,
                            inline=False)

        embed.set_footer(text="Note: Previous responses before now are ignored!")

        msg_obj = await self.send_message(channel,
                                          "Populating message options... Please wait!",
                                          )

        for i in range(len(prompt_list)):
            await self.add_reaction(msg_obj, digits[i])

        await self.edit_message(msg_obj, embed=embed)
        if user:
            await self.edit_message(msg_obj, new_content=f"<@{user.id}>")
        else:
            await self.edit_message(msg_obj, new_content=" ")

        ret_val = await self.wait_for_reaction(digits,
                                               message=msg_obj,
                                               user=user,
                                               timeout=timeout
                                               )

        if clean_up:
            await self.delete_message(msg_obj)

        if ret_val is None:
            raise TimeoutError("No user selection")

        for idx, val in enumerate(digits):
            if ret_val[0].emoji == val:
                return idx

        return None


    async def select_custom_prompt(self, channel, prompt_question, prompt_tuples, user=None, timeout=30, clean_up=False):  # noqa E501
        """ Ask user to respond and pick from a list of strings.

        @param channel (discord Obj): Channel to send to (This could be a user, and result in a DM!
        @param prompt_tuples (list/tuple): List of (emoji, option_str) tuples
        @param user (discord Obj): Valid responder (Set to None to accept any)
        @param timeout (int/float): Seconds to wait for user response
        @param clean_up: Should we cleanup after

        @throws TimeoutError If no response is given it time.
        """

        msg = f"\n{prompt_question}\n"
        for prompt_tuple in prompt_tuples:
            msg += f"{prompt_tuple[0]}: {prompt_tuple[1]}\n"


        initial_text = "Please Wait! Responses before the bot is ready are ignored!"

        msg_obj = await self.send_message(channel, initial_text)

        valid_responses = []
        for prompt_tuple in prompt_tuples:
            await self.add_reaction(msg_obj, prompt_tuple[0])
            valid_responses.append(prompt_tuple[0])

        if user:
            await self.edit_message(msg_obj, new_content=f"<@{user.id}>{msg}")
        else:
            await self.edit_message(msg_obj, new_content="{msg}")

        ret_val = await self.wait_for_reaction(valid_responses,
                                               message=msg_obj,
                                               user=user,
                                               timeout=timeout
                                               )

        if clean_up:
            await self.delete_message(msg_obj)

        if ret_val is None:
            raise TimeoutError("No user selection")

        for idx, val in enumerate(prompt_tuples):
            if ret_val[0].emoji == val[0]:
                return idx

        return None


    async def text_prompt(self, channel, prompt_question, user=None, timeout=30, clean_up=False):
        """ Ask user to respond and then returns the value to the caling function
        @param channel (discord Obj): Channel to send to (This could be a user, and result in a DM!
        @param prompt_question (str): Question asked of the user
        @param user (discord Obj): Valid responder (Set to None to accept any)
        @param timeout (int/float): Seconds to wait for user response
        @param clean_up: Should we cleanup after

        @return Text message user replied with

        @throws TimeoutError when user fails to respond in time
        """
        embed = discord.Embed(
            color=discord.Color.default(),
            description=prompt_question,
        )

        # footer_text = "Type 'STOP' to cancel this prompt."
        # if timeout:
        footer_text = f"You have {timeout:.0f} seconds to answer"
        embed.set_footer(text=footer_text)

        await self.send_message(channel, embed=embed)

        msg_obj = await self.wait_for_message(
            channel=channel,
            author=user,
            timeout=timeout)

        if msg_obj is None:
            raise TimeoutError()
        if msg_obj.content == "STOP":
            return False

        return msg_obj.content
