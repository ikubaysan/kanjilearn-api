import os
import configparser

class Config:
    def __init__(self, config_file_path: str):
        self.config_file_path = config_file_path
        if not os.path.exists(self.config_file_path):
            raise Exception(f"Config file not found at {self.config_file_path}")
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file_path)

        self.openai_api_key = self.config['openai_api_client']['api_key']
        self.openai_base_url = self.config['openai_api_client']['base_url']
        self.openai_path = self.config['openai_api_client']['path']
        self.openai_model = self.config['openai_api_client']['model']
        self.openai_max_response_tokens = int(self.config['openai_api_client']['max_response_tokens'])
        self.openai_temperature = float(self.config['openai_api_client']['temperature'])
        self.openai_max_prompt_chars = int(self.config['openai_api_client']['max_prompt_chars'])

        self.google_api_key = self.config['google_api_client']['api_key']
        self.google_model = self.config['google_api_client']['model']

        self.whitelist_enabled = self.config['server']['whitelist_enabled'].lower() == 'true'
        self.whitelist = [item.strip() for item in self.config['server']['whitelist'].split(',') if self.whitelist_enabled]

        self.sample_sentence_count = int(self.config['server']['sample_sentence_count'])
        self.min_seconds_between_requests_per_user = float(self.config['server']['min_seconds_between_requests_per_user'])
        self.min_seconds_between_requests_per_user = self.min_seconds_between_requests_per_user if self.min_seconds_between_requests_per_user > 0 else 0

        self.public_hostname = self.config['server']['public_hostname'] # Eg http://subdomain.example.com
        self.private_hostname = self.config['server']['private_hostname'] # Eg http://localhost
        self.port = int(self.config['server']['port'])

        self.max_chars_per_audio_url = int(self.config['server']['max_chars_per_audio_url'])

        self.quiz_max_chars_per_answer = int(self.config['quiz']['max_chars_per_answer'])
        self.quiz_potential_answers_count = int(self.config['quiz']['potential_answers_count'])
        self.quiz_max_chars_per_kanji_info_section = int(self.config['quiz']['max_chars_per_kanji_info_section'])


    def to_dict(self):
        return {
            'openai_api_key': self.openai_api_key,
            'openai_base_url': self.openai_base_url,
            'openai_path': self.openai_path,
            'openai_model': self.openai_model,
            'openai_max_response_tokens': self.openai_max_response_tokens,
            'openai_temperature': self.openai_temperature,
            'openai_max_prompt_chars': self.openai_max_prompt_chars,
            'google_api_key': self.google_api_key,
            'google_model': self.google_model,
            'whitelist_enabled': self.whitelist_enabled,
            'whitelist': self.whitelist,
            'sample_sentence_count': self.sample_sentence_count,
            'min_seconds_between_requests_per_user': self.min_seconds_between_requests_per_user,
            'public_hostname': self.public_hostname,
            'private_hostname': self.private_hostname,
            'port': self.port,
            'max_chars_per_audio_url': self.max_chars_per_audio_url
        }