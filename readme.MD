# KanjiLearn - Kanji Learning REST API for Resonite

## Server Setup:
1. Install Python 3
2. Create a virtual environment:
   - On Windows: Run `python -m venv venv` in your project directory
   - On Linux: Run `python3 -m venv venv` in your project directory
3. Activate the virtual environment:
   - On Windows: Run `venv\Scripts\activate`
   - On Linux: Run `source venv/bin/activate`
4. Install the requirements with `pip install -r requirements.txt`
5. Make a copy of `config_example.ini` and rename it to `config.ini`
6. Optional: Open `config.ini` in a text editor and enter your OpenAI API key to the api_key section. 
Change any other options as you see fit. Set `host` to `localhost` if testing locally.
If you want the server to be accessible to the internet, and assuming you've forwarded the port you want to use, set `host` to `0.0.0.0`
7. Run `python main.py` to start the server. The server will be hosted on the host and port you specified in `config.ini`

With the default configuration, you can test the server with Postman by making a GET HTTP request to your server at:
http://localhost:5733/random_kanji/

## Client Setup in Resonite:
1. This public folder contains the client:
`resrec:///U-DingoYabuki/R-9793cb26-f9ac-4eea-b52d-1bafdff8e502`
Copy this URI and paste it into Resonite, and the public folder will spawn. 
The client item is in the folder, named `KanjiLearnClient`. 
2. Spawn the item and navigate to the root of it with your Inspector tool.
3. You will see 2 `DynamicValueVariable<string>` components with VariableNames `Settings/URL` and `Settings/TryConnectionAsUsername`. 
   * `Settings/URL` - Your server's URL
   * `Settings/TryConnectionAsUsername` Not required to be set, but allows you to designate a user who will send requests to the server. You can set this as yourself so others do not have to make API requests. If this field is not set, or is set to a username of a user who is not in the session, API requests will be sent by whoever interacts with the item.


## Webapp:
1. Start the server as described above.
2. run `python start_web_app.py`, which is a frontent that calls the API


## Credits
The `kanji.json` file is from:
https://github.com/davidluzgouveia/kanji-data

