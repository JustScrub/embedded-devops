# Arduino UNO DevOps example
This example shows how to use the flask application to continuosly integrate and develop an arduino project. Pay attention to the `.gitlab-ci.yml` file containing a simple GitLab pipeline definition and to the `deploy.sh` script making a POST request to the flask app to compile and upload an arduino project to your Arduino UNO. The variables used in `deploy.sh` are propagated from the pipeline and defined in `.gitlab-ci.yml`.

## Run this example
To run this example:
1. install the Flask app on a node visible from your machine -- install python and pip, run `pip install -r requirements.txt`, install arduino-cli, git and wget and edit the config.py file. You can use the pwdcrypt.py script to generate the token from a password and salt.
2. Plug your Arduino UNO into a USB port of the node -- and change the tty device path in config.py
2. create a GitLab repository and push the contents of this directory in there, then edit the `.gitlab-ci.yml` variables
2. Optionally, push your arduino project as well and change the URL in `.gitlab-ci.yml` to your repo's.
3. run the Flask app using `python3 main.py` command
3. run the GitLab pipeline
If you set up the Flask App correctly, your code should be compiling and uploading to the Arduino. 