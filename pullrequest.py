import atexit
import os
import pprint
import re
import sys
import webbrowser
import colorama
import requests

from datetime import date
from itertools import groupby, islice
from pick import pick
from devops.configuration.loader import load_configuration
import CustomRepository

configuration = load_configuration('config.json')
AUTHENTICATION = configuration.authentication.tuple
ORGANIZATION = configuration.project.organization
PROJECT = configuration.project.name
ENDPOINT = f'https://dev.azure.com/{ORGANIZATION}/{PROJECT}/_apis'
GIT_ENDPOINT = f'dev.azure.com/{ORGANIZATION}/{PROJECT}/_git/{PROJECT}'
REPOSITORY_ID = [x['id'] for x in requests.get(f'{ENDPOINT}/git/repositories?api-version=5.0',
                                               auth=AUTHENTICATION).json()['value'] if x['name'] == PROJECT][0]
KEY_FUNC = lambda f: f['fields']['System.WorkItemType']

sourceBranch = sourcePulled = targetBranch = targetPulled = None


def create_pull_request(source_branch: str, target_branch: str, work_items: list, text: str):
    print('Creating pull request')
    title = f'Release of {date.today().strftime("%d/%m/%Y")}'
    title = input(f'Please enter a title [{title}]: {colorama.Fore.LIGHTWHITE_EX}') or title
    print(f'\n{colorama.Fore.RESET}Selected title: ({title})', end='')

    payload = {'sourceRefName': f'refs/heads/{source_branch}',
               'targetRefName': f'refs/heads/{target_branch}',
               'title': title,
               'workItemRefs': map(lambda work_item: {'id': work_item}, work_items),
               'description': text}

    print('Sending pull request: ', end='')
    response = requests.post(f'{ENDPOINT}/git/repositories/{REPOSITORY_ID}/pullrequests?api-version=5.0', json=payload,
                             auth=AUTHENTICATION)
    res = response.json()
    if not response.ok:
        print(f'{colorama.Fore.RED}Failed{colorama.Fore.RESET} [StatusCode: {response.status_code}]')
        print(f'Error message: {res["message"]}')
    else:
        print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')
        print(f'Opening pull request in the browser: ', end='')
        webbrowser.open(f'https://dev.azure.com/{ORGANIZATION}/_git/{PROJECT}/pullrequest/{res["pullRequestId"]}')
        print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')


def create_message(work_items: list, display: bool = False):
    msg = 'Sorting commits: '
    print(msg)
    d = {}
    for k, v in groupby(sorted(work_items, key=KEY_FUNC), KEY_FUNC):
        v = list(map(lambda x: x['id'], list(v)))
        if k in ['User Story', 'Bug', 'Task', 'Change request', 'Defect', 'Issue']:
            d[k] = v
            print(f'\t{colorama.Fore.CYAN}Nb of {k}: {len(v)}{colorama.Fore.RESET}')
        else:
            print(f'\t{colorama.Fore.YELLOW}Unhandled key: "{k}"{colorama.Fore.RESET}')

    print(f'{colorama.Cursor.UP(len(d.keys()) + 1)}{colorama.Cursor.FORWARD(len(msg))}', end='')
    print(f'{colorama.Fore.GREEN}Done.{colorama.Fore.RESET}')

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
    print(f'{colorama.Fore.GREEN}Done.{colorama.Fore.RESET}')

    return text


def format_text(title: str, key: str, values: dict) -> str:
    if values is not None and key in values:
        val = '\n'.join(map(lambda x: f'#{x}', values[key]))
        return f'''### {title}:

{val}

---

'''
    else:
        return ''


def send_request(ids: list):
    id_str = ','.join(ids)
    print(f'Sending request for {len(ids)} work items: ', end='')
    response = requests.get(f'{ENDPOINT}/wit/workitems?ids={id_str}&api-version=5.0',
                            auth=AUTHENTICATION)
    if response.ok:
        print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')
        return response.json()['value']
    else:
        print(f'{colorama.Fore.RED}Failed{colorama.Fore.RESET} [Status code: {response.status_code}]')
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
    return f'[{colorama.Fore.LIGHTBLUE_EX}{branch_name}{colorama.Fore.RESET}]'


