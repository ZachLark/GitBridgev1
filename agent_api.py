from flask import Flask
app = Flask(__name__)

@app.route('/agent')
def agent():
    return "Agent Interface for GitBridge"

if __name__ == "__main__":
    app.run(debug=True, port=10002)