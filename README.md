# HW1_42

Required libraries: tweepy, pyaudio, ibm_watson, datetime, argparse, pickle, socket, cryptography, hashlib

#Overview

This assignment contains a client installation, and server installation. 

Client:
After command-line initialization with server info, the client Pi will monitor Twitter for valid posts, which contain a tag unique to this team and assignment, #ECE4564T20. Upon receiving a valid Twitter post, the client Pi will take the question from the Twitter post and encrypt it, creating a checksum and sending the encrypted payload to the server Pi. It will then wait for a response from the server. Upon receiving an answer payload, the client will verify its checksum, decrypt the payload, and send the enclosed answer to IBM Watson to receive text to speech audio of the question, which is then played aloud. 

Server:
The server installation, upon initialization, waits to receive a question payload from the client installation. Upon this event, the checksum is verified and the question decrypted. The question is sent to IBM Watson, and text to speech audio is returned and played. Additionally, the question is sent to Wolfram Alpha, and the returned answer transformed into an encrypted answer payload which is returned to the client Pi.

#Initialization procedures

Client:
The client is initialized within the command line in the following format:
python3 client.py -sip <SERVER_IP> -sp <SERVER_PORT> -z <SOCKET_SIZE>

For example, with a server IP of 192.168.1.134, a server port of 4444, and a socket size of 1024, initialization would be as follows:
python3 client.py -sip 192.168.1.134 -sp 4444 -z 1024 

Server:
Server initialization is don in the command line as in the below format:
python3 server.py -sp <SERVER_PORT> -z <SOCKET_SIZE>

So, with the above example values, initialization would look like:
python3 server.py -sp 4444 -z 1024

#Other Requirements
No API keys or URLs are hardcoded into the client or server files. These must be provided in separate Python files, named ClientKeys.py and ServerKeys.py.