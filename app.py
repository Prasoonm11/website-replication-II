from flask import Flask, render_template

# Initialize the Flask app
app = Flask(__name__)

# Define the main route to serve the homepage
@app.route('/')
def home():
    return render_template('index.html')

# This allows you to run the app directly
if __name__ == '__main__':
    app.run(debug=True)