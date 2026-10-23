import os
import sqlite3
import datetime
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError, EndpointConnectionError
from config import Config
from database import add_backup_record

def create_local_sqlite_backup():
    """
    Perform an atomic online backup of the SQLite database to the backups/ directory.
    Uses SQLite's online backup API to prevent corruption or table locking.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"hospital_backup_{timestamp}.db"
    backup_path = Config.BACKUP_DIR / backup_filename

    # Source database connection
    src_conn = sqlite3.connect(str(Config.DATABASE_PATH))
    # Destination backup database connection
    dest_conn = sqlite3.connect(str(backup_path))

    with dest_conn:
        src_conn.backup(dest_conn)

    dest_conn.close()
    src_conn.close()

    file_size_kb = round(os.path.getsize(backup_path) / 1024, 2)
    return str(backup_path), backup_filename, file_size_kb

def get_s3_client():
    """
    Initialize boto3 S3 client using the AWS credential chain:
    1. Direct credentials from environment if provided.
    2. EC2 IAM Instance Profile Role (Standard AWS deployment best practice).
    3. Default AWS credentials file ~/.aws/credentials.
    """
    if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
        return boto3.client(
            "s3",
            region_name=Config.AWS_REGION,
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
        )
    else:
        # Relies on EC2 IAM Role or standard AWS environment
        return boto3.client("s3", region_name=Config.AWS_REGION)

def upload_backup_to_s3(file_path, filename):
    """
    Upload a local backup file to Amazon S3.
    Enforces AES256 server-side encryption and private access (no public ACL).
    """
    s3_key = f"{Config.S3_BACKUP_PREFIX.rstrip('/')}/{filename}"
    bucket_name = Config.S3_BUCKET_NAME

    try:
        s3 = get_s3_client()
        # Upload with Server-Side Encryption (AES256) and strictly private permissions
        s3.upload_file(
            Filename=file_path,
            Bucket=bucket_name,
            Key=s3_key,
            ExtraArgs={
                "ServerSideEncryption": "AES256"
            }
        )
        return {
            "success": True,
            "status": "Uploaded",
            "bucket": bucket_name,
            "key": s3_key,
            "message": f"Successfully uploaded to Amazon S3 bucket '{bucket_name}' with AES256 encryption."
        }
    except (NoCredentialsError, PartialCredentialsError):
        return {
            "success": False,
            "status": "Local Only",
            "bucket": bucket_name,
            "key": s3_key,
            "message": "AWS credentials not detected. Saved locally. On EC2, attach an IAM Role to enable automated cloud upload."
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_msg = e.response.get("Error", {}).get("Message", str(e))
        return {
            "success": False,
            "status": "Local Only",
            "bucket": bucket_name,
            "key": s3_key,
            "message": f"AWS S3 error ({error_code}): {error_msg}. Backup saved safely to local disk."
        }
    except EndpointConnectionError:
        return {
            "success": False,
            "status": "Local Only",
            "bucket": bucket_name,
            "key": s3_key,
            "message": f"Could not connect to AWS S3 in region '{Config.AWS_REGION}'. Check internet connectivity. Backup saved locally."
        }
    except Exception as e:
        return {
            "success": False,
            "status": "Local Only",
            "bucket": bucket_name,
            "key": s3_key,
            "message": f"S3 Upload failed: {str(e)}. Backup saved safely to local disk."
        }

def perform_database_backup():
    """
    Complete backup workflow:
    1. Creates atomic SQLite snapshot on disk in backups/ folder.
    2. Attempts S3 upload.
    3. Records backup log in SQLite database.
    """
    backup_path, backup_filename, file_size_kb = create_local_sqlite_backup()
    s3_result = upload_backup_to_s3(backup_path, backup_filename)

    record_id = add_backup_record(
        filename=backup_filename,
        file_size_kb=file_size_kb,
        s3_bucket=s3_result["bucket"],
        s3_key=s3_result["key"],
        status=s3_result["status"],
        message=s3_result["message"]
    )

    return {
        "id": record_id,
        "filename": backup_filename,
        "file_size_kb": file_size_kb,
        "s3_status": s3_result["status"],
        "message": s3_result["message"],
        "is_s3_uploaded": s3_result["success"],
        "bucket": s3_result["bucket"],
        "key": s3_result["key"]
    }

def test_s3_connection():
    """
    Test AWS connection and S3 bucket accessibility.
    Returns diagnostic information for the Settings and Backup views.
    """
    bucket_name = Config.S3_BUCKET_NAME
    region = Config.AWS_REGION
    
    try:
        s3 = get_s3_client()
        # Verify access by checking bucket existence or listing
        s3.head_bucket(Bucket=bucket_name)
        return {
            "connected": True,
            "bucket": bucket_name,
            "region": region,
            "status": "Active & Verified",
            "message": f"Successfully connected to private S3 bucket '{bucket_name}' in region '{region}'."
        }
    except (NoCredentialsError, PartialCredentialsError):
        return {
            "connected": False,
            "bucket": bucket_name,
            "region": region,
            "status": "Local Mode (No AWS Credentials)",
            "message": "Running in local presentation mode. AWS credentials or EC2 IAM Role not detected. Backups will be securely stored on local disk until AWS credentials/role are attached."
        }
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            return {
                "connected": False,
                "bucket": bucket_name,
                "region": region,
                "status": "Bucket Not Found (404)",
                "message": f"AWS credentials are valid, but S3 bucket '{bucket_name}' was not found. Please create this bucket or update the bucket name in settings."
            }
        elif error_code == "403":
            return {
                "connected": False,
                "bucket": bucket_name,
                "region": region,
                "status": "Access Denied (403)",
                "message": f"S3 bucket '{bucket_name}' exists, but current IAM credentials lack s3:ListBucket / s3:PutObject permissions."
            }
        else:
            return {
                "connected": False,
                "bucket": bucket_name,
                "region": region,
                "status": f"AWS Error: {error_code}",
                "message": e.response.get("Error", {}).get("Message", str(e))
            }
    except Exception as e:
        return {
            "connected": False,
            "bucket": bucket_name,
            "region": region,
            "status": "Connection Error",
            "message": str(e)
        }
