import time
import os

while True:
    print("Checking emails...")
    os.system("python mail_reader.py")
    time.sleep(60)  # every 1 minute