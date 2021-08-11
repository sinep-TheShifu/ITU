# ITU Projekt 2020: README

## Tým: DeusVult!
## Projekt: Automatický vypínač pre desktopovú a webovú aplikáciu

### Súbory

#### (1.) Inštalačný súbor
install.sh 

#### (2.) Licencia
LICENSE

#### (3.) Hlavný súbor serveru
main.py

#### (4.) Readme
README.md


#### (7.) Zdrojové súbory beckend serveru
src  <br />
    &nbsp;&nbsp;&nbsp;- monitor_status.sh  <br />
    &nbsp;&nbsp;&nbsp;- requierements.txt  <br />
    &nbsp;&nbsp;&nbsp;- resourse_monitor.py  <br />
    &nbsp;&nbsp;&nbsp;- shared.py  <br />
    &nbsp;&nbsp;&nbsp;- timer.py  <br /> 
    

#### (8.) Statické súbory pre Web aplikáciu
static  <br />
    &nbsp;&nbsp;&nbsp;-> css  <br />
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- index_style.css  <br />
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- login_style.css  <br />
    &nbsp;&nbsp;&nbsp;- pictures  <br />

#### (9.) Html súbory pre Web aplikáciu
templates  <br />
    &nbsp;&nbsp;&nbsp;- index.html  <br />
    &nbsp;&nbsp;&nbsp;- login.html  <br />

#### (10.) Zdrojové kódy desktopové aplikace
templates  <br />
    &nbsp;&nbsp;&nbsp;- client/main.py  <br />
    &nbsp;&nbsp;&nbsp;- client/src/*  <br />

### Spustenie

#### (1.) Požiadavky
Pre úspšné spustenie je nutné mať nainštalované všetky požiadavky v súbore *requierements.txt*.

Inštalácia požiadavkov pomocou príkazu:  <br />
*pip3 install -r requierements.txt*

#### (2.) Spustenie servera
Spustenie servera:  <br />
*python3 main.py [ip_adresa_rozhraní:port]*  <br />
*Pozn. je nutné mať práva superužívateľa.*  
#### (3.) Instalace
Spuštěním instalačního skriptu install.sh nainstaluje server do složky /root/bin/ShutDownToolServer. A server spustí na portu 60606 na všech rozhraní.
### Desktopová aplikácia
Desktopová aplikace se připojí k serveru na adrese 127.0.0.1 na port 60606. Zdrojové kódy jsou umístěné ve složkách client a client/src. Spuštění aplikace se provede příkazem python3 main.py. Přihlášení k serveru se provádí uživatelským jménem a heslem k účtu na Ubuntu. 

### Webová aplikácia
Použitie webovej aplikácie.

##### (1.) Vzdialený server
Je nutné sa pripojiť na vzdialený server pomocou príkazu:  <br />
*ssh -R 60606:localhost:60606 name@servername*

##### (2.) Spustenie
Spustenie cez webový prehliadač na adrese:  <br />
*localhost:60606* alebo *127.0.0.1:60606*

##### (3.) Prihlásenie a spustenie aplikácie
Po pripojení na vybraný server a spustení aplikácie v prehliadači sa musíte prihlásiť. Po prihlásení sa vám zobrazí stránka na ktorej môžete nastaviť ktoré akcie sa vykonajú a spustiť aplikáciu.
