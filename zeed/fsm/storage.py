import json
import os
import sqlite3
import threading


def _k(key):
    if isinstance(key, (tuple, list)):
        return ":".join(str(x) for x in key)
    return str(key)


class BaseStorage:
    def get_state(self, key):
        raise NotImplementedError

    def set_state(self, key, state):
        raise NotImplementedError

    def get_data(self, key):
        raise NotImplementedError

    def set_data(self, key, data):
        raise NotImplementedError

    def update_data(self, key, **kwargs):
        d = self.get_data(key) or {}
        d.update(kwargs)
        self.set_data(key, d)
        return d

    def clear(self, key):
        self.set_state(key, None)
        self.set_data(key, {})

    def close(self):
        pass


class MemoryStorage(BaseStorage):
    def __init__(self):
        self._states = {}
        self._data = {}
        self._lock = threading.RLock()

    def get_state(self, key):
        with self._lock:
            return self._states.get(_k(key))

    def set_state(self, key, state):
        with self._lock:
            self._states[_k(key)] = state

    def get_data(self, key):
        with self._lock:
            return dict(self._data.get(_k(key), {}))

    def set_data(self, key, data):
        with self._lock:
            self._data[_k(key)] = dict(data)

    def clear(self, key):
        k = _k(key)
        with self._lock:
            self._states.pop(k, None)
            self._data.pop(k, None)


class FileStorage(BaseStorage):
    def __init__(self, path="fsm.json"):
        self.path = path
        self._lock = threading.RLock()
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as f:
                blob = json.load(f)
        else:
            blob = {}
        self._states = blob.get("states", {})
        self._data = blob.get("data", {})

    def _save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"states": self._states, "data": self._data},
                      f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def get_state(self, key):
        with self._lock:
            return self._states.get(_k(key))

    def set_state(self, key, state):
        with self._lock:
            self._states[_k(key)] = state
            self._save()

    def get_data(self, key):
        with self._lock:
            return dict(self._data.get(_k(key), {}))

    def set_data(self, key, data):
        with self._lock:
            self._data[_k(key)] = dict(data)
            self._save()


class SQLiteStorage(BaseStorage):
    def __init__(self, path="fsm.db"):
        self.path = path
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS fsm ("
            "key TEXT PRIMARY KEY, state TEXT, data TEXT)"
        )
        self._conn.commit()

    def _row(self, key):
        return self._conn.execute(
            "SELECT state, data FROM fsm WHERE key = ?", (_k(key),)
        ).fetchone()

    def get_state(self, key):
        with self._lock:
            row = self._row(key)
            return row[0] if row else None

    def set_state(self, key, state):
        with self._lock:
            self._conn.execute(
                "INSERT INTO fsm(key, state, data) VALUES(?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET state=excluded.state",
                (_k(key), state, "{}"),
            )
            self._conn.commit()

    def get_data(self, key):
        with self._lock:
            row = self._row(key)
            if not row or not row[1]:
                return {}
            return json.loads(row[1])

    def set_data(self, key, data):
        with self._lock:
            self._conn.execute(
                "INSERT INTO fsm(key, state, data) VALUES(?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET data=excluded.data",
                (_k(key), None, json.dumps(data, ensure_ascii=False)),
            )
            self._conn.commit()

    def clear(self, key):
        with self._lock:
            self._conn.execute("DELETE FROM fsm WHERE key = ?", (_k(key),))
            self._conn.commit()

    def close(self):
        self._conn.close()