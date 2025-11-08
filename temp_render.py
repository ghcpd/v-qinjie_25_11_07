from flask import Flask, render_template_string
app = Flask(__name__)
with app.app_context():
    print(render_template_string('<h1>Hello {{7*7}}</h1>'))
