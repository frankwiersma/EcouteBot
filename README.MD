# 🎙️ EcouteBot 🤖

EcouteBot is a Telegram bot that transcribes voice messages and audio files using the Deepgram API.

## 🌟 Features

- 🗣️ Transcribes voice messages and audio files
- 🌐 Supports multiple languages (currently English 🇬🇧 and Dutch 🇳🇱)
- 🔍 Detects the language of the audio
- 📄 Outputs long transcriptions as text files

## 🛠️ Setup

### Prerequisites

- Docker 🐳
- Docker Compose 🐙

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/EcouteBot.git
   cd EcouteBot
   ```

2. Create a `.env` file in the root directory:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   ```

3. Build and start the Docker container:
   ```
   docker-compose up -d
   ```

## 🚀 Usage

1. Start a chat with your bot on Telegram
2. Use the `/start` command to begin
3. Select your preferred language
4. Send a voice message or audio file
5. Receive the transcription!

## 🔄 Running on Startup

To run EcouteBot on system startup:

1. Create a systemd service file:
   ```
   sudo nano /etc/systemd/system/ecoutebot.service
   ```

2. Add the following content (replace `/path/to/EcouteBot` with your actual path):
   ```
   [Unit]
   Description=EcouteBot Docker Compose Application
   Requires=docker.service
   After=docker.service

   [Service]
   Type=oneshot
   RemainAfterExit=yes
   WorkingDirectory=/path/to/EcouteBot
   ExecStart=/usr/local/bin/docker-compose up -d
   ExecStop=/usr/local/bin/docker-compose down
   TimeoutStartSec=0

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```
   sudo systemctl enable ecoutebot.service
   sudo systemctl start ecoutebot.service
   ```

## 📁 Project Structure

```
EcouteBot/
│
├── app/
│   ├── bot.py
│   ├── config.py
│   └── requirements.txt
│
├── .env
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🛑 Stopping the Bot

To stop the bot:
```
docker-compose down
```

## 🔒 Security Note

Keep your `.env` file secure and never share your API keys publicly!

## 📜 License

This project is licensed under the MIT License.