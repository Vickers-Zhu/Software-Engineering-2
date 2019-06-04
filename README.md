link to the schedule document

https://docs.google.com/spreadsheets/d/17fJVqaTl92F0CEn99tU45TGgTme2Ps5jTW8tHMy8CqI/edit?usp=sharing

#git savoir-vivre

* There is the master branch, and the development branch. Neither can be pushed into (except for siyana, because documentation changes dont mess with code. Just dont push code. Neither will be ever deleted.
* The feature branches. I know it seems natural to have one branch permanently for each of us, but it makes fast-forwarding and updating unnecessarily difficult. Thus, whenever you want to make a new feature, or have no branch to work on yet, you need to branch from development:
	* ```git checkout -b "BRANCH_NAME"```
	* (do things. if you added new files, you need to do ```git add FILE_NAME``` or, ```git add -A``` (however make sure there is no junk in your dir, as it will add everything, like node logs. use ```git reset FILE_NAME``` to revert ```git add```).
	* ```git commit -am "BRANCH_NAME created, stuff done"```
	* ```git push --set-upstream origin BRANCH_NAME```
* Other way (via bitbucket)
	* create branch -> from 'development'
	* ```git pull```. Remote branches dont show up on ```git branch``` command. You need to do ```git branch --all``` to list them.
	* ```git checkout "BRANCH_NAME"```
* Once you are done with your branch and have some finished functionality that you want to add to development branch, and have commited everything:
	* ```git push``` (if nobody messed with your branch remotely, there can't be any problems with this)
	* IMPORTANT: if somebody had made changes to development branch DO NOT DO ```GIT MERGE DEVELOPMENT``` ON YOUR BRANCH. while it will work, it will ruin logs, as all new changes from develop will pop up as new things in your branch. Instead do ```git rebase development```. You will be stopped if any conflicts are found and will need to resolve them manually. If you are unsure how to do that, skip this step - we will deal with it on pull request stage.
	* create a pull request via bitbucket menu. you will see changes you want to introduce lined out, and will be informed of any potential conflicts (that will need to be resolved). Even if your branch is outdated this won't break anything.
	* wait for at least 1 person to review your pull request and merge it to development. you can specify a reviewer, that will send them a notification. do not close a pull request if merge issue are found. pull requests are designed to be WIPs, all consecutive pushes from local will automatically be added to this pull request.
* After a successful pull request, if no work is projected for this branch, delete it, and create it again when you start a new functionality.
* I protected development and master branches from being pushed into, so don't worry - you won't break anything. Only step you can mess anything is by approving a bad pull request.

##usefull commands:
* ```git commit --ammend```
* ```git rebase```
* ```git reset --hard``` (will delete all changes made after the last commit. use with caution. other parameters will let you choose the commit to fallback to.)
* ```git push --force``` (if you run into an issue with your own branch (NOT MASTER OR DEVELOPMENT), this will bypass all merge conflicts and just force-sync bibucket branch with your local
* ```git diff COMMIT_ID1 COMMIT_ID2``` (or just ```git diff HEAD~1```. lists differences between two commits)

**do not use:**
```git merge```. It is a console-only version of a pull request. You could use it for merging two of your local branches, though.