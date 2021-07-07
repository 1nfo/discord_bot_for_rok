ssh ec2 "rm -rf app && mkdir app"
scp -r ./*.py ./goldbot ./models ./settings ./transactions ./etl ./run.sh ubuntu@ec2:~/app/
