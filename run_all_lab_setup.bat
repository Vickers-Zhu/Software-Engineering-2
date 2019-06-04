start cmd.exe /c C:\Anaconda3\python.exe Scripts/server/server.py --port=9997

start cmd.exe /c C:\Anaconda3\python.exe Scripts/gm_server.py --port 9997
powershell -command "Start-Sleep -s 2"

start cmd.exe /c C:\Anaconda3\python.exe  Scripts/bot_server.py --port 9997 
start cmd.exe /c C:\Anaconda3\python.exe  Scripts/bot_server.py --port 9997
start cmd.exe /c C:\Anaconda3\python.exe  Scripts/bot_server.py --port 9997
start cmd.exe /c C:\Anaconda3\python.exe  Scripts/bot_server.py --port 9997 