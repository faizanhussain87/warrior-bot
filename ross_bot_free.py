from flask import Flask
import os
app=Flask(__name__)
app.add_url_rule('/', 'home', lambda: 'Ross Bot LIVE')
app.add_url_rule('/health', 'health', lambda: 'OK')
if __name__=='__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
