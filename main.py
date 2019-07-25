#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

#  MIT License
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#
#  MIT License
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#
#  MIT License
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#
from __future__ import print_function, unicode_literals

import argparse
import atexit
import os
import pprint
import re
import sys
import webbrowser
from datetime import date
from itertools import groupby, islice

import colorama
import requests
from clint.textui import colored

from devops import custom_repository
from devops.configuration.loader import Loader
from devops.select import select
from devops.work_item_types import WorkItemTypes

configuration = Loader.load_configuration('config.json')
AUTHENTICATION = configuration.authentication.tuple
ORGANIZATION = configuration.project.organization
PROJECT = configuration.project.name
ENDPOINT = f'https://dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis'
GIT_ENDPOINT = f'dev.azure.com/{ORGANIZATION}/{PROJECT}/_git/{PROJECT}'
REPOSITORY_ID = [x['id'] for x in requests.get(f'{ENDPOINT}/git/repositories?api-version=5.0',
                                               auth=AUTHENTICATION).json()['value']
                 if x['name'] == PROJECT][0]
KEY_FUNC = lambda f: f['fields']['System.WorkItemType']

display = False
sourceBranch = sourcePulled = targetBranch = targetPulled = None


def create_title(default_title: str) -> str:
    print('Creating title: ')
    title = default_title
    title = input(f'Please enter a title [{title}]: {colorama.Fore.LIGHTWHITE_EX}') or title
    print(f'\n{colorama.Fore.RESET}Selected title: [{colored.white(title, False, True)}]')
    return title


def create_pull_request(source_branch: str, target_branch: str, title: str, work_items: list, text: str):
    payload = {'sourceRefName': f'refs/heads/{source_branch}',
               'targetRefName': f'refs/heads/{target_branch}',
               'title': title,
               'workItemRefs': [{'id': work_item} for work_item in work_items],
               'description': text}

    print('Sending pull request: ', end='')
    response = requests.post(f'{ENDPOINT}/git/repositories/{REPOSITORY_ID}/pullrequests?api-version=5.0', json=payload,
                             auth=AUTHENTICATION)
    res = response.json()
    if not response.ok:
        print(f'{colored.red("failed")} [StatusCode: {response.status_code}]')
        print(f'Error message: {res["message"]}')
    else:
        print(colored.green('Done'))
        print(f'Opening pull request in the browser: ', end='')
        webbrowser.open(f'{GIT_ENDPOINT}/pullrequest/{res["pullRequestId"]}')
        print(colored.green('Done'))


def create_message(work_items: list):
    msg = 'Sorting commits: '
    print(msg)
    d = {}
    for k, v in groupby(sorted(work_items, key=KEY_FUNC), KEY_FUNC):
        if k in ['User Story', 'Bug', 'Task', 'Change request', 'Defect', 'Issue']:
            d[k] = [{x['id']} for x in v]
            print(f'\t{colored.cyan(f"Nb of {k}: {len(d[k])}")}')
        else:
            print(f'\t{colored.yellow(f"Unhandled key: {k}")}')

    print(f'{colorama.Cursor.UP(len(d.keys()) + 1)}{colorama.Cursor.FORWARD(len(msg))}', end='')
    print(colored.green('Done.'))

    print(f'{colorama.Cursor.DOWN(len(d.keys()))}{colorama.Cursor.BACK(len(msg))}', end='')
    print(f'Generating message', end='')

    text = '# Release notes:\n'
    text += '## From git:\n'
    text += format_text('User stories', 'User Story', d)
    print('.', end='')
    text += format_text('Tasks', 'Task', d)
    print('.', end='')
    text += format_text('Change requests', 'Change request', d)
    print('.', end='')
    text += format_text('Bugs', 'Bug', d)
    print('.', end='')
    text += format_text('Defects', 'Defect', d)
    print('.', end='')
    text = re.sub(r"\n\n---\n\n$", '', text)
    print('. ', end='')
    print(colored.green('Done.'))

    return text


def format_text(title: str, key: str, values: dict) -> str:
    if values is not None and key in values:
        val = '\n'.join([f'#{x}' for x in values[key]])
        return f'### {title}:\n\n{val}\n\n---\n\n'
    else:
        return ''


def send_request(ids: list):
    id_str = ','.join(ids)
    print(f'Sending request for {len(ids)} work items: ', end='')
    response = requests.get(f'{ENDPOINT}/wit/workitems?ids={id_str}&api-version=5.0',
                            auth=AUTHENTICATION)
    if response.ok:
        print(colored.green('Done'))
        return response.json()['value']
    else:
        print(f'{colored.red("Failed")} [Status code: {response.status_code}]')
        pprint.pprint(response.json())

        message = response.json()['message']
        if response.status_code == 404 and 'TF401232' in message:
            print('TF401232: ')
            pprint.pprint(message)
            i = re.findall(r'TF401232:.*\s(\d{3,4})', message)[0]
            print(f'Removing id {i}')
            if len(i) == 0:
                print(f'Error message: {message}')
            ids.remove(i)
            return send_request(ids)
        else:
            print('Unhandled error has occurred in the request:')
            print(f'Response [Json]: ')
            pprint.pprint(response.json())
            print('Work items: ')
            pprint.pprint(id_str.split(","))
            raise RuntimeError('Unhandled error has occurred in the request')


