import mysql.connector
import numpy as np
from PIL import Image
import os
import cv2
import easyocr
import pandas as pd
import streamlit as st
from mysql.connector import errorcode

st.set_page_config(page_title='Business Card', layout='wide')   # Page configuration
st.header('Business Card Image Processing')  # title
col0, col1, col2, col3 = st.columns([3, .1, 2, 3])
data = []
uploaded_file = col0.file_uploader("Select the Image to preprocess",
                                   accept_multiple_files=False, type=["jpg", "jpeg", "png"])


def data_extraction():  # Extracting data from SQL database and executing UPDATE and DROP Query
    tables = []
    if uploaded_file is None:
        conn_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '12345678',
        'database': 'business_cards',
        'port': 3306,
    }
        # Establish a connection
        mydb = mysql.connector.connect(**conn_config)
        cursor = mydb.cursor()
        cursor.execute("SHOW TABLES;")
        result = cursor.fetchall()
        a = [tables.append(j[0]) for j in result]
        cursor = mydb.cursor()
        b = col3.selectbox('Select SQL data to view the details', tables)
        if b is None:
            col3.write('Please upload images to preprocess')
        else:
            try:
                cursor.execute(f"SELECT * FROM business_cards.`{b}`;")
                table_data = cursor.fetchall()
                df = pd.DataFrame(table_data, columns=['Business_card', 'Company_name', 'Contact_person', 'Designation',
                                                   'Address', 'Email', 'Phone_num', 'Website'])
                if not df.empty:
                    df2 = df.T
                    col3.write('Extracted data from image')
                    col3.write(df2)
                    img_path = df['Business_card'].values[0]
                    img = Image.open(img_path)
                    col0.write('Saved image from SQL')
                    col0.image(img)
                    d = col2.selectbox('select option', ('Update_Table', 'Drop_Table'))
                    if d == 'Drop_Table':
                        if col2.button('Confirm to Drop'):
                            cursor.execute(f"""DROP TABLE`{b}`;""")
                            col2.write('Table deleted')
                    elif d == 'Update_Table':
                        new = col2.text_input('New website')
                        cursor.execute(f"""UPDATE `{b}` SET Website ='{new}' WHERE Company_name ='{b}';""")
                    mydb.commit()
                    cursor.close()
                    mydb.close()
                else:
                    col3.write('DataFrame is empty.')

            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_NO_SUCH_TABLE:
                    col3.write(f"Table '{b}' does not exist.")
                else:
                    col3.write(f"Error: {err}")


data_extraction()


def data_processing():  # Uploaded image and Preprocessed image viewing

    if uploaded_file is not None:
        file_path = os.path.join("temp", uploaded_file.name)
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, 1)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, None, fx=1.8, fy=1.8, interpolation=cv2.INTER_LINEAR)
        threshold = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        return image, threshold, file_path
    else:
        return None, None, None


image, threshold, file_path = data_processing()


def data_creation():    # extracting data from processed image
    data.append(file_path)
    with col0:
        if image is not None:
            st.write("Uploaded Image")
            st.image(image)
            col3.write("Processed Image")
            col3.image(threshold)
            reader = easyocr.Reader(['en'])
            out = reader.readtext(threshold)
            col2.header("Extracted Data")
            for i in out:
                data.append(i[1])
                col2.write(i[1])
data_creation()

try:
    def data_insertion():   # Uploading extracted data to sql database
        if uploaded_file is not None:
            if col2.button("Click to upload to SQL"):
                col2.write("Uploaded to SQL")
                df = pd.DataFrame({'Data': data})
                df1 = df.T
                df1 = df1.reset_index(drop=True)
                df1.columns = ['Business_card', 'Company_name', 'Contact_person', 'Designation', 'Address',
                               'Email', 'Phone_num', 'Website']
                conn_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '12345678',
        'database': 'business_cards',
        'port': 3306,
    }
                mydb = mysql.connector.connect(**conn_config)
                cursor = mydb.cursor()
                a = data[1]
                cursor.execute(f"DROP TABLE IF EXISTS `{a}`")
                cursor.execute(
                        f"CREATE TABLE `{a}`( Business_card VARCHAR(500), Company_name VARCHAR(255), "
                        f"Contact_person VARCHAR(255),Designation VARCHAR(255),Address VARCHAR(500), "
                        f"Email VARCHAR(255), Phone_num VARCHAR(500), Website VARCHAR(255))")

                sql1 = f"INSERT INTO `{a}`(Business_card, Company_name, Contact_person, Designation, Address, " \
                       f"Email, Phone_num, Website) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

                val = (data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7])

                cursor.execute(sql1, val)

                mydb.commit()
                cursor.close()
                mydb.close()

    data_insertion()

except Exception as e:
    print("Extracting Business Card Data with OCR")