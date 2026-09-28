from zeed import FSMContext, MemoryStorage, State, StatesGroup


class Form(StatesGroup):
    name = State()
    age = State()


def test_statesgroup_prefix():
    assert str(Form.name) == "Form:name"
    assert str(Form.age) == "Form:age"


def test_context_set_get():
    st = MemoryStorage()
    ctx = FSMContext(st, "chat:user")
    assert ctx.get_state() is None
    ctx.set_state(Form.name)
    assert ctx.get_state() == "Form:name"
    ctx.clear()
    assert ctx.get_state() is None


def test_context_data():
    st = MemoryStorage()
    ctx = FSMContext(st, "1:1")
    ctx.set_data({"a": 1})
    assert ctx.get_data() == {"a": 1}
    ctx.update_data(b=2)
    assert ctx.get_data() == {"a": 1, "b": 2}


def test_isolated_keys():
    st = MemoryStorage()
    a, b = FSMContext(st, "1:1"), FSMContext(st, "1:2")
    a.set_state("x")
    b.set_state("y")
    assert a.get_state() == "x"
    assert b.get_state() == "y"