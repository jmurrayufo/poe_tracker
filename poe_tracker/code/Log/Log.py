import logging


class Log:
    __shared_state = {}
    def __init__(self, args=None):

        # Borg pattern
        self.__dict__ = self.__shared_state

        # In cases where we are just being created without args, just return
        if args is None:
            return

        self.args = args

        self.name = self.args.name
        self._log = logging.getLogger(self.name)
        # This needs to be reworked into an args call
        if args.log_level == 'INFO':
            self._log.setLevel(logging.INFO)
        elif args.log_level == 'DEBUG':
            self._log.setLevel(logging.DEBUG)

        formatter = logging.Formatter('{asctime} {levelname} {filename}:{funcName}:{lineno} {message}', style='{')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        self._log.addHandler(ch)


    def __getattr__(self, name):
        return getattr(self._log, name)
