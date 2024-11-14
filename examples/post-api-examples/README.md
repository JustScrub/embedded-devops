# API usage example
This example shows how to use some POST APIs of the Flask app.    
First, update the `APP_ADDR` variable in `call.sh` to the hostname and port of your Flask app, then change the `pass` fields of the .json files to the password of your app. Then call the script as `./call.sh <api-call>`. Feel free to change the contents of the .json files to try your own calls.    
The `<api-call>` argument can be one of:
 - compile
 - invoke
 - lib/install
The Flask app and all dependencies must be installed. Read the `README.md` file at the top of this repo.