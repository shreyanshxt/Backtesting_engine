---
description: Push code to GitHub with rebase
---
1. Stage all changes
   `git add .`

2. Commit changes (using a default message if one isn't provided, or prompt)
   `git commit -m "Update codebase"`

3. Pull latest changes from remote with rebase to avoid conflicts
   `git pull origin main --rebase`

4. Push to remote
   `git push -u origin main`
