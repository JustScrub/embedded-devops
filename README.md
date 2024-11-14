# Embedded Devices DevOps
Project for compiling and uploading embedded device code with the `arduino-cli` command from remote places. The host running this project must have a embedded device connected to it via Serial Port (usually over USB). The concrete device is specified by its FQBN string in the config file.

The project contains a Flask app with exposed API and password hashing utility.

## INSTALL and RUN
On your node running the Flask app, do the following:

1. intall python3 and pip, optionally in a virtual environment
1. copy the `main.py`, `config.py` and `requirements.txt` files on the node (or clone this repo)
1. run `pip install -r requirements.txt`
1. install arduino-cli, git and wget
1. edit the `config.py` file to match your configuration
     - use the `pwdcrypt.py` tool to generate the token from your password and salt
1. run `python3 main.py` 

Alternatively, browse the `ansible` directory, change the node IP and all variables and use ansible to provision the flask app onto your node.

<b>NOTE:</b> it may be neccessary to allow the port you plan to run your Flask app on in the firewall, e. g. using ufw: `ufw allow <port>`

## Embedded Devices DevOps app
The Embedded Devices DevOps (EDD) app is a Flask app that exposes APIs accessed via POST or GET requests. The APIs use JSON both for requests and replies.    
Since some POST APIs are security-critical, they are protected with a password.    
The application communicates over HTTPS with ad-hoc certificates, meaning the communication is encrypted, but the server cannot be verified, hence "insecure" connection is required in most cases.    
The recommended way to post a request is with the `curl` utility:


    curl -H 'Content-Type: application/json' -d '{"code": "https://github.com/schacon/blink.git", "upload": "true", "pass": "password"}' -k -X POST https://localhost:5000/api/v1/compile


The `-k` flag or the `--insecure` flag tell `curl` not to verify the certificate.

The Flask server can be configurated with the `config.py` file. This file contains some python variables:

 - BOARD_FQBN: the FQBN string of the device currently connected to the host machine
    - code for this device only must be provided
 - BOARD_PORT: the name of the serial port as exposed by the operating system
 - HOST, PORT: the IP / DNS name and TCP port the server will be listening on
 - API_TOKEN: sha3-256 hexdigest of salt and password as returned by the `pwdcrypt.py` utility (see [below](#pwdcrypt))
    - the password is used to access the API
 - API_SALT: salt prepended to the password before digesting
 - USE_INVOCATION_API: whether to enable the invoke API (see below)

The description of happy-day scenarios of APIs follows. For erroneous calls, consult the [Error handling](#errhand) section.

### Upload API
The upload API uploads a remotely located binary file to the device's flash memory.    
The JSON parameters are:

 - bin: URL to binary file from where it will be downloaded (using `wget`)
 - pass: the password (in plaintext)
    - ssl will encrypt it

On success, returns json with the specified bin and `"success": true`.

Example request using curl:

    curl -H 'Content-Type: application/json' -d '{"bin": "https://url/to/binary", "pass": "password"}' -k -X POST https://localhost:5000/api/v1/upload


Example success response:

    {"bin": "https://url/to/binary", "success": true}


### Compile API
The compile API tries to compile a git repo and if succeeded, optionally uploads it to the device's flash memory. The compiled binary and all other files created during the process will be deleted after the call to this API.    
The git repo MUST have a `.ino` file with the same name as the repo (e.g. the "https://github.com/schacon/blink.git" has a `blink.ino` file). This is the main code file of the arduino "sketch".    
The JSON parameters are:

 - code: a path to a git repository as given to the `git clone` command
 - upload: true / false wheter to upload compiled project to the device
    - default: false
 - pass: the password (in plaintext)
    - ssl will encrypt it

On success, returns the specified code and upload fields with success indication.

Example request using curl:

    curl -H 'Content-Type: application/json' -d '{"code": "https://github.com/schacon/blink.git", "upload": "true", "pass": "password"}' -k -X POST https://localhost:5000/api/v1/compile


Example success response:

    {"code": "https://github.com/schacon/blink.git", "upload": "true", "success": true}


### Library APIs
APIs handling arduino libraries, based at `/api/v1/lib/`.
#### Install Library API
POST API for installing libraries.    
JSON structure:    

    {
       "pass": "app password in plaintext",
       "libraries": ["library 1", "library 2", ...]
    }
    

On success, returns the specified libraries and success indicator.

Example request:


    curl -H 'Content-Type: application/json' -d '{"pass": "password", "libraries": ["Time", "LiquidCrystal I2C"]}' -k -X POST https://localhost:5000/api/v1/lib/install


Example success response:

   {"libraries": ["Time", "LiquidCrystal I2C"], "success": true}


### Invoke API
The invoke API invokes the `arduino-cli` utility with the provided arguments in JSON format. The format is as follows:    

    {
       "pass": "app password in plaintext",
       "invocations": [
          {
             "args": ["arg1", "arg2", ...]
          },
          ...
       ]
    }


Fields explanation:

 - pass: the password in plaintext, encrypted via SSL
 - invocations: list of JSON objects representing individual invocations of the `arduino-cli` utility
   - args: list of arguments to the `arduino-cli` utility, without `arduino-cli` as the first argument!

Returns JSON with results of each invocation (success or error):

    {
       "results": [
          {
             "args": ["arg1", "arg2", ...], //the passed arguments
             "returncode": x, //integer with the return code of the invocation, 0 = success
             "stdout": "stdout and stderr of the invocation combined",
          },
          ...
       ]
    }


For security reasons, this API can be completely disabled via the USE_INVOCATION_API parameter in `config.py`.    
Example request:    

    curl -H 'Content-Type: application/json' -d '{"pass": "password", "invocations": [ { "args": ["lib", "install", "Servo"] }, { "args": ["config", "dump"] } ] }' -k -X POST https://localhost:5000/api/v1/invoke


### FQBN API
The FQBN GET API returns JSON containing the FQBN string of the currently plugged device    
Example response: `{"FQBN": "arduino:avr:uno"}`    
Example request:     

    curl -k https://localhost:5000/api/v1/FQBN


### Version API
Get the version of arduino-cli installed. Returns the literal output of the `arduino-cli version` command.    
Example response: `{"version": "arduino-cli  Version: 0.35.3 Commit: 95cfd654 Date: 2024-02-19T13:24:25Z"}`    
Example request:    

    curl -k https://localhost:5000/api/v1/version


### <a name="errhand"></a> Error Handling
Some APIs may end with error. In such case, JSON is returned in the format:    

    { "error": "Error description"}


The errors may arise due to unprovided mandatory parameters (e.g. `code` parameter to the compile API) or failed authentication (if the password didn't transalte to correct hash). Other errors may be caused by failed subprocess call (e.g. wget, git or arduino-cli). In such case, the JSON format also includes the `stdout` field:

    { "error": "Error description", "stdout": "subprocess stdout + stderr"}


## <a name="pwdcrypt"></a> Password hash utility
For conveniece, the script `pwdcrypt.py` takes one command-line argument, which is a password, salts it with the API_SALT from `config.py` and hashes it. The output is printed out and can be used as the API_TOKEN field in `config.py`. Alternatively, you can pass the salt as the second argument.
