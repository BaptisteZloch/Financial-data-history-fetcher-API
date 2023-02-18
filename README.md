# Crypto Historical Data Fetcher
This project is an API that allow you to get crypto history from KuCoin Exchange. No mater the timeframe, you are not limited to 1500 records per call. The fetch operation is done using timestamp windowing and multithreading. <br>
With that tool you can have a lot of data for backtesting your strategies, training you Machine Learning models or even discover Data Science.<br><br>
The API is in Python with Fast API and uses the KuCoin API SDK.

# Setting up the project
## With Containers
### Docker compose 
First clone the project :
```bash
git clone https://github.com/BaptisteZloch/Financial-data-history-fetcher-API.git
```
The docker compose file in already ready to and build and launch the app however you can change the volume, network and environnement variables parts.
Run the building process and run the project just execute :
```bash
docker compose up --build
```
### Kubernetes
**Soon read**

## Without containers
First clone the project :
```bash
git clone https://github.com/BaptisteZloch/Financial-data-history-fetcher-API.git
```
Then install all the dependencies 
```bash
poetry install
```
To conclude execute this command to run the API :
```bash
poetry run start
```