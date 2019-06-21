Read and follow **ALL** of these instructions carefully, otherwise I might eat you.

# Setting Up

Clone this repository.
```
git clone https://github.com/fishblowbubbles/devastator.git
cd devastator
```
Switch to the `develop` branch.
```
git checkout develop
```
Create and switch to a local branch.
```
git checkout -b <your-branch-name>
```
Setup your virtual environment (Python 3.6, please) and activate it.
Make sure to run your scripts from the top-level directory.
```
pip install virtualenv
virtualenv venv
source venv/bin/activate
```
When you've finished, leave your virtual environment. Remember to activate it again the next time you work on this project.
```
deactivate
```

# Commit, Merge & Push

Make sure you are working on your local branch. If you're on the remote branch, do not proceed.
```
git status
```
Switch to remote and pull, to make sure you that you are at the tip of the branch.
```
git checkout develop
git pull origin develop
```
Return to your local branch.
```
git checkout <your-branch-name>
```
Update project requirements (from top-level directory). Include your temporary folders in .gitignore, if any.
```
pip freeze > requirements.txt
```
Add your changes.
```
git add <your-file-name>
```
If there are files you don't want to upload yet, stash them away before you commit.
```
git stash
git commit -m <your-commit-message>
```
Rebase, switch to the remote branch, merge and push.
```
git rebase develop
git checkout develop
git merge <your-branch-name>
git push origin develop
```
Remove your local branch if you've no more updates.
```
git branch -d <your-branch-name>
```
If you still have stashed files, pop them and keep working.
```
git checkout <your-branch-name>
git stash pop
```

# Good Practices

1.  Don't work on the remote branch.

2.  You can upload any number of new files, but commits should be at most for files within the same module (i.e. robot, sound, vision). Create separate local branches for each module and commit them individually if possible.

3.  Keep the lifespan of your local branch short. Ideally, 1 per new feature, cleaning it up after your commit and starting afresh (with a pull of the remote branch).

# Project Structure

```
devastator
├── devastator
│   ├── main.py
│   ├── robot
│   │   ├── realsense.py
│   │   ├── respeaker.py
│   │   └── romeo.py
│   ├── sound
│   └── vision
│       ├── darknet
│       ├── darknet.py
│       └── helpers.py
├── docs
├── readme.md
├── requirements.txt
├── scripts
└── tests
    ├── robot
    │   ├── test_realsense.py
    │   ├── test_respeaker.py
    │   └── test_romeo.py
    ├── sound
    │   ├── test_correlation.py
    │   └── test_vokaturi.py
    └── vision
        ├── test_face_detection.py
        └── test_yolo.py
```