APP=~/app;
pkill python3; sleep 3 && cd $APP && nohup python3 driver.py > /dev/null 2>&1 &