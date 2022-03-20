from fabric.contrib.files import exists
from fabric.api import cd, local, run, hosts

REPO_URL = 'git@github.com:c-Door-in/food-plan-service.git'


@hosts(['137.184.45.165'])
def deploy():
    site_folder = f'/home/django/code/food-plan-service'
    run(f'mkdir -p {site_folder}')
    with cd(site_folder):
        _get_latest_source()
        _update_database()
        _reload_services()
        _daemon_reload()
        _nginx_reload()


def _get_latest_source():
    if exists('.git'):
        run('git pull')
    else:
        run(f'git clone {REPO_URL} .')
    current_commit = local("git log -n 1 --format=%H", capture=True)
    run(f'git reset --hard {current_commit}')


def _update_database():
    run('./env/bin/python manage.py migrate --noinput')


def _reload_services():
    run('sudo systemctl restart food.socket food.service foodbot.service')


def _daemon_reload():
    run('sudo systemctl daemon-reload')


def _nginx_reload():
    run('sudo nginx -t && sudo systemctl restart nginx')



