import ctypes
import functools
import importlib
import multiprocessing
import unittest
import unittest.mock
import pickle

from llvmlite import binding as llvm


def _test_dylib_resource_loading(result):
    try:
        assert llvm.ffi.lib._lib_handle is None  # We must not have loaded the llvmlite dylib yet.
        spec = importlib.util.find_spec(llvm.ffi.__name__.rpartition(".")[0])

        true_dylib = spec.loader.get_resource_reader().open_resource(llvm.ffi.get_library_name())

        # A mock resource loader that does not support resource paths
        class MockResourceReader(importlib.abc.ResourceReader):
            def is_resource(self, name):
                return True
            def resource_path(self, name):
                raise FileNotFoundError
            def open_resource(self, name):
                return true_dylib
            def contents(self):
                return []

        # Mock resource loader to force the dylib to be extracted into a
        # temporary file.
        with unittest.mock.patch.object(
                spec.loader, 'get_resource_reader',
                return_value = MockResourceReader()), \
             unittest.mock.patch(
                 'llvmlite.binding.ffi.get_library_name',
                 return_value = 'notllvmlite.so'):
            llvm.llvm_version_info  # force library loading to occur.
    except Exception as e:
        result.put(e)
        raise
    result.put(None)


class TestModuleLoading(unittest.TestCase):
    def test_dylib_resource_loading(self):
        subproc_result = multiprocessing.Queue()
        subproc = multiprocessing.Process(
                target=_test_dylib_resource_loading,
                args=(subproc_result,))
        subproc.start()
        result = subproc_result.get()
        subproc.join()
        if subproc.exitcode:
            raise result


if __name__ == "__main__":
    unittest.main()
