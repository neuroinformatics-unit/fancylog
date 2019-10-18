"""
git
===============

Wrappers around gitpython to return information about the git repository
for debugging

"""


class GitPythonError(Exception):
    """
    Exception if gitpython cannot be found (Typical in production
    environments).
    """

    pass


class GitEnvironmentError(Exception):
    """
    Exception if gitpython  fails (Typical in production environments).
    """

    pass


class GitHead:
    """
    Class to parse a repo.head.commit object from gitpython, and return
    more informative properties
    """

    def __init__(self, head_commit):
        self.hash = head_commit.hexsha
        self.committer_name = head_commit.committer.name
        self.committer_email = head_commit.committer.email
        self.message = head_commit.summary
        self.datetime = head_commit.authored_datetime.strftime(
            "Date: %Y-%m-%d, Time: %H-%M-%S"
        )


class GitInfo:
    """
    Class to parse a repo object from gitpython, and return more informative
    properties
    """

    def __init__(self, repo):
        self.head = GitHead(repo.head.commit)


def get_git_info(repo_path):
    """
    Returns a class with useful information about the git repository.
    (if there is one). Will only work with "dev" installs (otherwise
    gitpython is not installed)
    :return:
    """

    try:
        import git

    except ImportError:
        raise GitPythonError
        return None

    try:
        repo = git.Repo(repo_path)
        return GitInfo(repo)

    except git.InvalidGitRepositoryError:
        raise GitEnvironmentError
        return None
