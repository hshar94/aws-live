from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

# DBHOST = os.environ.get("DBHOST")
# DBPORT = os.environ.get("DBPORT")
# DBPORT = int(DBPORT)
# DBUSER = os.environ.get("DBUSER")
# DBPWD = os.environ.get("DBPWD")
# DATABASE = os.environ.get("DATABASE")

bucket= custombucket
region= customregion

db_conn = connections.Connection(
    host= customhost,
    port=3306,
    user= customuser,
    password= custompass,
    db= customdb
    
)
output = {}
table = 'employee';

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')

@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com');
@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']
  
    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        
        cursor.execute(insert_sql,(emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-"+str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        
        
        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

            # Save image file metadata in DynamoDB #
            print("Uploading to S3 success... saving metadata in dynamodb...")
        
            
            try:
                dynamodb_client = boto3.client('dynamodb', region_name='us-east-2')
                dynamodb_client.put_item(
                 TableName='employee_image_table',
                    Item={
                     'empid': {
                          'N': emp_id
                      },
                      'image_url': {
                            'S': object_url
                        }
                    }
                )

            except Exception as e:
                program_msg = "Flask could not update DynamoDB table with S3 object URL"
                return str(e)
        
        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    return render_template("GetEmp.html")


@app.route("/fetchdata", methods=['GET','POST'])
def FetchData():
    emp_id = request.form['emp_id']

    output = {}
    select_sql = "SELECT emp_id, first_name, last_name, pri_skill, location from employee where emp_id=%s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql,(emp_id))
        result = cursor.fetchone()

        output["emp_id"] = result[0]
        print('EVERYTHING IS FINE TILL HERE')
        output["first_name"] = result[1]
        output["last_name"] = result[2]
        output["primary_skills"] = result[3]
        output["location"] = result[4]
        print(output["emp_id"])
        dynamodb_client = boto3.client('dynamodb', region_name=customregion)
        try:
            response = dynamodb_client.get_item(
                TableName='employee_image_table',
                Key={
                    'empid': {
                        'N': str(emp_id)
                    }
                }
            )
            image_url = response['Item']['image_url']['S']

        except Exception as e:
            program_msg = "Flask could not update DynamoDB table with S3 object URL"
            return render_template('addemperror.html', errmsg1=program_msg, errmsg2=e)

    except Exception as e:
        print(e)

    finally:
        cursor.close()

    return render_template("GetEmpOutput.html", id=output["emp_id"], fname=output["first_name"],
                           lname=output["last_name"], interest=output["primary_skills"], location=output["location"],
                           image_url=image_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=80,debug=True)
