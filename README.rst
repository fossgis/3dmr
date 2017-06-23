= 3D Model Repository =
This is a temporary name for the model repository I am developing as part of GSoC.

== Development Server Instructions ==
Firstly, install `python3` and `pip3`. You also need the `virtualenv` python package, you can install it with `sudo pip3 install virtualenv`.
Then, to get a development server running from this repository:

1. Clone the repository, `git clone https://gitlab.com/n42k/3dmr.git`.
2. Move inside the directory that was created, `cd 3dmr`.
3. Set up the virtualenv, `virtualenv .env`.
4. Activate the virtualenv, `source .env/bin/activate`.
5. Install the required packages, `pip3 install -r requirements.txt`.
6. Run the server! `./manage.py runserver 8080`.

Your development server should now be running on port 8080. Note that you will need to make and apply migrations: `./manage.py makemigrations` and `./manage.py migrate`.

== Deployment Instructions ==
TODO
