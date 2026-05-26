import datetime
import json
import sqlite3

from flask import Flask, render_template, request, session, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'key'

@app.route('/')
def home():
    return render_template('home.html')

def load_data():
    try:
        with open('data/services.json') as f:
            data = json.load(f)
        with open('data/services.json') as f:
            services = json.load(f)
        return data, services
    except(FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return {}, {}

if __name__ == '__main__':
    app.run(debug=True)