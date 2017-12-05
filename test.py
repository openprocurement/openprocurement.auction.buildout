#! bin/python_interpreter

# BEFORE SCRIPT RUN YOU SHOULD STOP CHRONOGRAPH:
# bin/circusctl stop chronograph

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
from openprocurement.auction.worker.tests.data.data import SIMPLE_TENDER_ID, \
    MULTILOT_TENDER_ID
from openprocurement.auction.esco.tests.data.data import ESCO_TENDER_ID, \
    ESCO_MEAT_TENDER_ID, ESCO_MEAT_MULTILOT_TENDER_ID

PAUSE_SECONDS = timedelta(seconds=120)


PWD = os.path.dirname(os.path.realpath(__file__))
CWD = os.getcwd()


TENDER_DATA = \
    {'simple': {'path': 'src/openprocurement.auction.worker/openprocurement/auction/worker/tests/functional/data/tender_simple.json',
                'worker': 'auction_worker',
                'id': SIMPLE_TENDER_ID},
     'multilot': {'path': 'src/openprocurement.auction.worker/openprocurement/auction/worker/tests/functional/data/tender_multilot.json',
                  'worker': 'auction_worker',
                  'id': MULTILOT_TENDER_ID},
     'esco': {'path': 'src/openprocurement.auction.esco/openprocurement/auction/esco/tests/functional/data/tender_esco.json',
              'worker': 'auction_esco',
              'id': ESCO_TENDER_ID},
     'esco_meat': {'path': 'src/openprocurement.auction.esco/openprocurement/auction/esco/tests/functional/data/tender_esco_meat.json',
                   'worker': 'auction_esco',
                   'id': ESCO_MEAT_TENDER_ID},
     'esco_meat_multilot': {'path': 'src/openprocurement.auction.esco/openprocurement/auction/esco/tests/functional/data/tender_esco_meat_multilot.json',
                            'worker': 'auction_esco',
                            'id': ESCO_MEAT_MULTILOT_TENDER_ID}}


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
        actions.get(args.action_type)(TENDER_DATA[args.auction_type]['path'],
                                      TENDER_DATA[args.auction_type]['worker'],
                                      TENDER_DATA[args.auction_type]['id'])
