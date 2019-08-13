"""
    Stanford CoreNLP function wrapper
    @author: João Gabriel Melo Barbirato
"""

import subprocess
from time import sleep

from config import TMP_DIR, BASE_DIR, CORENLP_DIR

_UTIL_SHELL_BASE = '/app/src/UTIL/shell'

_dict_commands = {
    'start_base': '/usr/bin/bash ' + BASE_DIR + _UTIL_SHELL_BASE + '/start-corenlp-server.sh '
                  + BASE_DIR + '/' + CORENLP_DIR + ' ' + TMP_DIR,
    'stop_base': '/usr/bin/bash ' + BASE_DIR + _UTIL_SHELL_BASE + '/stop-corenlp-server.sh ' + TMP_DIR,
    'correference_resolution': '/usr/bin/bash ' + BASE_DIR + _UTIL_SHELL_BASE + '/coreference-corenlp.sh'
}


class CoreNLPWrapper:
    def __init__(self):
        self._subprocess = None

    def communicate(self):
        if self._subprocess is not None:
            self._subprocess.communicate()

    def start_base(self):
        self._subprocess = subprocess.Popen(_dict_commands['start_base'].split(' '))
        sleep(1)

    def coreference_resolution(self, input_file, out_dir, comm=False):
        """
        Coreference resolution
        :param input_file: sentence file
        :param out_dir: output directory
        :param comm: conditional for waiting on the subprocess to end
        :return:
        """
        command_with_args = _dict_commands['correference_resolution'] + ' ' + input_file + ' ' + out_dir
        self._subprocess = subprocess.Popen(command_with_args.split(' '))
        if comm:
            self._subprocess.communicate()
        # TODO: manage it's return

    def terminate_base(self):
        self._subprocess = subprocess.Popen(_dict_commands['stop_base'].split(' '))
        sleep(1)
