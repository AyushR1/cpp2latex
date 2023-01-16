
#!/usr/bin/python3

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import subprocess
import shlex



app = Flask(__name__)

host ="https://cpp2latex.pythonanywhere.com/"
app.config["UPLOAD_FOLDER"] = "/home/instructions/dic/static/dic_temp_files/"

@app.route('/')
def upload_file():
    return render_template('index.html')


@app.route('/display', methods = ['GET', 'POST'])
def save_file():
    if request.method == 'POST':
        input=request.form['code']

        out = input + "Done"

    return render_template('contenthome.html', output=out)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug = True)
