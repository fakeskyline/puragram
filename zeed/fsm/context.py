class FSMContext:
    def __init__(self, storage, key):
        self.storage = storage
        self.key = key

    def set_state(self, state):
        self.storage.set_state(self.key, None if state is None else str(state))

    def get_state(self):
        return self.storage.get_state(self.key)

    def set_data(self, data):
        self.storage.set_data(self.key, data)

    def get_data(self):
        return self.storage.get_data(self.key)

    def update_data(self, **kwargs):
        return self.storage.update_data(self.key, **kwargs)

    def clear(self):
        self.storage.clear(self.key)