def finalize(repo: CustomRepository):
    global sourceBranch, targetBranch, sourcePulled, targetPulled
    print(f'\n\n{colorama.Fore.YELLOW}Script run finished. Cleaning works.{colorama.Fore.RESET}')
    if repo is not None:
        repo.reset_index()
        if sourcePulled:
            print(f'Removing branch {colorama.Fore.LIGHTBLUE_EX}{sourceBranch}{colorama.Fore.RESET} from local: ',
                  end='')
            repo.repo.git.branch(sourceBranch, '-D')
            print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')

        if targetPulled:
            print(f'Removing branch {colorama.Fore.LIGHTBLUE_EX}{targetBranch}{colorama.Fore.RESET} from local: ',
                  end='')
            repo.repo.git.branch(targetBranch, '-D')
            print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')


def release(repo: CustomRepository):
    global sourceBranch, targetBranch, sourcePulled, targetPulled

    sourceBranch, targetBranch = repo.select_src_dest_branch()

    sourcePulled = repo.check_branch(sourceBranch)
    targetPulled = repo.check_branch(targetBranch)

    ahead = repo.repo.git.rev_list(f'{sourceBranch}..{targetBranch}', '--count', '--no-merges')
    behind = repo.repo.git.rev_list(f'{targetBranch}..{sourceBranch}', '--count', '--no-merges')

    print(f'Diffs {colorama.Fore.LIGHTBLUE_EX}{sourceBranch}{colorama.Fore.RESET}...'
          f'{colorama.Fore.LIGHTBLUE_EX}{targetBranch}{colorama.Fore.RESET}')
    print(f'<Ahead: {colorama.Fore.CYAN}{ahead}{colorama.Fore.RESET}, '
          f'Behind: {colorama.Fore.CYAN}{behind}{colorama.Fore.RESET}>')

    print('Looking for git logs in the repo: ', end='')
    logs = repo.repo.git.log(f'{targetBranch}..{sourceBranch}', r'--pretty=%D%s%b', '--no-merges')
    print(f'{colorama.Fore.GREEN}Done{colorama.Style.RESET_ALL}')

    print('Treating logs: ', end='')
    str_ids = re.findall(r'#\d{3,4}', logs)
    ids = sorted(list(map(lambda id: id.replace('#', ''), set(str_ids))))
    n = int(len(ids) / 200) + 1
    print(f'{colorama.Fore.GREEN}Done{colorama.Style.RESET_ALL}')

    work_items = list()
    for i in range(n):
        ids_items = list(islice(ids, i * 200, (i + 1) * 200))
        work_items.extend(send_request(ids_items))

    message = create_message(work_items)

    _, i = pick(['Create pull request', 'Display message'], 'What should be done: ')
    if i == 0:
        wi = list(map(lambda f: f['id'], work_items))
        create_pull_request(sourceBranch, targetBranch, wi, message)
    elif i == 1:
        print(f'{message}')
    else:
        print(f'Please chose an other option.')


def close_bug(repo: CustomRepository):
    sourceBranch = repo.select_fix_branch()
    print(f'Selected source branch: {sourceBranch}')

    print(f'{colorama.Fore.RED}Not implemented yet{colorama.Fore.RESET}')


def print_colorama():
    colorama.init()
    for key, value in dict(vars(colorama.Fore)).items():
        print(f'{value}Fore: {key}')
    for key, value in dict(vars(colorama.Back)).items():
        print(f'{value}Back: {key}')
    sys.exit()


def remove_escape(input: str) -> str:
    return re.sub(r'(\x1b\[\d{2}m)', '', input)


def main():
    colorama.init()

    if len(sys.argv) >= 2:
        cwd = sys.argv[1]
    else:
        cwd = os.getcwd()

    os.system('cls' if os.name == 'nt' else 'clear')

    repository = CustomRepository.CustomRepository(cwd)

    atexit.register(finalize, repository)

    print(f'Repo opened in path: {colorama.Fore.LIGHTBLUE_EX}{cwd}{colorama.Fore.RESET}')

    _, i = pick(['Create release', 'Close bug'], 'Please select an action')
    if i == 0:
        release(repository)
    elif i == 1:
        close_bug(repository)


if __name__ == "__main__":
    main()
