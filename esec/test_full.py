import os
import sys

class Interpreter(object):
    def __init__(self, optimise=False):
        self.path = None
        self._proc = None
        self._str = self.safe_name = type(self).__name__
        if optimise:
            self.interpreter_args = ["-B", "-OO"]
            self._str += " -OO"
            self.safe_name += "_OO"
            self.nose_cmd = None
        else:
            self.interpreter_args = ["-B"]
            self.nose_cmd = ["-m", "nose.core"]
        self.log_file = "test_%s.txt" % self.safe_name.lower()
        self._temp_file = "test_%s.tmp" % self.safe_name.lower()

    def __str__(self):
        return self._str

    def run(self, script, *arguments):
        import subprocess
        try:
            if self.path and script:
                args = [self.path]
                if self.interpreter_args:
                    args.extend(self.interpreter_args)
                if isinstance(script, str):
                    args.append(script)
                else:
                    args.extend(script)
                args.extend(arguments)
                self._proc = subprocess.Popen(args, stdin=None, stdout=open("NUL", "w"), stderr=open(self._temp_file, "w"))
        except (IOError, WindowsError):
            self._proc = None
            try: os.remove(self._temp_file)
            except: pass

    def wait(self):
        if self._proc:
            self._proc.wait()
            data = open(self._temp_file).readlines()
            os.remove(self._temp_file)
            return data
        else:
            return []

    def reset(self):
        self._proc = None
    
    def run_nose(self):
        self.run(self.nose_cmd)

    def clear_log(self):
        try:
            os.remove(self.log_file)
        except (WindowsError, IOError):
            pass

    def log(self, text):
        with open(self.log_file, mode='a') as f:
            print >> f, text

class CPython27(Interpreter):
    def __init__(self, oo=False):
        Interpreter.__init__(self, optimise=oo)

        try:
            import _winreg
            self.path = str(_winreg.QueryValue(_winreg.HKEY_LOCAL_MACHINE, r"Software\Python\PythonCore\2.7\InstallPath"))
            self.path = os.path.join(self.path, 'python.exe')
        except:
            self.path = r"\Python27\python.exe"

class CPython26(Interpreter):
    def __init__(self, oo=False):
        Interpreter.__init__(self, optimise=oo)

        self.path = r"\Python26\python.exe"

class IronPython27(Interpreter):
    def __init__(self, oo=False):
        Interpreter.__init__(self, optimise=oo)

        self.path = r"\IronPython27\ipy.exe"

class IronPython26(Interpreter):
    def __init__(self, oo=False):
        Interpreter.__init__(self, optimise=oo)

        self.path = r"\IronPython_26\ipy.exe"


def clean(interpreters):
    for i in interpreters:
        i.clear_log()

def run_nosetests(interpreters):
    print 'Running nosetests'
    for i in interpreters:
        i.run_nose()

    all_succeeded = True
    for i in interpreters:
        result = i.wait()
        if not result: continue
        if 'F' in result[0] or 'E' in result[0]:
            all_succeeded = False
            print 'Failure for', i
            i.log(''.join(result[1:]))
        i.reset()

    if not all_succeeded:
        print
        print "Failures in unit tests."
        print
    return all_succeeded

def run_regression(interpreters):
    print 'Running Regression batch file'
    for i in interpreters:
        import shutil
        shutil.rmtree("results/Test_" + i.safe_name, ignore_errors=True)
        i.run("run.py", "-b", "Regression", "-s", "batch.pathbase='results/Test_%s'" % i.safe_name)

    all_succeeded = True
    for i in interpreters:
        try:
            errors = i.wait()
            if errors:
                all_succeeded = False
                print 'Failure for', i
                i.log(''.join(errors))

            for line in open('results/Test_%s/_summary.txt' % i.safe_name):
                bits = [bit for bit in line.split(' ') if bit]
                if bits[0] == '#': continue

                if bits[4] != 'ITER_LIMIT' and bits[6] != 'ITER_LIMIT':
                    i.log(line)
        except (IOError, WindowsError):
            pass
        i.reset()

    if not all_succeeded:
        print
        print "Failures in regression tests."
    return all_succeeded


if __name__ == '__main__':
    assert sys.platform == 'win32', "This script is designed for Windows machines."
    
    interpreters = [CPython26(), CPython27(), IronPython26(), IronPython27(),
                    CPython26(oo=True), CPython27(oo=True), IronPython26(oo=True), IronPython27(oo=True)]
    
    clean(interpreters)
    run_nosetests(interpreters)
    run_regression(interpreters)
