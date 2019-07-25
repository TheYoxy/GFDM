#  MIT License
#
#  Copyright (c) 2019. Floryan Simar
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import pprint
from itertools import groupby
from typing import Optional

import requests


class WorkItemTypes:
    workItemList: list

    def __init__(self, endpoint: str, authentication: (str, str), types: list = None):
        if types is None:
            types = ['Task']
        point = f'{endpoint}/wit/reporting/workitemlinks?types={",".join(types)}&api-version=5.0'
        end = False
        workItemList = list()
        i = 0
        while not end:
            response = requests.get(point, auth=authentication)
            i += 1
            workItemList += response.json()['values']
            end = response.json()['isLastBatch']
            point = response.json()['nextLink']

        self.workItemList = sorted([x for x in workItemList],
                                   key=lambda x: x['attributes']['changedDate'])
        pprint.pprint(self.get_parent(3340))

    # Source = parent target = child
    def get_parent(self, item_id: int) -> Optional[int]:
        l = sorted([x for x in self.workItemList if
                    x['attributes']['targetId'] == item_id and x['rel'] == 'System.LinkTypes.Hierarchy'],
                   key=lambda x: (x['attributes']['sourceId'], x['attributes']['changedDate']))

        a = [key for key, value in groupby(l, key=lambda x: x['attributes']['sourceId']) if len(list(value)) % 2 == 1]
        if len(a) == 0:
            return None
        elif len(a) == 1:
            return a[0]
        else:
            print(f'More than one elements for id {item_id}')

    def get_parents(self, item_ids: list) -> list:
        ret = list()
        list_ids = [x for x in item_ids if type(x) is int]
        if len(list_ids) == 0:
            raise ValueError('No ids has been passed to the method')
        for item_id in list_ids:
            parent = self.get_parent(item_id)
            if parent is not None:
                ret += [parent]
        return ret
