## Overview
The project is designed to monitor and verify compliance with recommended retail prices by partners on the trading platform https://catalog.onliner.by/.
In case of price discrepancies, emails are sent with a request to correct the prices. As well as reporting violations to the administrator

## Installation

To get started, clone the repository and install the required dependencies.

```bash
git clone https://github.com/STEJKpro/onliner_dumping
cd onliner_dumping
pip install -r requirements.txt
```

## Configuration

1. Rename `config_example.ini` to `config.ini`.

```bash
mv config_example.ini config.ini
```

2. Open `config.ini` and enter your specific configuration details.

## Usage

### Running the Database Administration Panel

To launch the database administration panel, use the following command:

```bash
python -m database_administration.app
```
This comand will start flask server on http://localhost:5000 or http://127.0.0.1:5000


### Running the Main Script

The main script collects information, updates the price list, sends a newsletter, and emails a report to the administrator's email specified in the configuration file.

Run the script with:

```bash
python main.py --admin_email --notify_emails
```
or for more info about options
```bash
python main.py -h
```