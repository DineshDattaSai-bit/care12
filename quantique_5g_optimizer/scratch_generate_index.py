import shutil
import os

# Backup index.html first
shutil.copyfile("templates/index.html", "templates/index_backup.html")
print("Backed up templates/index.html to templates/index_backup.html")
