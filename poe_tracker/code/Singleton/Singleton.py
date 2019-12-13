
import inspect



class Singleton(type):
    """ Simple Singleton that keep only one value for all instances
    """
    def __init__(cls, name, bases, dic):
        super(Singleton, cls).__init__(name, bases, dic)
        cls.instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance



class SingletonArgs(type):
    """ Singleton that keep single instance for single set of arguments. E.g.:
    assert SingletonArgs('spam') is not SingletonArgs('eggs')
    assert SingletonArgs('spam') is SingletonArgs('spam')
    """
    _instances = {}
    _init = {}

    def __init__(cls, name, bases, dct):
        cls._init[cls] = dct.get('__init__', None)

    def __call__(cls, *args, **kwargs):
        init = cls._init[cls]
        if init is not None:
            key = (cls, frozenset(inspect.getcallargs(init, None, *args, **kwargs).items()))
        else:
            key = cls

        if key not in cls._instances:
            cls._instances[key] = super(SingletonArgs, cls).__call__(*args, **kwargs)
        return cls._instances[key]
