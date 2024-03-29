**usage: stepclone.py [-h] [--pullonly] [--revblock [REVBLOCK]]  
                    [-force-update-revision]   [--cloneonly]  
                    repository folder**

*A python utility to automate incrimental mercurial clones for large
repositories.*  
  
positional arguments:  
  **repository**:  The mercurial repository to be cloned or pulled.  
  **folder**: The folder the repository is located. Give it the same name as the folder that hg will create.  
  
optional arguments:  
  **-h, --help**            show this help message and exit  
  
  **--pullonly, -p**        Specifies that the program should skip cloning entirely. This can be used to continue an incremental pull that was interrupted.  
  
  **--revblock [REVBLOCK], -rb [REVBLOCK]** Specifies how many revisions to clone initially or pull each time. Default is 1.  
  
  **-force-update-revision, -fur** Forces the program to grab the latest revision from the repository's changelogs. This number is where the program will stop pulling revisions, so you may want to use this option if you have not continued pulling in a while...  
  
  **--cloneonly, -c** Only clone the earliest revision of the repository.  
