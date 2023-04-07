FROM ubuntu
RUN apt-get update
# For Sql-client
RUN apt-get install mysql-client -y

# For python and related frameworks

RUN apt-get install python3 -y
RUN apt-get install python3-flask -y
RUN apt-get install python3-pymysql -y
RUN apt-get install python3-boto3 -y

COPY . .
EXPOSE 80
# for running application
CMD ["python3","EmpApp.py"]
~                            
