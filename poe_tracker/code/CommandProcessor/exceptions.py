


class DiscordArgumentError(Exception):
    """Base class for exceptions in this modules."""
    pass



class NoValidCommands(DiscordArgumentError):

    def __init__(self, message):
        self.message = message



class HelpNeeded(DiscordArgumentError):

    def __init__(self, message):
        self.message = message
