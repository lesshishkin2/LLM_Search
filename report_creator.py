from flask import Flask, render_template
from data_tools import load_from_pickle

app = Flask(__name__)


data = load_from_pickle(
    "runs/20250228_124412/questions_with_final_answers.pkl")


@app.route('/')
def index():
    return render_template('index.html', questions=data)


if __name__ == '__main__':
    app.run(debug=True)
