:orphan:

DevSpace
==================

目的
-------

* 搭建日常开发用的工具

命令
-------

Usage::
   
   devspace <command> [options] [args]

Available commands::
   
   init          Create new project
   render        Render servers
   show          Show project information

例子
-----

运行::

   git clone https://github.com/d12y12/DevSpace.git
   pip3 install -r requirements.txt
   cd DevSpace/
   python3 ./devspace init demo ./workdir --example --extra='maintainer=yang <d12y12@hotmail.com>'
   cd workdir/
   ! modify your devspace.json
   python3 ../devspace render --server Web
   python3 ../devspace render --server GitMirror
   python3 ../devspace render --server DocBuilder
   echo your_github_user_name:your_github_token > ./servers/GitMirror/apps/github_token
   docker-compose build
   docker-compose up -d

进入 docker::

   docker exec -it -u yang <container_name> /bin/sh

