
# import libraries
import sys
import numpy as np
from PIL import Image
from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from sqlite3 import Error

np.set_printoptions(threshold=sys.maxsize)

def create_connection():
    conn = None;
    try:
        conn = sqlite3.connect('users.db')
        print(f'successful connection to sqlite version {sqlite3.version}')
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL)''')
        print("Table created successfully")
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
create_connection()

users = {}


# encoding function
def Encode(src, message, dest):
    img = Image.open(src, 'r')
    width, height = img.size
    array = np.array(list(img.getdata()))

    if img.mode == 'RGB':
        n = 3
    elif img.mode == 'RGBA':
        n = 4

    total_pixels = array.size//n

    
    b_message = ''.join([format(ord(i), "08b") for i in message])
    req_pixels = len(b_message)

    if req_pixels > (total_pixels * 3):
        return "ERROR: Need larger file size"

    else:
        index=0
        for p in range(total_pixels):
            for q in range(0, 3):
                if index < req_pixels:
                    array[p][q] = int(bin(array[p][q])[2:9] + b_message[index], 2)
                    index += 1

        array=array.reshape(height, width, n)
        enc_img = Image.fromarray(array.astype('uint8'), img.mode)
        enc_img.save(dest)
        return "Image Encoded Successfully"


# decoding function
def Decode(src):
    img = Image.open(src, 'r')
    array = np.array(list(img.getdata()))

    if img.mode == 'RGB':
        n = 3
    elif img.mode == 'RGBA':
        n = 4

    total_pixels = array.size//n

    hidden_bits = ""
    for p in range(total_pixels):
        for q in range(0, 3):
            hidden_bits += (bin(array[p][q])[2:][-1])

    hidden_bits = [hidden_bits[i:i+8] for i in range(0, len(hidden_bits), 8)]

    message = ""
    for i in range(len(hidden_bits)):
        message += chr(int(hidden_bits[i], 2))
        

    
    return message

# initialize Flask app
app = Flask(__name__)
app.secret_key = 'my_secret_key'

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        query = "INSERT INTO users (username, password) VALUES (?, ?)"
        c.execute(query, (username, password))
        conn.commit()
        c.close()
        conn.close()
        return redirect(url_for('login'))
    else:
        return render_template('signup.html')


# login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        query = "SELECT * FROM users WHERE username = ? AND password = ?"
        c.execute(query, (username, password))
        result = c.fetchone()
        c.close()
        conn.close()
        if result:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid username or password')
    else:
        return render_template('login.html')

        
# home page
@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html')
    else:
        return redirect(url_for('login'))
# encoding page
@app.route('/encode')
def encode():
    if 'username' in session:
        return render_template('encode.html')
    else:
        return redirect(url_for('login'))


# decoding page
@app.route('/decode')
def decode():
    if 'username' in session:
        return render_template('decode.html')
    else:
        return redirect(url_for('login'))
# encode function
@app.route('/do_encode', methods=['POST'])
def do_encode():
    if 'username' in session:
        src = request.files['source-image']
        message = request.form['message']
        dest = request.form['destination-image']
        src.save('src.png')
        result = Encode('src.png', message, dest)
        return render_template('result.html', result=result)
    else:
        return redirect(url_for('login'))

# decode function
@app.route('/do_decode', methods=['POST'])
def do_decode():
    if 'username' in session:
        src = request.files['source-image']
        src.save('src.png')
        result = Decode('src.png')
        return render_template('result.html',result=result)
    else:
        return redirect(url_for('login'))
        
# logout function
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
