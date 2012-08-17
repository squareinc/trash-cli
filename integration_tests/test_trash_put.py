# Copyright (C) 2009-2011 Andrea Francia Trivolzio(PV) Italy
import os

from nose.tools import istest, assert_equals, assert_not_equals
from nose.tools import assert_in

from .files import having_file, require_empty_dir, having_empty_dir
from trashcli.trash import TrashPutCmd

class TrashPutTest:

    def setUp(self):
        self.prepare_fixture()

    def prepare_fixture(self):
        require_empty_dir('sandbox')
        self.environ = {'XDG_DATA_HOME': 'sandbox/XDG_DATA_HOME' }

        from .output_collector import OutputCollector
        self.out     = OutputCollector()
        self.err     = OutputCollector()
        self.fstab   = FakeFstab()

        self.stderr_should_be = self.err.should_be
        self.output_should_be = self.out.should_be

    def run_trashput(self, *argv):
        cmd = TrashPutCmd(
            stdout  = self.out,
            stderr  = self.err,
            environ = self.environ,
            fstab   = self.fstab
        )
        self.exit_code = cmd.run(list(argv))
        self.stderr = self.err.getvalue()

@istest
class trash_put_stderr(TrashPutTest):
    @istest
    def should_tell_where_a_file_is_trashed(self):
        having_file('foo')
        self.run_trashput('trash-put', '-v', 'foo')

        assert_in("trash-put: `foo' trashed in sandbox/XDG_DATA_HOME/Trash",
                  self.stderr.splitlines())


from trashcli.trash import FakeFstab
from textwrap import dedent
@istest
class when_trash_dir_is_not_sticky(TrashPutTest):
    @istest
    def shoult_print_a_warning(self):
        having_empty_dir('fake-vol/.Trash')
        having_file('fake-vol/foo')
        self.fstab.add_mount('fake-vol')

        self.run_trashput('trash-put', '-v', 'fake-vol/foo')

        self.assert_line_in_text(
                'trash-put: found unsecure .Trash dir (should be sticky): '
                'fake-vol/.Trash', self.stderr)

    def assert_line_in_text(self, line, text):
        assert_in(line, text.splitlines(), dedent('''\
                Line not found in text
                Line:

                %s

                Text:

                ---
                %s---''')
                %(repr(line), text))



def should_fail(func):
    from nose.tools import assert_raises
    with assert_raises(AssertionError):
        func()

@istest
class exit_code(TrashPutTest):
    @istest
    def should_be_zero_on_success(self):
        having_file('foo')
        self.run_trashput('trash-put', 'foo')
        self.exit_code_should_be_successfull()

    @istest
    def should_be_non_zero_on_failure(self):
        self.run_trashput('trash-put', 'non-existent')
        self.exit_code_should_be_not_successfull()

    def exit_code_should_be_successfull(self):
        assert_equals(0, self.exit_code)

    def exit_code_should_be_not_successfull(self):
        assert_not_equals(0, self.exit_code)

@istest
class when_deleting_a_file(TrashPutTest):

    def setUp(self):
        self.prepare_fixture()

        having_file('sandbox/foo')
        self.run_trashput('trash-put', 'sandbox/foo')

    @istest
    def it_should_remove_the_file(self):

        file_should_have_been_deleted('sandbox/foo')

    @istest
    def it_should_remove_it_silently(self):

        self.output_should_be('')

    def a_trashinfo_file_should_have_been_created(self):

        file('sandbox/XDG_DATA_HOME/Trash/info/foo.trashinfo').read()

@istest
class when_fed_with_dot_arguments(TrashPutTest):

    def setUp(self):
        self.prepare_fixture()

    def test_dot_argument_is_skipped(self):
        having_file('other_argument')

        self.run_trashput("trash-put", ".", "other_argument")

        # the dot directory shouldn't be operated, but a diagnostic message
        # shall be writtend on stderr
        self.stderr_should_be(
                "trash-put: cannot trash directory `.'\n")

        # the remaining arguments should be processed
        assert not exists('other_argument')

    def test_dot_dot_argument_is_skipped(self):
        having_file('other_argument')

        self.run_trashput("trash-put", "..", "other_argument")

        # the dot directory shouldn't be operated, but a diagnostic message
        # shall be writtend on stderr
        self.stderr_should_be(
            "trash-put: cannot trash directory `..'\n")

        # the remaining arguments should be processed
        assert not exists('other_argument')

    def test_dot_argument_is_skipped_even_in_subdirs(self):
        having_empty_dir('sandbox/')
        having_file('other_argument')

        self.run_trashput("trash-put", "sandbox/.", "other_argument")

        # the dot directory shouldn't be operated, but a diagnostic message
        # shall be writtend on stderr
        self.stderr_should_be(
            "trash-put: cannot trash `.' directory `sandbox/.'\n")

        # the remaining arguments should be processed
        assert not exists('other_argument')
        assert exists('sandbox')

    def test_dot_dot_argument_is_skipped_even_in_subdirs(self):
        having_empty_dir('sandbox')
        having_file('other_argument')

        self.run_trashput("trash-put", "sandbox/..", "other_argument")

        # the dot directory shouldn't be operated, but a diagnostic message
        # shall be writtend on stderr
        self.stderr_should_be(
            "trash-put: cannot trash `..' directory `sandbox/..'\n")

        # the remaining arguments should be processed
        assert not exists('other_argument')
        assert exists('sandbox')

def file_should_have_been_deleted(path):
    import os
    assert not os.path.exists('sandbox/foo')

exists = os.path.exists
