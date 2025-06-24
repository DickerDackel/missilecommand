import pytest

from contextlib import nullcontext as does_not_raise


def test_FIXME():
    assert True is True
    ...

    with pytest.raises(FIXME_ExpectedException_FIXME) as e:  # noqa
        FIXME_function_expected_to_raise_exception()  # noqa
    assert 'FIXME_string_expected_in_exception' in str(e.value)
