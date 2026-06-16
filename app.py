from flask import Flask, render_template, request
import mysql.connector
import requests

app = Flask(__name__)

# Fetch AWS Metadata (Instance ID and Availability Zone) safely
def get_aws_metadata():
    try:
        # Step 1: Request an IMDSv2 Token (Required by modern AWS security)
        token_url = "http://169.254.169"
        token_headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
        token_response = requests.put(token_url, headers=token_headers, timeout=2)
        token = token_response.text

        # Step 2: Request Instance ID and Availability Zone using the Token
        metadata_headers = {"X-aws-ec2-metadata-token": token}
        
        instance_id = requests.get("http://169.254.169", headers=metadata_headers, timeout=2).text
        az = requests.get("http://169.254.169", headers=metadata_headers, timeout=2).text
        
        return instance_id, az
    except Exception:
        # Fallback values if running locally outside of an AWS EC2 instance
        return "Local-Machine-ID", "local-zone-1a"

# Helper function to connect to your AWS RDS MySQL Instance
def get_db_connection():
    db = mysql.connector.connect(
        host="://amazonaws.com",  # <-- PASTE YOUR RDS ENDPOINT HERE
        user="root",                                  # Your RDS Master Username
        password="password123"                        # Your RDS Master Password
    )
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS web_db")
    cursor.execute("USE web_db")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS web_table (
            id INT AUTO_INCREMENT PRIMARY KEY,
            content VARCHAR(255)
        )
    """)
    return db, cursor

@app.route('/')
def index():
    instance_id, az = get_aws_metadata()
    return render_template('index.html', instance_id=instance_id, az=az)

@app.route('/submit', methods=['POST'])
def submit_data():
    if request.method == 'POST':
        form_input = request.form['user_data']
        instance_id, az = get_aws_metadata()
        
        try:
            db, cursor = get_db_connection()
            query = "INSERT INTO web_table (content) VALUES (%s)"
            cursor.execute(query, (form_input,))
            db.commit()
            
            success_msg = f"🎉 Successfully saved '{form_input}' directly inside AWS RDS Database!"
            cursor.close()
            db.close()
            
        except Exception as e:
            success_msg = f"❌ RDS Connectivity failure: {e}"
            
        return render_template('index.html', message=success_msg, instance_id=instance_id, az=az)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
