# BeamIT-Server

This application was created as part of the university lecture "Software Engineering 2" as an exam. It is intended for sharing files, links and text. There are two repositorys for this project, the BeamIT-Server and the BeamIT-Desktop-App (see [Beamit-Desktop-App](https://github.com/SHexplorer/BeamIT-Desktop-App))

The Server is based on python 3.10+ and FastAPI and uvicorn. Requirement for this project was also some automated tests with github actions, so some small tests were implemented (see .github/module-test_and_syntax.yml and test_pwcrypt.py). The code is more or less commented, just look a little bit around. An install script is provided which copys the server to /opt and creates a linux systemd service. The following part is a short description/install/user manual (translated from german):  
<br><br>


The tool consists of at least three components.

- Application on device 1

- server

- Application on device 2, 3, 4, ...


First, the applications must be installed on at least two end devices, since at least two participants are needed for communication. For this purpose, 2 different applications are available which can be downloaded from [Beamit Desktop App](https://github.com/SHexplorer/BeamIT-Desktop-App) and must be installed afterwards:

- Windows application

- Android app: The project team has decided to temporarily stop the development of the Android app, as the originally responsible developer has dropped out of the project. We are working on finding a new person to continue the development of the app.

- Linux app

In order for the devices/participants to communicate with each other, a server is also needed. The Server for this can be downloaded here.


Quick guide:

 1. download and install the corresponding application for device 1
 2. download and install the corresponding application for device 2
	- For other devices download and install the corresponding application
 3. decide which type of server to use
	- Use public server at the following address: Not available any more
	- Set up private server:
		- Install a Debian based server (recommended: Ubuntu 22.04; supporting at least python 3.10+)
		- `git clone https://github.com/SHexplorer/BeamIT-Server.git`
		- `cd BeamIT Server`
		- `chmod +x install.sh`
		- `sudo ./install.sh`
		- for further settings see the installation messages
 4. registration in the application
 5. ready for operation!!!

Add more devices:

 1. download and install the appropriate application.
 Register in the application and specify the server address (public or private) that you want to use.