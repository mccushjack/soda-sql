import os


class ENV:

    @staticmethod
    def get_variable(name: str) -> str:
        value = os.environ.get(name, '')
        if value == '':
            raise Exception(f"No environment variable '{name}' has been defined!")
        return value

    @staticmethod
    def get_deployment_description():
        environment = os.environ.get('ENV', '')
        if environment == '':
            return ''
        else:
            return f"with deployment to *{environment}* environment"

    @classmethod
    def get_branch(cls):
        return os.path.basename(cls.get_variable('GITHUB_REF'))

    @classmethod
    def get_project(cls):
        return os.path.basename(cls.get_variable('GITHUB_REPOSITORY'))

    @classmethod
    def get_reports_url(cls):
        return cls.get_variable('REPORTS_URL')

    @classmethod
    def get_test_module(cls):
        return cls.get_variable('TEST_MODULE')

    @classmethod
    def get_python_version(cls):
        return cls.get_variable('PYTHON_VERSION')

    @classmethod
    def get_included_branches(cls):
        return cls.get_variable('INCLUDED_BRANCHES')

    @classmethod
    def get_force_send(cls):
        return os.environ.get('FORCE_SEND', 'false')
