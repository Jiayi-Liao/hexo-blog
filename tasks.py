# coding=utf8
from fabric import Connection
from invoke import task
from password import *


@task
def blogpic(c, src):
    conn = Connection(host='101.200.171.13', user='root',
                      connect_kwargs={"password": password})    
    file = src.split("/")[-1]
    conn.put(src,
             "/server/hexo/themes/next/source/assets/")
    conn.run("cp /server/hexo/themes/next/source/assets/" +
             file + " /var/www/hexo/assets/")


@task
def upload(c, src, lang):
    if lang == "en":
        dest = "/server/hexoen/source/_posts/"
    elif lang == "ch":
        dest = "/server/hexo/source/_posts/"
    else:
        exit(100)
    conn = Connection(host='101.200.171.13', user='root',
                      connect_kwargs={"password": password})
    conn.put(src, dest)


@task
def deployEn(c):
    conn = Connection(host='101.200.171.13', user='root',
                      connect_kwargs={"password": password})
    conn.run("cd /server/hexoen/ && /server/node-v6.11.2/bin/hexo g")
    conn.run("cp -r /server/hexoen/public/* /server/hexo/public/en/")


@task
def deploy(c):
    conn = Connection(host='101.200.171.13', user='root',
                      connect_kwargs={"password": password})
    conn.run("cd /server/hexo/ && /server/node-v6.11.2/bin/hexo g -d")
