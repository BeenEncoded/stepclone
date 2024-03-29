# Stepclone clones a mercurial repository incrementally.  This can be 
# useful when the entire repository and all its checksums results
# in a clone that takes too long to be practical.

# Copyright (C) 2019  Jonathan Whitlock

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see https://www.gnu.org/licenses/

import sys, os, subprocess, dataclasses, pickle, atexit, argparse, re, semver

from urllib import request

VERSION = semver.VersionInfo(1, 1, 0, "beta")

def most_recent_rev(repository):
    print("Obtaining the most recent revision from the repository's log...")
    rev_expression = "(rev [0-9]+)"
    repository += "/log"
    response = request.urlopen(repository)

    matches = re.findall(rev_expression, str(response.read()))
    if len(matches) == 0:
        print("UNABLE TO READ THE REV!")
        sys.exit(1)
    print(repository + " @ " + matches[0][4:])
    return matches[0][4:]

@dataclasses.dataclass
class IncrementalState:
    current_rev: int=0
    rev_end: int=int(-1)
    blocksize: int=1
    cwd: str=os.getcwd()

    def next_rev(self):
        self.current_rev += self.blocksize

    def prev_rev(self):
        self.current_rev -= self.blocksize

    def at_end(self) ->bool:
        return (self.current_rev >= self.rev_end)

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
            success = False
            with open(self.state_save_file, 'rb') as f:
                try:
                    self.state = pickle.load(f)
                    success = True
                except:
                    pass
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
    ap.add_argument("-force-update-revision", "-fur", action="store_true", help="Forces the program to grab the latest revision from the repository's \
        changelogs.  This number is where the program will stop pulling revisions, so you may want to use this option if you \
        have not continued pulling in a while...")
    ap.add_argument("--cloneonly", "-c", action="store_true", help="Only clone the earliest revision of the repository.")
    ap.add_argument("--warranty", "-w", action="store_true", help="Show the copyright notice.")
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

def incremental_clone(repository: str, destination: str, revblock: int=1, pullonly: bool=False, cloneonly=False) -> bool:
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
    
    if not cloneonly:
        #we currently have no stop condition... yet...
        if os.path.isdir(destination):
            print("changing cwd to " + destination)
            os.chdir(destination)
        else:
            print("Unable to chdir into " + destination + os.linesep + "It does not exist!")
            return False
        while not state.at_end():
            state.next_rev()
            print(os.linesep + "Pulling revision " + str(state.current_rev) + os.linesep)
            if hgpull(destination, state.current_rev):
                PDATA.save()
                print(os.linesep + "Percent complete: %" + str((state.current_rev * 100) / state.rev_end) + os.linesep)
            else:
                state.prev_rev()
                PDATA.save()
                print(os.linesep + "Creating working copy..." + os.linesep)
                hgupdate()
                break
    return state.at_end()

def show_warranty() -> None:
    print("Stepclone v" + str(VERSION) + """ clones a mercurial repository incrementally.  This can be 
    useful when the entire repository and all its checksums results
    in a clone that takes too long to be practical.

    Copyright (C) 2019  Jonathan Whitlock

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see https://www.gnu.org/licenses/""")

def main(argv):
    print("Stepclone " + str(VERSION) + "  Copyright (C) 2019  Jonathan Whitlock " + os.linesep + "\
    This program comes with ABSOLUTELY NO WARRANTY; for details pass `--warranty\' as one of the program's arguments. " + os.linesep + "\
    This is free software, and you are welcome to redistribute it " + os.linesep + "\
    under certain conditions; pass --warranty for details." + os.linesep + os.linesep)
    if ("--warranty" in argv) or ("-w" in argv):
        show_warranty()
        sys.exit(0)

    arguments = None
    if len(argv) > 1:
        arguments = PARGS.parse_args(argv[1:])
    else:
        PARGS.parse_args(argv) #this will print the appropriate error and exit
    if arguments.warranty:
        show_warranty()
    PDATA.load()
    if arguments.revblock is not None:
        PDATA.state.blocksize = arguments.revblock

    if (PDATA.state.rev_end < 0) or arguments.force_update_revision:
        PDATA.state.rev_end = int(most_recent_rev(arguments.repository))

    return int(incremental_clone(arguments.repository, arguments.folder, PDATA.state.blocksize, arguments.pullonly, arguments.cloneonly))

if __name__ == "__main__":
    sys.exit(main(sys.argv))