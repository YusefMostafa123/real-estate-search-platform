from flask import Flask, render_template, redirect, request, url_for
import time

# Create an instance of the Flask class
app = Flask(__name__)

# Define a route for the homepage ("/")
@app.route("/")
def home():
    return render_template('home.html')

@app.route('/handle_button', methods=['POST'])
def useless_button_handler():
    if 'useless_button' in request.form:
        print("Button was pressed!")
        # Perform server-side logic here
        time.sleep(1)
    return redirect("/")



# Run the application if this script is executed directly
if __name__ == "__main__":
    app.run(debug=True) # debug=True enables debug mode for development
    print("Running from command...")
