import logging

from os import path
from os import listdir

log = logging.getLogger(__name__)


class FlagsFile:

    """docstring for ClangCompleteFile"""

    _clang_complete_file = None
    _last_modification_time = 0

    def __init__(self, from_folder, to_folder):
        """search for .clang_complete file up the tree

        Args:
            from_folder (str): path to folder where we start the search
            to_folder (str): path to folder we should not go beyond

        Returns:
            str: path to .clang_complete file or None if not found
        """
        current_folder = from_folder
        one_past_stop_folder = path.dirname(to_folder)
        while current_folder != one_past_stop_folder:
            for file in listdir(current_folder):
                if file == ".clang_complete":
                    self._clang_complete_file = path.join(current_folder, file)
                    self._last_modification_time = path.getmtime(
                        self._clang_complete_file)
                    log.debug(" found .clang_complete file: %s",
                              self._clang_complete_file)
                    return
            if current_folder == path.dirname(current_folder):
                break
            current_folder = path.dirname(current_folder)

    def was_modified(self):
        if not self._clang_complete_file:
            # it was not even found yet
            return False
        actual_modification_time = path.getmtime(self._clang_complete_file)
        if actual_modification_time > self._last_modification_time:
            log.info(" .clang_complete was modified.")
            self._last_modification_time = actual_modification_time
            return True
        return False

    def get_flags(self, separate_includes):
        """parse .clang_complete file

        Args:
            file (str): path to a file
            separate_includes (bool): if True: -I<include> turns to '-I "<include>"'.
                                      if False: stays -I<include>
                                      Separation is needed for binary completion

        Returns:
            list(str): parsed list of includes from the file
        """
        file = self._clang_complete_file
        if not file:
            log.error(" cannot get flags from clang_complete_file. No file.")
            return []

        flags = []
        folder = path.dirname(file)
        mask = '-I{}'
        if separate_includes:
            mask = '-I "{}"'
        with open(file) as f:
            content = f.readlines()
            for line in content:
                if line.startswith('-D'):
                    flags.append(line)
                elif line.startswith('-I'):
                    path_to_add = line[2:].rstrip()
                    if path.isabs(path_to_add):
                        flags.append(mask.format(
                            path.normpath(path_to_add)))
                    else:
                        flags.append(mask.format(
                            path.join(folder, path_to_add)))
        log.debug(" .clang_complete contains flags: %s", flags)
        return flags