def print_branch(branch_name: str) -> str:
    return f'[{colored.blue(f"{branch_name}", False, True)}]'


def finalize(repo: custom_repository):
    global sourceBranch, targetBranch, sourcePulled, targetPulled
    print(colored.yellow("Script run finished. Cleaning works."))
    if repo is not None:
        repo.reset_index()
        if sourcePulled:
            print(f'Removing branch {colored.blue(f"{sourceBranch}", False, True)} from local: ',
                  end='')
            repo.repo.git.branch(sourceBranch, '-D')
            print(colored.green('Done'))

        if targetPulled:
            print(f'Removing branch {colored.blue(f"{targetBranch}", False, True)} from local: ',
                  end='')
            repo.repo.git.branch(targetBranch, '-D')
            print(colored.green('Done'))


def release(repo: custom_repository):
    global sourceBranch, targetBranch, sourcePulled, targetPulled, display

    sourceBranch, targetBranch = repo.select_src_dest_branch(sourceBranch, targetBranch)

    sourcePulled = repo.check_branch(sourceBranch)
    targetPulled = repo.check_branch(targetBranch)

    ahead = repo.repo.git.rev_list(f'{sourceBranch}..{targetBranch}', '--count', '--no-merges')
    behind = repo.repo.git.rev_list(f'{targetBranch}..{sourceBranch}', '--count', '--no-merges')

    print(f'Diffs {colored.blue(sourceBranch, False, True)}...'
          f'{colored.blue(targetBranch, False, True)}')
    print(f'<Ahead: {colored.cyan(ahead)}, '
          f'Behind: {colored.cyan(behind)}>')

    print('Looking for git logs in the repo: ', end='')
    logs = repo.repo.git.log(f'{targetBranch}..{sourceBranch}', r'--pretty=%D%s%b', '--no-merges')
    print(f'{colorama.Fore.GREEN}Done{colorama.Style.RESET_ALL}')

    print('Treating logs: ', end='')
    str_ids = re.findall(r'#\d{3,4}', logs)
    ids = sorted([work_item_id.replace('#', '') for work_item_id in set(str_ids)])
    n = int(len(ids) / 200) + 1
    print(f'{colorama.Fore.GREEN}Done{colorama.Style.RESET_ALL}')

    work_items = list()
    for i in range(n):
        ids_items = list(islice(ids, i * 200, (i + 1) * 200))
        work_items.extend(send_request(ids_items))

    if display:
        i = 1
    else:
        _, i = select(['Create pull request', 'Display message'], 'What should be Done: ')

    if i == 0:
        message = create_message(work_items)
        title = create_title(f'Release of {date.today().strftime("%d/%m/%Y")}')
        create_pull_request(sourceBranch, targetBranch, title, [f['id'] for f in work_items], message)
    elif i == 1:
        print(f'{message}')
    else:
        print(f'Please chose an other option.')


def close_bug(repo: custom_repository):
    global sourceBranch, targetBranch
    sourceBranch = repo.select_fix_branch()
    print(f'Selected source branch: {sourceBranch}')
    repo.checkout(sourceBranch)
    repo.update_with_remote(sourceBranch)
    work_item_id = re.findall(r'#\d{3,4}', sourceBranch)[0].replace('#', '')

    work_item_list = send_request([work_item_id])
    title = create_title(work_item_list[0]['fields']['System.Title'])
    text = create_message(work_item_list)

    targetBranch, _ = select(['Release', 'master'],
                             'For which branch the pull request should be created: ')
    create_pull_request(sourceBranch, targetBranch, title, work_item_id, text)
    create_pull_request(sourceBranch, 'Develop', title, work_item_id, text)
    print(colored.green(f'Pull requests has been created to Develop and {targetBranch}'))


def print_colorama():
    colorama.init()
    for key, value in dict(vars(colorama.Fore)).items():
        print(f'{value}Fore: {key}')
    for key, value in dict(vars(colorama.Back)).items():
        print(f'{value}Back: {key}')
    sys.exit()


def main():
    global sourceBranch, targetBranch, display
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', type=str, help='path to use', default=os.getcwd())
    parser.add_argument('-r', '--release', action='store_true', help='short way to create a release')
    parser.add_argument('-b', '--base', type=str, help='base branch name used for a release')
    parser.add_argument('-t', '--target', type=str, help='target branch name used in the application')
    parser.add_argument('-d', '--display', action='store_true', help='Display the message to sned')
    args = parser.parse_args()
    cwd = args.path
    sourceBranch = args.base
    targetBranch = args.target
    display = args.display

    colorama.init()
    os.system('cls' if os.name == 'nt' else 'clear')

    repository = custom_repository.CustomRepository(cwd)
    atexit.register(finalize, repository)

    print(f'Repo opened in path: {colored.magenta(f"{cwd}", False, True)}')

    if args.release:
        i = 0
    else:
        _, i = select(['Create release', 'Close bug'], 'Please select an action')

    if i == 0:
        release(repository)
    elif i == 1:
        close_bug(repository)


if __name__ == "__main__":
    main()
