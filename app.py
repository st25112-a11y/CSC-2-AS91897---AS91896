import datetime
import json
import sqlite3

from flask import Flask, render_template, request, session, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/order_history')
def order_history():
    return render_template('order_history.html')

@app.route('/ordering_menu')
def ordering_menu():
    return render_template('ordering_menu.html')

@app.route('/help')
def help():
    return render_template('help.html')

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