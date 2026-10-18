code="from flask import Flask;import os,threading,time;app=Flask(__name__)\n@app.route('/')\ndef home():\n return 'Ross Bot LIVE'\n@app.route('/health')\ndef health():\n return 'OK'\nif __name__=='__main__':\n port=int(os.environ.get('PORT',10000));app.run(host='0.0.0.0',port=port)\n"
exec(code)
