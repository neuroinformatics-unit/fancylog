"""Wrappers around gitpython.

Return information about the git repository for debugging.
"""


class GitPythonError(Exception):
    """Exception if gitpython cannot be found.

    It is typical in production environments that gitpython
    will not be available.
    """

    pass


class GitEnvironmentError(Exception):
    """Exception if gitpython  fails."""

    pass


class GitHead:
    """Parse a gitpython repo.head.commit object."""

    def __init__(self, head_commit):
        """Initialise GitHead.

        Parameters
        ----------
        head_commit
            The commit object representing the current HEAD of the repository.

        """
        self.hash = head_commit.hexsha
        self.committer_name = head_commit.committer.name
        self.committer_email = head_commit.committer.email
        self.message = head_commit.summary
        self.datetime = head_commit.authored_datetime.strftime(
            "Date: %Y-%m-%d, Time: %H-%M-%S"
        )


class GitInfo:
    """Parse a gitpython repo object and return informative properties."""

    def __init__(self, repo):
        """Initialise GitInfo.

        repo
            A gitpython repo object.
        """
        self.head = GitHead(repo.head.commit)


def get_git_info(repo_path):
    """Return a class with information about the git repository.

    Will only work with "dev" installs (otherwise gitpython is not installed).
    Will raise if no github repository found.
    """
    try:
        import git

    except ImportError as exc:
        raise GitPythonError from exc

    try:
        repo = git.Repo(repo_path)
        return GitInfo(repo)

    except git.InvalidGitRepositoryError as exc:
        raise GitEnvironmentError from exc
