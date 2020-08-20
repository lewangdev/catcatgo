---
layout: post
title: '使用 Docker 方式安装 Gitlab，没你想得那么简单'
subtitle: '可能是全网唯一的一篇靠谱的介绍用 Docker 来安装配置 Gitlab 的文档'
date: 2018-12-18 23:25:20
author: Le
header_img: 'img/sara-codair-1084651-unsplash.jpg'
catalog: true
tags:
    - Docker
    - Gitlab
    - SSH
    - Linux
---

## 为什么要写这篇文章？

曾经几年前在 Docker 还没有广泛应用的时候，在公司使用过源码的方式安装和升级过 Gitlab，虽远没有 Docker 方便，因为自己对 Linux 系统的理解，所以整体上感觉还是挺简单的。这几年随着 Docker 的普及，使得安装 Gitlab 更加的容易，不仅方便了我这样的老鸟，也更方便了小白用户们。但是 Gitlab 官方的 [Docker 安装文档](https://docs.gitlab.com/omnibus/docker/)并没有写得很完善, 除了官方文档之外，检索出来的安装文档也是人云亦云，东拼西凑，结果也就是能运行起来，凑合着能用而已。

我希望每做一件小事的时候也都能抱着“知其然知其所以然”的心态对待，用 Docker 方式安装 Gitlab，说简单来说就是一行命令的事儿，但是这样就够了吗？我看是不够的，所以就有了这篇文档。

## 本文需要达成的事项

* 在 CentOS 7 系统中安装 Docker
* 使用 Docker 方式安装中文版 Gitlab
* 和宿主机器共用 22(SSH) 端口
* 支持 SSH(22)/HTTPS(443) 方式推拉仓库
* 使用 SMTP 方式配置通知邮箱(腾讯企业邮箱)
* 改写默认的项目标签(Labels)

## 在 CentOS 7 系统中安装 Docker

这部分参考 [Docker 的官方文档](https://docs.docker.com/install/linux/docker-ce/centos/), 罗列一下安装步骤, 细节请看 [Docker 的官方文档](https://docs.docker.com/install/linux/docker-ce/centos/)。如果使用 root 用户安装，sudo 可以去掉。

### 1. 删除老版本 Docker

```sh
$ sudo yum remove docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-selinux \
                  docker-engine-selinux \
                  docker-engine
```

### 2. 安装 Docker CE 的仓库配置

```sh
$ sudo yum install -y yum-utils \
  device-mapper-persistent-data \
  lvm2
$ sudo yum-config-manager \
    --add-repo \
    https://download.docker.com/linux/centos/docker-ce.repo

```

### 3. 安装仓库中最高版本 Docker CE

```sh
$ sudo yum install -y docker-ce
```

### 4. 启动 Docker

```sh
$ sudo systemctl start docker
```

### 5. 验证 Docker 是否安装成功

```sh
$ sudo docker run hello-world
```

## 使用 Docker 方式安装中文版 Gitlab

目前我的团队习惯使用中文版的 Gitlab 的，并且使用的版本是 `beginor/gitlab-ce:10.3.1-ce.0`，所以还是以这个版本来说明安装配置过程。

在起动 Gitlab 之前，创建几个目录作为 Docker 的卷，这样的配置或者升级 gitlab 的时候可以保留配置和数据。

```sh
$ sudo mkdir -p /data/var/lib/gitlab/etc
$ sudo mkdir -p /data/var/lib/gitlab/log
$ sudo mkdir -p /data/var/lib/gitlab/data
```

启动 Gitlab

```sh
$ sudo docker run \
    --detach \
    --sysctl net.core.somaxconn=1024 \
    --publish 8080:80 \
    --publish 8022:22 \
    --name gitlab \
    --restart unless-stopped \
    --volume /data/var/lib/gitlab/etc:/etc/gitlab \
    --volume /data/var/lib/gitlab/log:/var/log/gitlab \
    --volume /data/var/lib/gitlab/data:/var/opt/gitlab \
    beginor/gitlab-ce:10.3.1-ce.0
```

这个 Gitlab 的 Docker 镜像是基于  Ubuntu 16.04.3 LTS 这个版本来构建的，所以在 `docker exec -it gitlab /bin/bash` 进入 Docker 容器之后跟使用 Ubuntu 就没有什么差别了。

gitlab 容器中启动了很多服务，主要包括：

* gitlab
* redis
* postgresql
* nginx
* sshd

通过查看 Dockerfile 发现，除了可以使用 `docker exec -it gitlab /bin/bash` 进入容器之外，还可以直接使用 SSH 登录到容器中。其实 Gitlab 这个镜像，并不符合 [Dockerfile 最佳实践规范](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#decouple-applications), 因为将会有太多的服务在这个镜像构建的容器之中，不利于服务的扩容和重用。不过通过这种超级包的方式确实大大降低了用户的使用门槛，对于高段位选手，自然也会自己去拆分去解耦，进而去构建自己的镜像。

讲到这里，gitlab 服务已经在运行了，大多数人也认为自己任务完成了，一切到此为止。但是对于有些许强迫症的人来说，是无法接受 HTTP 得用 8080 端口， SSH 得用 8022 端口，这样 Git 的 URL 就不太美观了。

偷懒的人有个很简单的方法来解决这个端口的问题， 可以使用这样的命令启动 Docker

```sh
$ sudo docker stop gitlab
$ sudo docker rm gitlab
$ sudo docker run \
    --detach \
    --sysctl net.core.somaxconn=1024 \
    --publish 443:443 \
    --publish 80:80 \
    --publish 22:22 \
    --name gitlab \
    --restart unless-stopped \
    --volume /data/var/lib/gitlab/etc:/etc/gitlab \
    --volume /data/var/lib/gitlab/log:/var/log/gitlab \
    --volume /data/var/lib/gitlab/data:/var/opt/gitlab \
    beginor/gitlab-ce:10.3.1-ce.0
```

这样有带来了新问题:

1. 80/443 将会被 gitlab 独占，宿主机器上 Nginx 等 HTTP/HTTPS 服务将无法使用 80/443
2. 22 将会被 gitlab 独占，那么宿主机器上的 SSHD 服务需要改为其它端口

这两个新问题大概对于有些许强迫症的人来说也是无法接受的。 我们还是回到这样的方式启动 Gitlab

```sh
$ sudo docker stop gitlab
$ sudo docker rm gitlab
$ sudo docker run \
    --detach \
    --sysctl net.core.somaxconn=1024 \
    --publish 8080:80 \
    --publish 8022:22 \
    --name gitlab \
    --restart unless-stopped \
    --volume /data/var/lib/gitlab/etc:/etc/gitlab \
    --volume /data/var/lib/gitlab/log:/var/log/gitlab \
    --volume /data/var/lib/gitlab/data:/var/opt/gitlab \
    beginor/gitlab-ce:10.3.1-ce.0
```

然后寻找其它更好的解决方案：

1. 使用 Nginx 代理 8080 端口，这样很容易实现 HTTP(80)/HTTPS(443) 端口共用
2. 共享宿主机器的 SSH(22) 端口，如果使用 git 这个账号登录，则转发 SSH 到 gitlab 的容器中

下面来讲如何解决这两个问题。

## 使用宿主机器上的 Nginx 配置 HTTP 和 HTTPS

使用宿主机器上的 Nginx 使得我们安装 Gitlab 更加灵活。先停用 Gitlab 容器中的 HTTPS 服务, 需要这样改写配置文件, 需要编辑
`/data/var/lib/gitlab/etc/gitlab.rb` 文件相应的行，[具体配置可以参考这里](https://docs.gitlab.com/omnibus/settings/nginx.html#using-a-non-bundled-web-server)

```ruby
external_url "https://gitlab.example.com"
nginx['listen_port'] = 80
nginx['listen_https'] = false
```

修改完成之后，可以在 Docker 容器中执行 `gitlab-ctl reconfigure` 来使之生效。这样配置以后，容器中讲只提供 HTTP 服务，不会根据 `external_url` 解析来自动启动 HTTPS 而导致日志中出现大量的缺少证书的日志。现在只需要配置宿主机器的 Nginx 就可以了。关于如何获取免费的 SSL 证书，这里就不在赘述了，读者可以自行搜索 Let's Encrypt + Nginx 相关文章，如果没有域名，只有 IP，那可以试试 [TrustOcean](https://www.trustocean.com/)。

## Gitlab Docker 和宿主服务器共享 SSH(22) 端口

Gitlab Docker 镜像中默认使用的 SSH 账户是 git，那能不能在宿主机器上也建一个账户 git，只是当 git 帐号进行操作的时候，我们转发命令到 gitlab 容器呢？答案是肯定的，宿主机器上非 git 帐号就不受影响了，还可以正常使用。

我们在宿主机器上创建 git 账户，并且获取他的 uid 和 gid

```sh
adduser git
id git
uid=1001(git) gid=1001(git) groups=1001(git)
```

要完成共享22端口，要求 gitlab 容器中的 git 账户的 uid 和 gid 和宿主机器上完全相同，这样读取 SSH Key 时就不会有权限问题。关于如何修改两个系统中 git 账户的 uid 和 gid，可以通过手动的方式修改这两个文件：`/etc/passwd` 和 `/etc/group`, 找到对应的行进行修改。获取通过编辑 `/data/var/lib/gitlab/etc/gitlab.rb` 这个配置文件，修改其中的行，[具体请参考这里](https://docs.gitlab.com/omnibus/settings/configuration.html#specify-numeric-user-and-group-identifiers):

```ruby
user['username'] = 'git'
user['group'] = 'git'
user['uid'] = 1001
user['gid'] = 1001
```

修改完成之后，可以在 Docker 容器中执行 `gitlab-ctl reconfigure` 来使之生效.

在宿主机器上切换到 git 账户：`su - git` 然后执行 `ln -s /data/var/lib/gitlab/data/.ssh .ssh` 与 gitlab 容器共享 .ssh 下面的内容。为了在宿主机器上可以使用 git 账户无密码登录到 gitlab 容器中，需要创建在 .ssh 目录中添加一组密钥，并且把公钥加到 .ssh/authorized_keys 文件中去。

在宿主机器上执行:

```ssh
ssh-keygen -t rsa -P ''
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
```

添加 `no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty` 到 `~/.ssh/authorized_keys` 所在的行首，结果看起来是这样的：

```sh
no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAA......CzGuj git@cn-bj-aliyun-3
```

登录测试一下

```sh
ssh -p 8022 127.0.0.1
```

观察到 `~/.ssh/authorized_keys` 其它行都是这样

```sh
command="/opt/gitlab/embedded/service/gitlab-shell/bin/gitlab-shell key-32",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAA......hOtpAl7J
```

在宿主机看来，每次git账户进行操作是都会执行 `/opt/gitlab/embedded/service/gitlab-shell/bin/gitlab-shell`, 我们恰好可以使用这个脚本来实现转发。

```sh
mkdir -p /opt/gitlab/embedded/service/gitlab-shell/bin/
touch gitlab-shell
chmod +x gitlab-shell
```

并且输入以下内容到 `/opt/gitlab/embedded/service/gitlab-shell/bin/gitlab-shell` 中

```sh
#!/bin/sh

ssh -p 8022 -o StrictHostKeyChecking=no git@127.0.0.1 "SSH_ORIGINAL_COMMAND=\"$SSH_ORIGINAL_COMMAND\" $0 $@"
```

一切就绪了， 可以使用 `https://gitlab.example.com/repo.git` 或者 `git@gitlab.example.com:repo.git` 这样的 URL 了。

## 使用 SMTP 方式配置通知邮箱(腾讯企业邮箱)

[Gitlab SMTP 文档参考这里](https://docs.gitlab.com/omnibus/settings/smtp.html)

```sh
gitlab_rails['smtp_enable'] = true
gitlab_rails['smtp_address'] = "smtp.exmail.qq.com"
gitlab_rails['smtp_port'] = 465
gitlab_rails['smtp_user_name'] = "xxxx@xx.com"
gitlab_rails['smtp_password'] = "password"
gitlab_rails['smtp_authentication'] = "login"
gitlab_rails['smtp_enable_starttls_auto'] = true
gitlab_rails['smtp_tls'] = true
gitlab_rails['gitlab_email_from'] = 'xxxx@xx.com'
gitlab_rails['smtp_domain'] = "exmail.qq.com"
```

## 改写默认的项目标签(Labels)

添加丰富的标准，方便进行项目管理。修改 `issues_labels.rb` 文件

```ruby
labels = [
  {"title": "优先级:低", "color": "#E99695", "description": "低优先级"},
  {"title": "优先级:紧急", "color": "#E99695", "description": "需要立即处理"},
  {"title": "优先级:高", "color": "#E99695", "description": "优先处理"},
  {"title": "分类:BUG", "color": "#D4C5F9", "description": "发现的BUG"},
  {"title": "分类:功能增强", "color": "#D4C5F9", "description": "增强已有的功能，属于优化的环节"},
  {"title": "分类:功能完善", "color": "#D4C5F9", "description": "完善功能"},
  {"title": "分类:文档修改", "color": "#D4C5F9", "description": "只是做文档修改"},
  {"title": "分类:新功能", "color": "#D4C5F9", "description": "新的功能和需求"},
  {"title": "项目:已上线", "color": "#C5DEF5", "description": "已发布上线"},
  {"title": "项目:已排期", "color": "#C5DEF5", "description": "已经安排了开发时间milestone"},
  {"title": "项目:已确认", "color": "#C5DEF5", "description": "功能已经确认，后续进行排期"},
  {"title": "项目:延后", "color": "#C5DEF5", "description": "功能无法确定是否开发，延期处理"},
  {"title": "项目:开发中", "color": "#C5DEF5", "description": "功能正在开发"},
  {"title": "项目:待讨论", "color": "#C5DEF5", "description": "需求已经提出，但是需要讨论是否需要开发"},
  {"title": "项目:测试中", "color": "#C5DEF5", "description": "功能已经完成开发，正在测试"}
]
```

## 总结

使用 Docker 方式安装 Gitlab 部署过程很简单，但是想达到一个理想的配置状况还是挺繁琐的，Docker 并不是治疗百病的良药，打铁还得自身硬。

完