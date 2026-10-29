import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

try:
    connection = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "chess_analytics"),
        port=int(os.getenv("MYSQL_PORT", "3306"))
    )

    if connection.is_connected():
        print("Connected to chess_analytics successfully!")

        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM games")
        print("Current games in table:", cursor.fetchone()[0])

        cursor.close()
        connection.close()

except mysql.connector.Error as error:
    print("MySQL connection failed:", error)
