:orphan:

DevSpace
==================

目的
-------

* 搭建日常开发用的工具

命令
-------

Usage:
  devspace <command> [options] [args]

Available commands:
  init          Create new project
  render        Render servers
  show          Show project information


例子
-----

运行::

git clone https://github.com/d12y12/DevSpace.git
pip3 install -r requirements.txt
cd DevSpace/
python3 ./devspace init demo ./workdir --extra='author=yang <d12y12@hotmail.com>' --extra='version=1.0.0'
cd workdir/
python3 ../devspace render --server gitmirror-demo
echo your_github_user_name:your_github_token > ./gitmirror-demo/github_token
docker-compose build
docker-compose up -d

进入 docker::

docker exec -it -u yang gitmirror-demo /bin/bash
