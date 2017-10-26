#! bin/python_interpreter

# HOW TO USE:
# run the command:
# ./test.py simple planning && ./test.py simple run
# or
# ./test.py multilot planning && ./test.py multilot run
# or
# ./test.py esco planning && ./test.py esco run
# or
# ./test.py esco_meat planning && ./test.py esco_meat run
# or
# ./test.py esco_meat_multilot planning && ./test.py esco_meat_multilot run

import os
import os.path
import os.path
import datetime
import json
import argparse
import contextlib
import tempfile
from dateutil.tz import tzlocal
from subprocess import check_output
from datetime import datetime, timedelta


PAUSE_SECONDS = timedelta(seconds=120)


PWD = os.path.dirname(os.path.realpath(__file__))
CWD = os.getcwd()
TENDER = {'simple': os.path.join(PWD, 'src/openprocurement.auction.worker/openprocurement/auction/worker/tests/functional/data/tender_simple.json'),
          'multilot': os.path.join(PWD, 'src/openprocurement.auction.worker/openprocurement/auction/worker/tests/functional/data/tender_multilot.json'),
          'esco': 'src/openprocurement.auction.esco/openprocurement/auction/esco/tests/functional/data/tender_esco.json',
          'esco_meat': 'src/openprocurement.auction.esco/openprocurement/auction/esco/tests/functional/data/tender_esco_meat.json',
          'esco_meat_multilot': 'src/openprocurement.auction.esco/openprocurement/auction/esco/tests/functional/data/tender_esco_meat_multilot.json'}

WORKER = {'simple': 'auction_worker',
          'multilot': 'auction_worker',
          'esco': 'auction_esco',
          'esco_meat': 'auction_esco',
          'esco_meat_multilot': 'auction_esco'}


@contextlib.contextmanager
def update_auctionPeriod(path, auction_type):
    with open(path) as file:
        data = json.loads(file.read())
    new_start_time = (datetime.now(tzlocal()) + PAUSE_SECONDS).isoformat()

    if auction_type == 'simple':
        data['data']['auctionPeriod']['startDate'] = new_start_time
    elif auction_type == 'multilot':
        for lot in data['data']['lots']:
            lot['auctionPeriod']['startDate'] = new_start_time

    with tempfile.NamedTemporaryFile(delete=False) as auction_file:
        json.dump(data, auction_file)
        auction_file.seek(0)
    yield auction_file.name
    auction_file.close()


def planning(tender_file_path, worker, auction_id):
    with update_auctionPeriod(tender_file_path,
                              auction_type='simple') as auction_file:
        os.system('{0}/bin/{1} planning {2}'
                  ' {0}/etc/auction_worker_defaults.yaml --planning_procerude partial_db --auction_info {3}'.format(
            CWD, worker, auction_id, auction_file))
    os.system('sleep 3')


def run(tender_file_path, worker, auction_id):
    with update_auctionPeriod(tender_file_path,
                              auction_type='simple') as auction_file:
        check_output('{0}/bin/{1} run {2}'
                     ' {0}/etc/auction_worker_defaults.yaml --planning_procerude partial_db --auction_info {3}'.format(
            CWD, worker, auction_id, auction_file).split())
    os.system('sleep 3')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('auction_type', type=str)
    parser.add_argument('action_type', type=str)

    args = parser.parse_args()

    actions = globals()
    if args.action_type in actions:
        actions.get(args.action_type)(TENDER[args.auction_type], WORKER[args.auction_type], "11111111111111111111111111111111")
