

# KanjiLearn - An OpenAI-Powered Kanji Learning REST API for Resonite

## Server Setup:
1. Install Python 3
2. Install the requirements with `pip install -r requirements.txt`
3. Make a copy of `config_example.ini` and rename it to `config.ini`
4. Open `config.ini` in a text editor and enter your OpenAI API key to the api_key section. 
Change any other options as you see fit. Set `host` to `localhost` if testing locally.
If you want the server to be accessible to the internet, and assuming you've forwarded the port you want to use, set `host` to `0.0.0.0`
5. Run `python main.py` to start the server. The server will be hosted on the host and port you specified in `config.ini`

With the default configuration, you can test the server with Postman by making a GET HTTP request to your server at:
http://localhost:5733/random_kanji/

## Client Setup in NeosVR:
1. This public folder contains the client:
`resrec:///U-DingoYabuki/R-9793cb26-f9ac-4eea-b52d-1bafdff8e502`
Copy this URI and paste it into Neos, and the public folder will spawn. 
The client item is in the folder, named `KanjiLearnClient`. 
2. Spawn the item and navigate to the root of it with your Inspector tool.
3. You will see 2 `DynamicValueVariable<string>` components with VariableNames `Settings/URL` and `and Settings/ClientUserID`. Modify those components' values to match your server's URL and your Neos UserID.

Now your client has been configured. It will only work when you are in a session, and connect to your server, using your OpenAI API key. When other users send prompts, the requests will be sent to your server on your behalf. There is no need for other users to connect to your server.

## Credits
The `kanji.json` file is from:
https://github.com/davidluzgouveia/kanji-data

