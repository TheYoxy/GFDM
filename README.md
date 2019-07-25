# Git-Flow Devops Management (GFDM)

Small cli tool in python to manage flow for a git repository with pull request.
Currently based on [Azure Devops](https://azure.microsoft.com/en-us/services/devops/?nav=min)

## Required

* `Python 3`
* A git repository where work items are set inside the commit message.
* An azure devops linked to this repository
> E.G. `#{id of the work item} - Update readme.md`

## How to use

1. `git clone https://github.com/TheYoxy/GFDM`
2. `cd GFDM`
3. Copy `config.temp.json` to `config.json`
4. `pip install -r requirement.txt`
5. `python pullrequest.py "Path to the directory to work on"`

## Built With

* [PythonGit](https://github.com/gitpython-developers/GitPython) - Library used for git management

## Contributing

Please read [CONTRIBUTING.md]() for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](). 

## Authors

* **Floryan Simar** - *Initial work* - [TheYoxy](https://github.com/theyoxy)

See also the list of [contributors](https://github.com/TheYoxy/GFDM/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
