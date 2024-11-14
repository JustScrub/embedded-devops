from flask import Flask, request, jsonify
from config import *
import subprocess
from tempfile import TemporaryDirectory
import os
from hashlib import sha3_256
import markdown

# flask app with endpoints:
# / - returns the index.html and usage instructions
# /api/v1/ - returns the API documentation
# /api/v1/compile - POST request to compile the code
#      # request body: {"code": "path to git repo", "upload": "true/false wheter to upload to flash or not"}
# /api/v1/upload - POST request to upload the binary to the device
#      # request body: {"bin": "url to binary file"}

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <h1>Embedded Devices DevOps</h1>
    <p><a href="/api/v1/">Documentation</a></p>"""

md_html = None
@app.route('/api/v1/')
def api():
    global md_html
    if md_html is None:
        with open('README.md', 'r') as f:
            md = f.read()
        md_html = markdown.markdown(md)
    return md_html

def run_proc(cmd, print_output=True, **sub_args):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, **sub_args)
    if print_output: print(result.stdout)
    return result.returncode

def auth(pwd):
    pwd = sha3_256((API_SALT + pwd).encode()).hexdigest()
    return pwd == API_TOKEN

def check_req_data(data, *keys):
    return all(k in data for k in keys)

@app.route('/api/v1/compile', methods=['POST'])
def compile():
    data = request.json
    if not check_req_data(data, 'code', 'upload', 'pass'):
        return jsonify({'error': 'Missing parameters'}), 400
    if not auth(data['pass']):
        return jsonify({'error': 'Unauthorized'}), 401
    #return "Compile endpoint is not implemented yet \n" + str(request.json)

    code = data['code']
    upload = data.get('upload', 'false').lower()
    workspace = TemporaryDirectory()

    print(f'Cloning {code} to {workspace.name}')
    # clone the repo
    res = subprocess.run(['git', 'clone', code], cwd=workspace.name, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        return jsonify({'error': 'Failed to clone the repo', 'stdout': res.stdout.decode()}), 400
    
    cloned_repo = os.path.join(workspace.name, os.listdir(workspace.name)[0])
    
    # compile the code using arduino-cli
    print(f'Compiling the code')
    res = subprocess.run([ARDUINO_CLI_PATH, 'compile', '-b', BOARD_FQBN, cloned_repo], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        return jsonify({'error': 'Failed to compile the code', 'stdout': res.stdout.decode()}), 400
    
    # upload the binary to the device
    if upload == 'true':
        print(f'Uploading the binary')
        res = subprocess.run([ARDUINO_CLI_PATH, 'upload', '-b', BOARD_FQBN, '-p', BOARD_PORT, cloned_repo], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if res.returncode != 0:
            return jsonify({'error': 'Failed to upload the binary', 'stdout': res.stdout.decode()}), 400
    
    workspace.cleanup()
    return jsonify({'code': code, 'upload': upload, 'success': True})

@app.route('/api/v1/upload', methods=['POST'])
def upload():
    data = request.json
    if not check_req_data(data, 'bin', 'pass'):
        return jsonify({'error': 'Missing parameters'}), 400
    if not auth(data['pass']):
        return jsonify({'error': 'Unauthorized'}), 401
    #return "Upload endpoint is not implemented yet \n" + str(request.json)

    bin = data['bin']
    workspace = TemporaryDirectory()
    bin_name = f"{workspace.name}/firmware.hex"

    print(f'Downloading {bin} to {workspace.name}')
    # download the binary
    res = subprocess.run(['wget', bin, '-O', bin_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        return jsonify({'error': 'Failed to download the binary', 'stdout': res.stdout.decode()}), 400
    # upload the binary to the device

    print(f'Uploading the binary')
    res = subprocess.run([ARDUINO_CLI_PATH, 'upload', '-b', BOARD_FQBN, '-p', BOARD_PORT, '-i', bin_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        return jsonify({'error': 'Failed to upload the binary', 'stdout': res.stdout.decode()}), 400
    
    workspace.cleanup()
    return jsonify({'bin': bin, 'success': True})

@app.route('/api/v1/FQBN')
def get_FQBN():
    return jsonify({'FQBN': BOARD_FQBN})

# get arduion-cli version
@app.route('/api/v1/version')
def get_version():
    version = subprocess.run([ARDUINO_CLI_PATH, 'version'], stdout=subprocess.PIPE).stdout.decode()
    return jsonify({'version': version})

@app.route('/api/v1/invoke', methods=['POST'])
def invoke():
    if not USE_INVOCATION_API:
        return jsonify({'error': 'Invocation API is disabled'}), 400

    data = request.json
    if not check_req_data(data, 'invocations', "pass"):
        return jsonify({'error': 'Missing parameters'}), 400
    if not auth(data['pass']):
        return jsonify({'error': 'Unauthorized'}), 401
    
    invocations = data['invocations']
    results = []
    for invocation in invocations:
        args = invocation.get('args', [])
        if not args or not isinstance(args, list):
            results.append({
                'args': args,
                'returncode': -1,
                'stdout': 'Invalid arguments: must be list'
            })
            continue
        result = subprocess.run([ARDUINO_CLI_PATH] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        results.append({
            'args': args,
            'returncode': result.returncode,
            'stdout': result.stdout.decode()
        })
    return jsonify({'results': results})

@app.route('/api/v1/lib/install', methods=['POST'])
def install_lib():
    data = request.json
    if not check_req_data(data, 'libraries', 'pass'):
        return jsonify({'error': 'Missing parameters'}), 400
    if not auth(data['pass']):
        return jsonify({'error': 'Unauthorized'}), 401
    
    lib = data['libraries']
    if not isinstance(lib, list):
        return jsonify({'error': 'Invalid libraries parameter: must be list'}), 400
    
    res = subprocess.run([ARDUINO_CLI_PATH, 'lib', 'install'] + lib, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if res.returncode != 0:
        return jsonify({'error': 'Failed to install libraries', 'stdout': res.stdout.decode()}), 400
    return jsonify({'libraries': lib, 'success': True})

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, ssl_context='adhoc')


# Communication example:
# curl -H 'Content-Type: application/json' -d '{"code": "https://github.com/schacon/blink.git", "upload": "true"}' -k -X POST https://localhost:5000/api/v1/compile
