from PyInquirer import prompt


def select(choices: list, message: str, **kwargs) -> (object, int):
    ACTION = 'action'
    prompt_list = [{'type': 'list',
                    'name': ACTION,
                    'message': message,
                    'choices': choices}]

    default = kwargs.get('default_index', None)

    if default is not None:
        prompt_list[0]['default'] = default
    choice = prompt(prompt_list)[ACTION]
    return choice, choices.index(choice)
