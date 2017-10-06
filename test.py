#!bin/python
import os
import os.path
import os.path
import datetime
import json
import sys
import argparse
import contextlib
import tempfile
from dateutil.tz import tzlocal
from subprocess import check_output


PWD = os.path.dirname(os.path.realpath(__file__))
CWD = os.getcwd()
TENDER = os.path.join(PWD, 'src/openprocurement.auction.insider/openprocurement/auction/insider/tests/functional/data/tender_insider.json')
WORKER = 'auction_insider'
CONFIG = 'auction_worker_insider.yaml'


@contextlib.contextmanager
def update_auctionPeriod(path, auction_type):
    with open(path) as file:
        data = json.loads(file.read())
    new_start_time = (datetime.datetime.now(tzlocal()) + datetime.timedelta(seconds=20)).isoformat()
    data['data']['auctionPeriod']['startDate'] = new_start_time
    with tempfile.NamedTemporaryFile(delete=False) as auction_file:
        json.dump(data, auction_file)
        auction_file.seek(0)
    yield auction_file.name
    auction_file.close()


def planning(tender_file_path, auction_id):
    with update_auctionPeriod(tender_file_path, auction_type='simple') as auction_file:
        os.system('{0}/bin/{1} planning {2}'
                     ' {0}/etc/{3} --planning_procerude partial_db --auction_info {4}'.format(CWD, WORKER,
                                                                                                  auction_id, CONFIG,
                                                                                                  auction_file))
    os.system('sleep 3')

def run(tender_file_path, auction_id):
    with update_auctionPeriod(tender_file_path, auction_type='simple') as auction_file:
        check_output('{0}/bin/{1} run {2}'
                     ' {0}/etc/{3} --planning_procerude partial_db --auction_info {4}'.format(CWD, WORKER,
                                                                                                  auction_id, CONFIG,
                                                                                                  auction_file).split())
    os.system('sleep 3')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('type', type=str)

    args = parser.parse_args()
    actions = globals()
    if args.type in actions:
        actions.get(args.type)(TENDER, "11111111111111111111111111111111")
