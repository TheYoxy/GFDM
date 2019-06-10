import re
import sys

import colorama
import git
from pick import pick

from pullrequest import print_branch, GIT_ENDPOINT, remove_escape


class CustomRepository:
    def __init__(self, folder: str):
        self.repo = git.Repo(folder)
        self.current_branch = self.repo.git.rev_parse('--abbrev-ref', 'HEAD')
        print(f'Current branch: {print_branch(self.current_branch)}')
        self._is_stash = not not self.repo.git.status('--porcelain')
        if self.is_stash:
            print(f'Uncommitted files found. Creating stash: ', end='')
            self.stash_push()
            print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')

    @property
    def is_stash(self) -> bool:
        """
        Status of any stashed data during the process
        :return:
        """
        return self._is_stash

    @property
    def remote(self) -> str:
        """
        Get the remote linked to the git endpoint
        :return:
        """
        return next(filter(lambda remote: re.compile(GIT_ENDPOINT).search(remote[1][0]),
                           [(r.name, list(r.urls)) for r in self.repo.remotes]))[0]

    def push_branch(self, remote: str, branch_name: str):
        self.checkout(branch_name)
        print(f'Pushing {print_branch(branch_name)}: ', end='')
        self.repo.git.push(remote, branch_name)
        print(f'{colorama.Fore.GREEN}Done.{colorama.Fore.RESET}')

    def pull_branch(self, remote: str, branch_name: str):
        self.checkout(branch_name)
        print(f'Pulling {print_branch(branch_name)}: ', end='')
        self.repo.git.pull(remote, branch_name)
        print(f'{colorama.Fore.GREEN}Done.{colorama.Fore.RESET}')

    def check_branch(self, branch_name: str) -> bool:
        print(f'Trying to found the branch {print_branch(branch_name)} in local: {colorama.Fore.RESET}', end='')
        remote = self.remote
        if self.local_exist(branch_name):
            print(f'{colorama.Fore.GREEN}Found{colorama.Fore.RESET}')
            print(f'Checking if branch exist in remote {remote}: ', end='')
            if self.remote_exist(branch_name):
                print(f'{colorama.Fore.GREEN}Found{colorama.Fore.RESET}')
                print(f'Comparing with remote: ', end='')
                val = self.compare_branch(branch_name, f'{remote}/{branch_name}')
                if val == 0:
                    print(f'{colorama.Fore.GREEN}Sync{colorama.Fore.RESET}')
                elif val == -1:
                    print(f'{colorama.Fore.LIGHTBLUE_EX}Behind{colorama.Fore.RESET}')
                    self.pull_branch(remote, branch_name)
                elif val == 1:
                    print(f'{colorama.Fore.LIGHTBLUE_EX}Ahead{colorama.Fore.RESET}')
                    self.push_branch(remote, branch_name)
                else:
                    print(f'{colorama.Fore.RED}Unable to find any link between and local.{colorama.Fore.RESET}')
                    sys.exit(-1)
            else:
                print(f'{colorama.Fore.RED}Not found{colorama.Fore.RESET}')
                self.push_branch(remote, branch_name)
        else:
            print(f'{colorama.Fore.RED}Not found{colorama.Fore.RESET}')
            print(f'{colorama.Fore.YELLOW}Trying to found the branch {print_branch(branch_name)}'
                  f'{colorama.Fore.YELLOW} in remotes: {colorama.Fore.RESET}', end='')
            if self.remote_exist(branch_name):
                print(f'{colorama.Fore.GREEN}Found{colorama.Fore.RESET}')
                print('Pulling branch: ', end='')
                self.repo.git.checkout('-b', branch_name, '--track', f'{remote}/{branch_name}')
                print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')
                print()
                return True
            else:
                print(f'{colorama.Fore.RED}Not found{colorama.Fore.RESET}')
                print(f'Stopping the application')
                sys.exit(-1)
        return False

    def checkout(self, branch_name: str):
        print(f'Checking out branch -> {print_branch(branch_name)}: ', end='')
        self.repo.git.checkout(branch_name)
        print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')

    def clean_branch_name(self, branch_name: str) -> str:
        for origin in self.repo.remotes:
            branch_name = re.sub(f'{origin.name}/', '', branch_name)
        return branch_name

    def remove_newer_branch(self, source_branch_name: str, branch_list: list) -> list:
        return [branch for branch in branch_list if
                int(self.repo.git.rev_list(f'{branch}..{source_branch_name}', '--count', '--no-merges')) > 0]

    def compare_branch(self, b1: str, b2: str) -> int:
        """
        Compare 2 branchs inside a git repository
        :param b1: 1st branch name
        :param b2: 2nd branch name
        :return: 1 if b1 > b2
                O if b1 == b2
                -1 if b1 < b2
        """
        base = self.repo.git.merge_base(b1, b2)
        local = self.repo.git.rev_parse(b1)
        remote = self.repo.git.rev_parse(b2)
        if local == remote:
            return 0
        elif base == local:
            return -1
        elif base == remote:
            return 1
        else:
            return -2

    def local_exist(self, branch: str) -> bool:
        return branch in self.repo.branches

    def remote_exist(self, branch: str) -> bool:
        return self.repo.heads[branch].tracking_branch() is not None

    @property
    def remote_branch(self) -> list:
        return [branch.strip() for branch in self.repo.git.branch('-r').split('\n') if
                not re.search(r' -> ', branch)]

    @property
    def local_branch(self) -> list:
        return [branch.name for branch in self.repo.heads]

    @property
    def branch(self) -> list:
        return [branch for branch in self.remote_branch if not self.local_exist(self.clean_branch_name(branch))] \
               + self.local_branch

    def select_branch(self, branch_list: list = None) -> str:
        if list is None:
            print('Loading list of branch: ', end='')
            branch_list = self.local_branch
            print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')

        source, _ = pick(branch_list, 'Please select base branch: ',
                         default_index=branch_list.index(self.current_branch))
        return source

    def select_fix_branch(self) -> str:
        print('Loading list of branch: ', end='')
        branch_list = [branch for branch in self.local_branch if re.search(r'bugfix/', branch)]
        print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')
        if len(branch_list) == 0:
            print(f'{colorama.Fore.RED}There is no opened bugfix branches.{colorama.Fore.RESET}')
        elif len(branch_list) == 1:
            print(f'{colorama.Fore.YELLOW}There is only one bug branch opened. {colorama.Fore.RESET}')
            input_text = f'Close branch {print_branch(branch_list[0])} [Y/N]: '
            confirm = input(f'{input_text}{colorama.Fore.LIGHTWHITE_EX}')
            if not confirm:
                confirm = 'Y'
                print(f'{colorama.Cursor.UP(1)}{colorama.Cursor.FORWARD(len(remove_escape(input_text)))}'
                      f'{confirm}{colorama.Cursor.BACK(len(input_text))}{colorama.Fore.RESET}')

            if confirm.upper() == 'Y':
                return branch_list[0]
            else:
                print(f'{colorama.Fore.YELLOW}Stopping application{colorama.Fore.RESET}')
        else:
            return self.select_branch(branch_list)

    def select_src_dest_branch(self) -> (str, str):
        print('Loading list of branch: ', end='')
        branch_list = self.branch

        print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')

        source, _ = pick(branch_list, 'Please select base branch: ',
                         default_index=branch_list.index(self.current_branch))

        branch_list.remove(source)
        print(f'Removing newer branch: ', end='')
        branch_list = self.remove_newer_branch(source, branch_list)
        print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')

        source = self.clean_branch_name(source)
        print(f'Source branch selected: {print_branch(source)}')

        target, index = pick(branch_list, 'Please select target branch: ')
        target = self.clean_branch_name(target)
        print(f'Target branch selected: {print_branch(target)}')
        print()
        return source, target

    def reset_index(self):
        self.checkout(self.current_branch)
        if self.is_stash:
            print(f'Getting back uncommitted files. Popping stash: ', end='')
            self.stash_pop()
            print(f'{colorama.Fore.GREEN}Done{colorama.Fore.RESET}')

    def stash_push(self):
        self.repo.git.stash('push', '-u')

    def stash_pop(self):
        self.repo.git.stash('pop')