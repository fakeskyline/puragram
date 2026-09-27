class State(str):
    def __new__(cls, value=""):
        return super().__new__(cls, value)


class StatesGroup:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        prefix = cls.__name__
        for name, value in list(vars(cls).items()):
            if name.startswith("_") or not isinstance(value, State):
                continue
            key = str(value) or name
            setattr(cls, name, State(f"{prefix}:{key}"))

    def __init__(self):
        raise TypeError("StatesGroup cannot be instantiated")