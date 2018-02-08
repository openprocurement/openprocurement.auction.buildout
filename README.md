# openprocurement.auction.buildout
Buildout for OpenProcurement Auction

For build use Makefile
```
make install
```

System requirements (Fedora 27):

* Redis
* Nginx
* python2-systemd
* systemd-devel

For running internal auction test `phantomjs` executable needs to be in `PATH`

English Auction Internal Robot Test
```
bin/auction_test simple
```

Insider Auction Internal Robot Test
```
bin/auction_test insider
```
