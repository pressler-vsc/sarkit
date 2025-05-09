import itertools
import sys

import pytest

import sarkit.verification._consistency as con


class DummyConsistency(con.ConsistencyChecker):
    """A ConsistencyChecker used for unit testing and code coverage"""

    def check_need_pass(self):
        with self.need("need pass"):
            assert True

    def check_need_fail(self):
        with self.need("need fail"):
            assert False

    def check_need_both(self):
        with self.need("need pass"):
            assert True
        with self.need("need fail"):
            assert False

    def check_need_fail_nodetails(self):
        with self.need():
            assert False

    def check_pre_need_pass(self):
        with self.precondition():
            assert True
            with self.need("need pass"):
                assert True

    def check_nopre_need_pass(self):
        with self.precondition():
            assert False
            with self.need("need pass"):
                assert True

    def check_want_pass(self):
        with self.want("want pass"):
            assert True

    def check_want_fail(self):
        with self.want("want fail"):
            assert False

    def check_pre_want_pass(self):
        with self.precondition():
            assert True
            with self.want("want pass"):
                assert True

    def check_nopre_want_pass(self):
        with self.precondition():
            assert False
            with self.want("want pass"):
                assert True

    def check_exception(self):
        raise ValueError


@pytest.fixture
def dummycon():
    """Fixture which initializes a DummyConsistency object

    Yields
    ------
    DummyConsistency object
    """
    yield DummyConsistency()


def test_all(dummycon, capsys, monkeypatch):
    dummycon.check()
    assert len(dummycon.all()) == 11
    assert len(dummycon.failures()) == 5

    num_checks_by_part = [
        len(x) for x in (dummycon.passes(), dummycon.skips(), dummycon.failures())
    ]
    assert all(x > 0 for x in num_checks_by_part)
    assert sum(num_checks_by_part) == len(dummycon.all())

    failures = dummycon.failures()
    details = itertools.chain.from_iterable(
        [value["details"] for value in failures.values()]
    )
    passed = [item for item in details if item["passed"]]
    assert passed

    failures = dummycon.failures(omit_passed_sub=True)
    details = itertools.chain.from_iterable(
        [value["details"] for value in failures.values()]
    )
    passed = [item for item in details if item["passed"]]
    assert not passed

    def prints_color():
        captured = capsys.readouterr()
        return "\x1b" in captured.out

    # color=None, notty
    dummycon.print_result(color=None)
    assert not prints_color()

    # color=None, tty
    with monkeypatch.context() as m:
        m.setattr(sys.stdout, "isatty", lambda: True)
        dummycon.print_result(color=None)
        assert prints_color()

        m.setenv("NO_COLOR", "")
        dummycon.print_result(color=None)
        assert not prints_color()

    # color=True
    dummycon.print_result(color=True)
    assert prints_color()

    # color=False
    dummycon.print_result(color=False)
    assert not prints_color()

    dummycon.print_result(
        include_passed_checks=True, skip_detail=True, fail_detail=True, pass_detail=True
    )
    captured3 = capsys.readouterr()
    assert "Skip" in captured3.out
    assert "check_nopre_want_pass" in captured3.out
    assert "check_want_pass" in captured3.out


def test_one(dummycon):
    dummycon.check("check_need_pass")
    assert not dummycon.failures()


def test_multiple(dummycon):
    dummycon.check(["check_need_pass", "check_need_fail"])
    assert set(dummycon.failures()) == {"check_need_fail"}
    assert set(dummycon.all()).difference(dummycon.failures()) == {"check_need_pass"}


def test_check_with_ignore_pattern(dummycon):
    # all checks must start with check_
    dummycon.check(ignore_patterns=["check_"])
    assert set(dummycon.all()) == set()


@pytest.mark.parametrize("should_ignore", [True, False])
def test_check_with_ignore_specific(dummycon, should_ignore):
    test_name = "check_exception"
    ignore_patterns = [test_name] if should_ignore else []
    dummycon.check(ignore_patterns=ignore_patterns)
    was_tested = test_name in dummycon.all()
    assert was_tested != should_ignore


def test_invalid(dummycon):
    with pytest.raises(ValueError):
        dummycon.check("this_does_not_exist")


def test_approx():
    apx = con.Approx(10.0, atol=0.1, rtol=0)
    assert apx == 10.0
    assert apx == 10.01
    assert not apx != 10.01
    assert apx > 10.01
    assert apx >= 10.01
    assert apx >= 0
    assert not apx <= 0
    assert apx < 10.01
    assert apx <= 10.01
    assert repr(apx) == "10.0 ± 0.1"
