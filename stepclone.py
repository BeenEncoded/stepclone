import sys, os, subprocess, dataclasses, pickle, atexit, argparse

import random

@dataclasses.dataclass
class IncrementalState:
    current_rev: int=0
    blocksize: int=1
    cwd: str=os.getcwd()

    def next_rev(self):
        self.current_rev += self.blocksize

    def prev_rev(self):
        self.current_rev -= self.blocksize

@dataclasses.dataclass
class ProgramData:
    #program data
    state: IncrementalState=IncrementalState()

    #temp or constant metadata
    state_save_file: str=os.path.abspath("python_clone_state.dat")

    def load(self) -> bool:
        return self._load_state()

    def save(self):
        self._save_state()
    
    def _load_state(self) -> bool:
        '''
        Loads the state.  Returns false if the file was not found.
        '''
        if os.path.isfile(self.state_save_file):
            success = True
            with open(self.state_save_file, 'rb') as f:
                try:
                    self.state = pickle.load(f)
                except EOFError:
                    success = False
                except:
                    success = False
            return success
        return True

    def _save_state(self):
        with open(self.state_save_file, 'wb') as f:
            pickle.dump(self.state, f)

def mkargparse():
    ap = argparse.ArgumentParser(description="A python utility to automate incrimental mercurial clones for large repositories.")
    ap.add_argument("repository", type=str, help="The mercurial repository to be cloned or pulled.")
    ap.add_argument("folder", type=str, help="The folder the repository is located.  Give it the same name as the folder that hg will create.")
    ap.add_argument("--pullonly", "-p", action='store_true', help="Specifies that the program should skip cloning entirely.  This can be used to continue \
        an incremental pull that was interrupted.")
    ap.add_argument("--revblock", "-rb", nargs='?', const=1, type=int, help="Specifies how many revisions to clone initially \
        or pull each time.  Default is 1.")
    return ap

PDATA = ProgramData()
PARGS = mkargparse()

def hgclone(repository: str, destination: str, revblock: int=1) -> bool:
    '''
    executes an incrimental clone on a mercurial repository, returning true if the return code 
    is zero.  False otherwise.
    '''
    command = ["hg", "clone", "--uncompressed", ("--rev=" + str(revblock)), repository, os.path.abspath(destination)]
    result = subprocess.run(command, stdout=sys.stdout)
    return (result.returncode == 0)

def hgpull(destination: str, revision: int=1) -> bool:
    '''
    pulls a revision from the remote.
    '''
    command = ["hg", "pull", ("--rev=" + str(revision))]
    result = subprocess.run(command, stdout=sys.stdout)
    return (result.returncode == 0)

def hgupdate() -> bool:
    command = ["hg", "update"]
    result = subprocess.run(command, stdout=sys.stdout)
    return (result.returncode == 0)

def incremental_clone(repository: str, destination: str, revblock: int=1, pullonly: bool=False) -> bool:
    state = PDATA.state

    if not pullonly:
        state.current_rev = 0
        state.next_rev()
        print(os.linesep + "Cloning revision " + str(state.current_rev) + os.linesep)
        if hgclone(repository, destination, state.current_rev):
            PDATA.save()
        else:
            state.prev_rev()
            return False
    
    #we currently have no stop condition... yet...
    if os.path.isdir(destination):
        print("changing cwd to " + destination)
        os.chdir(destination)
    else:
        print("Unable to chdir into " + destination + os.linesep + "It does not exist!")
        return False
    while True:
        state.next_rev()
        print(os.linesep + "Pulling revision " + str(state.current_rev) + os.linesep)
        if hgpull(destination, state.current_rev):
            PDATA.save()
        else:
            state.prev_rev()
            PDATA.save()
            print(os.linesep + "Creating working copy..." + os.linesep)
            hgupdate(destination)
            break

def test_pdata():
    global PDATA
    state = PDATA.state
    for x in range(0, 1000):
        PDATA = ProgramData()
        state.current_rev = random.randint(1, 10000)
        tempdata = ProgramData()
        tempdata.state.current_rev = PDATA.state.current_rev
        PDATA.save()
        PDATA = ProgramData(state=IncrementalState())
        assert PDATA.state.current_rev != tempdata.state.current_rev
        PDATA.load()
        assert PDATA.state.current_rev == tempdata.state.current_rev

def main(argv):
    global PARGS
    arguments = None
    if len(argv) > 1:
        arguments = PARGS.parse_args(argv[1:])
    else:
        PARGS.parse_args(argv) #this will print the appropriate error and exit
    PDATA.load()
    if arguments.revblock is not None:
        PDATA.state.blocksize = arguments.revblock

    incremental_clone(arguments.repository, arguments.folder, PDATA.state.blocksize, arguments.pullonly)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))