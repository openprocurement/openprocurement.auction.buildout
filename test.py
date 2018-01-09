# Examples of usage:
# ./test.py insider planning --wait_for_result
# ./test.py insider run
# or
# ./test.py insider planning --wait_for_result && ./test.py insider run
#
# ./test.py insider load-testing --auctions_number 10000

import os.path
import json
import argparse
import contextlib
import tempfile
from dateutil.tz import tzlocal
from subprocess import Popen
from datetime import datetime, timedelta
from math import ceil, log10
from time import sleep

PAUSE_SECONDS = timedelta(seconds=120)
PWD = os.path.dirname(os.path.realpath(__file__))
CWD = os.getcwd()

TENDER_DATA = \
    {'insider': {'path': os.path.join(
        PWD, 'src', 'openprocurement.auction.insider', 'openprocurement',
        'auction', 'insider', 'tests', 'functional', 'data',
        'tender_insider.json'),
                 'worker': 'auction_insider',
                 'id': 'NOT DEFINED YET',
                 'config': 'auction_worker_insider.yaml',
                 'tender_id_base': '1'}}


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


def planning(tender_file_path, worker, auction_id, config,
             wait_for_result=False):
    with update_auctionPeriod(tender_file_path,
                              auction_type='simple') as auction_file:
        p = Popen('{0}/bin/{1} planning {2} {0}/etc/{3} --planning_procerude '
                  'partial_db --auction_info {3}'
                  .format(CWD, worker, auction_id, config,
                          auction_file).split())
        if wait_for_result:
            p.wait()
            sleep(1)


def run(tender_file_path, worker, auction_id, config, wait_for_result=False):
    with update_auctionPeriod(tender_file_path,
                              auction_type='simple') as auction_file:
        p = Popen('{0}/bin/{1} run {2} {0}/etc/{3} --planning_procerude '
                  'partial_db --auction_info {3}'
                  .format(CWD, worker, auction_id, config,
                          auction_file).split())
        if wait_for_result:
            p.wait()
            sleep(1)


def load_testing(tender_file_path, worker, config, count, tender_id_base,
                 run_auction=False, wait_for_result=False):
    positions = int(ceil(log10(count)))

    auction_id_template = \
        tender_id_base * (32 - positions) + '{{0:0{}d}}'.format(positions)

    for i in xrange(0, count):
        auction_id = auction_id_template.format(i)
        planning(tender_file_path, worker, auction_id, config, wait_for_result)
        if run_auction:
            run(tender_file_path, worker, auction_id, config, wait_for_result)


def main(auction_type, action_type, tender_file_path='', tender_id_base=None,
         auctions_number=0, run_auction=False, wait_for_result=False):
    actions = globals()
    tender_id_base_local = TENDER_DATA[auction_type]['tender_id_base'] if \
        tender_id_base is None else tender_id_base
    path = tender_file_path or TENDER_DATA[auction_type]['path']
    if action_type in [elem.replace('_', '-') for elem in actions]:
        if action_type == 'load-testing':
            load_testing(
                path,
                TENDER_DATA[auction_type]['worker'],
                TENDER_DATA[auction_type]['config'],
                auctions_number,
                tender_id_base_local,
                run_auction,
                wait_for_result
            )
        else:
            actions.get(action_type)(path,
                                     TENDER_DATA[auction_type]['worker'],
                                     TENDER_DATA[auction_type]['id'],
                                     TENDER_DATA[auction_type]['config'],
                                     wait_for_result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('auction_type', type=str)
    parser.add_argument('action_type', type=str)
    parser.add_argument('--tender_file_path', type=str, nargs='?', default='')
    parser.add_argument('--tender_id_base', type=str, nargs='?', default=None)
    parser.add_argument('--auctions_number', type=int, nargs='?', default=1)
    parser.add_argument('--run_auction', action='store_true')
    parser.add_argument('--wait_for_result', action='store_true')

    args = parser.parse_args()
    main(args.auction_type, args.action_type, args.tender_file_path,
         args.tender_id_base, args.auctions_number, args.run_auction,
         args.wait_for_result)
